"""OpenCifra: a focused songbook and practice companion."""
from concurrent.futures import ThreadPoolExecutor
import json
import logging
import math
from pathlib import Path

from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Ellipse, Line, RoundedRectangle
from kivy.lang import Builder
from kivy.metrics import dp, sp
from kivy.properties import BooleanProperty, ListProperty, NumericProperty, StringProperty
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.utils import platform
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFlatButton
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.textfield import MDTextField
import requests

from music import ChordBook, TUNINGS, NOTE_NAMES, chord_formula, note_name
from songbook import Library, SongService, escape, transpose

BASE = Path(__file__).resolve().parent


class SongItem(MDCard):
    title = StringProperty()
    artist = StringProperty()


class SearchScreen(MDScreen):
    pass


class LyricsScreen(MDScreen):
    pass


class TunerScreen(MDScreen):
    pass


class ChordDiagram(MDBoxLayout):
    def __init__(self, chord, frets, omitted=(), **kwargs):
        super().__init__(orientation='vertical', size_hint_x=None, width=dp(104), **kwargs)
        self.frets = frets
        self.add_widget(Label(text=chord, bold=True, color=(.70, .53, 1, 1),
                              size_hint_y=None, height=dp(26)))
        self.board = Widget()
        self.add_widget(self.board)
        self.board.bind(pos=self.draw, size=self.draw)
        label = 'See chord details' if frets is None else ' '.join('x' if f < 0 else str(f) for f in frets)
        if omitted:
            label += '\nOmit ' + ', '.join(NOTE_NAMES[n] for n in omitted)
        self.add_widget(Label(text=label, font_size=sp(10), color=(.64, .61, .70, 1),
                              size_hint_y=None, height=dp(30)))

    def draw(self, *_):
        self.board.canvas.clear()
        if self.frets is None:
            return
        pressed = [f for f in self.frets if f > 0]
        base = min(pressed) if pressed and max(pressed) > 4 else 1
        x, y = self.board.x + dp(18), self.board.y + dp(10)
        width, height = dp(64), max(dp(40), self.board.height - dp(26))
        with self.board.canvas:
            Color(.35, .31, .42, 1)
            for string in range(6):
                xx = x + width * string / 5
                Line(points=[xx, y, xx, y + height], width=1)
            for fret in range(5):
                yy = y + height * fret / 4
                Line(points=[x, yy, x + width, yy], width=2 if fret == 4 and base == 1 else 1)
            Color(.70, .53, 1, 1)
            for string, fret in enumerate(self.frets):
                xx = x + width * string / 5
                if fret > 0:
                    yy = y + height - (fret - base + .5) * height / 4
                    Ellipse(pos=(xx - dp(4), yy - dp(4)), size=(dp(8), dp(8)))
                elif fret == 0:
                    Line(circle=(xx, y + height + dp(8), dp(3)), width=1)
                else:
                    yy = y + height + dp(8)
                    Line(points=[xx - dp(3), yy - dp(3), xx + dp(3), yy + dp(3)], width=1)
                    Line(points=[xx - dp(3), yy + dp(3), xx + dp(3), yy - dp(3)], width=1)


class TunerMeter(Widget):
    cents = NumericProperty(0)
    signal = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self.draw, size=self.draw, cents=self.draw, signal=self.draw)

    def draw(self, *_):
        self.canvas.clear()
        x, y, width = self.x + dp(16), self.center_y, self.width - dp(32)
        with self.canvas:
            Color(.20, .17, .26, 1)
            RoundedRectangle(pos=(x, y - dp(4)), size=(width, dp(8)), radius=[dp(4)])
            Color(.50, .35, .75, 1)
            RoundedRectangle(pos=(x + width * .45, y - dp(9)), size=(width * .1, dp(18)), radius=[dp(4)])
            Color(.7, .65, .8, 1)
            for tick in range(11):
                xx = x + width * tick / 10
                Line(points=[xx, y - dp(17), xx, y - dp(23)], width=1)
            if self.signal:
                Color(*((.55, .90, .72, 1) if abs(self.cents) < 5 else (.70, .53, 1, 1)))
                xx = x + width * (max(-50, min(50, self.cents)) + 50) / 100
                Ellipse(pos=(xx - dp(8), y - dp(8)), size=(dp(16), dp(16)))


class OpenCifraApp(MDApp):
    background = ListProperty([.065, .055, .09, 1])
    surface = ListProperty([.12, .10, .16, 1])
    accent = ListProperty([.70, .53, 1, 1])
    muted = ListProperty([.65, .61, .72, 1])
    section = StringProperty('Search')
    active_list = StringProperty('Favorites')
    search_status = StringProperty('Search for a song or artist to get started.')
    search_busy = BooleanProperty(False)
    search_failed = BooleanProperty(False)
    song_title = StringProperty('')
    song_artist = StringProperty('')
    song_status = StringProperty('')
    song_busy = BooleanProperty(False)
    song_ready = BooleanProperty(False)
    song_failed = BooleanProperty(False)
    font_size = NumericProperty(15)
    transpose_steps = NumericProperty(0)
    hide_tabs = BooleanProperty(False)
    show_diagrams = BooleanProperty(True)
    capo = NumericProperty(0)
    tuning = StringProperty('Standard')
    scrolling = BooleanProperty(False)
    scroll_speed = NumericProperty(24)
    tuner_note = StringProperty('--')
    tuner_reading = StringProperty('Ready when you are')
    tuner_status = StringProperty('Start the microphone to tune your guitar.')
    tuner_cents = NumericProperty(0)
    tuner_signal = BooleanProperty(False)
    tuner_target = NumericProperty(-1)
    mic_requested = BooleanProperty(False)

    def build(self):
        self.title = 'OpenCifra'
        self.icon = str(BASE / 'icon.png')
        self.theme_cls.theme_style = 'Dark'
        self.theme_cls.primary_palette = 'DeepPurple'
        self.theme_cls.accent_palette = 'DeepPurple'
        self.library = Library(Path(self.user_data_dir) / 'library.json')
        settings = self.library.data['settings']
        for name, low, high in [('font_size', 10, 28), ('scroll_speed', 5, 80)]:
            value = settings.get(name)
            if isinstance(value, (int, float)) and math.isfinite(value):
                setattr(self, name, max(low, min(high, value)))
        for name in ('hide_tabs', 'show_diagrams'):
            if isinstance(settings.get(name), bool):
                setattr(self, name, settings[name])
        self.service = SongService()
        self.search_service = SongService()
        self.search_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="search")
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix='songbook')
        self.diagram_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix='chords')
        self.diagram_generation = 0
        self.pending = {}
        self.search_generation = self.song_generation = 0
        self.search_event = self.scroll_event = self.render_event = None
        self.song = None
        self.chord_book = ChordBook()
        self.audio = None
        self.dialog = None
        self.closed = False
        Builder.load_file(str(BASE / 'ui.kv'))
        manager = MDScreenManager()
        for screen in (SearchScreen(), LyricsScreen(), TunerScreen()):
            manager.add_widget(screen)
        Window.bind(on_keyboard=self.on_keyboard)
        if platform != 'android':
            Window.minimum_width, Window.minimum_height = 360, 600
        Clock.schedule_interval(self.update_tuner, .05)
        return manager

    def save_library(self):
        self.library.data['settings'].update({name: getattr(self, name) for name in
            ('font_size', 'hide_tabs', 'show_diagrams', 'scroll_speed')})
        try:
            self.library.save()
        except OSError:
            logging.exception('Unable to save library')
            self.message('Storage unavailable', 'Your changes could not be saved. Check available storage.')

    def submit(self, kind, work, done):
        previous = self.pending.get(kind)
        if previous:
            previous.cancel()
        executor = {'diagrams': self.diagram_executor, 'search': self.search_executor}.get(kind, self.executor)
        future = executor.submit(work)
        self.pending[kind] = future
        def finish(future):
            if future.cancelled() or self.closed:
                return
            try:
                result, error = future.result(), None
            except Exception as exc:
                result, error = None, exc
            Clock.schedule_once(lambda dt: done(result, error) if not self.closed else None)
        future.add_done_callback(finish)

    @staticmethod
    def error_text(error):
        if isinstance(error, requests.Timeout):
            return 'The connection timed out. Please try again.'
        if isinstance(error, requests.HTTPError) and error.response is not None and error.response.status_code in (403, 429):
            return 'The source is limiting access. Please try again later.'
        if isinstance(error, requests.RequestException):
            return 'Could not connect. Check your internet and try again.'
        if isinstance(error, ValueError):
            return str(error) if 'Cifra' not in str(error) else 'No chord sheet found. Try another song.'
        logging.error('Request failed: %s', error)
        return 'Could not load this content. Please try again.'

    def on_search_text(self, text):
        if not self.root:
            return
        self.search_generation += 1
        token = self.search_generation
        if self.search_event:
            self.search_event.cancel()
        if self.pending.get('search'):
            self.pending['search'].cancel()
        self.search_busy = self.search_failed = False
        query = text.strip()
        if self.section != 'Search':
            self.refresh_library()
            return
        self.root.get_screen('search').ids.results.data = []
        if len(query) < 2:
            self.search_status = 'Type at least 2 characters to find a song.'
            return
        self.search_status = 'Searching…'
        self.search_busy = True
        def dispatch(dt):
            self.submit('search', lambda: self.search_service.search(query),
                        lambda results, error: self.search_done(token, results, error))
        self.search_event = Clock.schedule_once(dispatch, .3)

    def search_done(self, token, results, error):
        if token != self.search_generation or self.section != 'Search':
            return
        self.search_busy = False
        self.search_failed = error is not None
        self.root.get_screen('search').ids.results.data = results or []
        self.search_status = self.error_text(error) if error else (
            f'{len(results)} song{"s" if len(results) != 1 else ""} found' if results else 'No matches. Try a different title or artist.')

    def select_section(self, section):
        self.section = section
        self.on_search_text(self.root.get_screen('search').ids.query.text)

    def refresh_library(self):
        items = self.library.data['recent'] if self.section == 'Recent' else self.library.data['lists'].get(self.active_list, [])
        query = self.root.get_screen('search').ids.query.text.strip().casefold()
        items = [x for x in items if query in (x['title'] + ' ' + x['artist']).casefold()]
        self.root.get_screen('search').ids.results.data = items
        self.search_status = f'{len(items)} song{"s" if len(items) != 1 else ""}' if items else 'No songs here yet. Open a song and add it to a list.'

    def open_song(self, title, artist):
        self.stop_scroll()
        self.song_generation += 1
        token = self.song_generation
        self.song_title, self.song_artist = title, artist
        self.song = None
        self.diagram_generation += 1
        self.song_ready = self.song_failed = False
        self.song_busy = True
        self.song_status = 'Loading chord sheet…'
        self.transpose_steps, self.capo = 0, 0
        self.root.get_screen('lyrics').ids.lyrics_container.clear_widgets()
        self.root.current = 'lyrics'
        self.submit('song', lambda: self.service.fetch(title, artist),
                    lambda song, error: self.song_done(token, song, error))

    def song_done(self, token, song, error):
        if token != self.song_generation:
            return
        self.song_busy = False
        self.song_failed = error is not None
        self.song_status = self.error_text(error) if error else ''
        if error:
            return
        self.song = song
        self.song_ready = True
        self.library.visit(song.title, song.artist)
        self.save_library()
        self.render_song(reset=True)

    def render_song(self, reset=False):
        if not self.song:
            return
        screen = self.root.get_screen('lyrics')
        container = screen.ids.lyrics_container
        scroll = screen.ids.lyrics_scroll
        old_y = scroll.scroll_y
        container.clear_widgets()
        lines = self.song.render(int(self.transpose_steps), self.hide_tabs).split('\n')
        if self.song.credits:
            lines += ['', '[color=A69BB8]' + escape(self.song.credits) + '[/color]']
        lines += ['', '[color=A69BB8]Source: Cifra Club[/color]']
        self.render_generation = getattr(self, 'render_generation', 0) + 1
        generation = self.render_generation
        # Small batches keep touch and animation responsive for long songs.
        def add_batch(offset=0):
            if generation != self.render_generation or not self.song:
                return
            for start in range(offset, min(offset + 60, len(lines)), 20):
                label = Label(text='\n'.join(lines[start:start + 20]), markup=True,
                              font_name=str(BASE / 'RobotoMono-Regular.ttf'), font_size=sp(self.font_size),
                              size_hint=(None, None), halign='left', valign='top',
                              color=(.91, .89, .94, 1), line_height=1.25)
                label.bind(on_ref_press=lambda widget, chord: self.show_chord(chord))
                label.texture_update()
                label.size = label.texture_size
                container.add_widget(label)
            if offset + 60 < len(lines):
                Clock.schedule_once(lambda dt: add_batch(offset + 60))
            else:
                Clock.schedule_once(lambda dt: setattr(scroll, 'scroll_y', 1 if reset else old_y))
        add_batch()
        self.refresh_diagrams()

    def refresh_diagrams(self):
        box = self.root.get_screen('lyrics').ids.diagrams
        box.clear_widgets()
        self.diagram_generation += 1
        token = self.diagram_generation
        if not self.song or not self.show_diagrams:
            return
        chords = list(dict.fromkeys(transpose(text, int(self.transpose_steps))
                      for line in self.song.lines for text, chord in line if chord))
        tuning = self.tuning
        def ready(results, error):
            if token != self.diagram_generation or error:
                return
            for chord, positions in results:
                first = positions[0] if positions else None
                diagram = ChordDiagram(chord, first.frets if first else None,
                                       first.omitted if first else ())
                box.add_widget(diagram)
        self.submit('diagrams', lambda: [(c, self.chord_book.positions(c, tuning)) for c in chords], ready)

    def show_chord(self, chord):
        from kivy.uix.scrollview import ScrollView
        positions = self.chord_book.positions(chord, self.tuning)
        if not positions:
            try:
                formula = chord_formula(chord)
                notes = ', '.join(NOTE_NAMES[n] for n in sorted(formula.tones))
                text = 'Notes: ' + notes + '. No playable four-finger shape was found in this tuning. Try another tuning or a simpler voicing.'
            except ValueError:
                text = 'This chord notation is not recognized. Try a standard chord symbol such as Cmaj7, F#m7b5 or Bb7(9).'
            self.message(chord, text)
            return
        content = MDBoxLayout(orientation='vertical', size_hint_y=None, height=dp(208))
        scroll = ScrollView(do_scroll_y=False)
        row = MDBoxLayout(size_hint_x=None, spacing=dp(12))
        row.bind(minimum_width=row.setter('width'))
        for pos in positions:
            row.add_widget(ChordDiagram(chord, pos.frets, pos.omitted))
        scroll.add_widget(row)
        content.add_widget(scroll)
        self.open_dialog(MDDialog(title=chord + ' · ' + self.tuning, type='custom', content_cls=content,
                                  buttons=[self.button('CLOSE', self.dismiss_dialog)]))

    def change_font(self, amount):
        self.font_size = max(10, min(28, self.font_size + amount))
        self.queue_render()

    def change_key(self, amount):
        self.transpose_steps = max(-12, min(12, self.transpose_steps + amount))
        self.queue_render()

    def queue_render(self):
        self.stop_scroll()
        if self.render_event:
            self.render_event.cancel()
        self.render_event = Clock.schedule_once(lambda dt: self.render_song(), .1)

    def toggle_tabs(self):
        self.hide_tabs = not self.hide_tabs
        self.queue_render()

    def toggle_diagrams(self):
        self.show_diagrams = not self.show_diagrams
        self.refresh_diagrams()

    def toggle_scroll(self):
        if self.scrolling:
            self.stop_scroll()
        elif self.song_ready:
            self.scrolling = True
            self.scroll_event = Clock.schedule_interval(self.scroll_tick, 1 / 30)

    def scroll_tick(self, dt):
        screen = self.root.get_screen('lyrics')
        scroll = screen.ids.lyrics_scroll
        distance = screen.ids.lyrics_container.height - scroll.height
        if distance <= 0 or scroll.scroll_y <= 0:
            self.stop_scroll()
            return
        scroll.scroll_y = max(0, scroll.scroll_y - dp(self.scroll_speed) * dt / distance)

    def stop_scroll(self, *_):
        self.scrolling = False
        if self.scroll_event:
            self.scroll_event.cancel()
            self.scroll_event = None

    def back_to_search(self):
        self.stop_scroll()
        self.song_generation += 1
        self.song_busy = False
        self.root.current = 'search'
        if self.section != 'Search':
            self.refresh_library()
        self.save_library()

    def button(self, text, callback):
        return MDFlatButton(text=text, theme_text_color='Custom', text_color=self.accent,
                            on_release=lambda *_: callback())

    def open_dialog(self, dialog):
        self.stop_scroll()
        self.dismiss_dialog()
        self.dialog = dialog
        dialog.open()

    def dismiss_dialog(self):
        if self.dialog:
            self.dialog.dismiss()
            self.dialog = None

    def message(self, title, text):
        self.open_dialog(MDDialog(title=title, text=text, buttons=[self.button('OK', self.dismiss_dialog)]))

    def choose_list(self, for_song=False):
        content = MDBoxLayout(orientation='vertical', adaptive_height=True, spacing=dp(4))
        item = {'title': self.song_title, 'artist': self.song_artist}
        for name, songs in self.library.data['lists'].items():
            label = ('REMOVE FROM ' if item in songs else 'ADD TO ') + name if for_song else name
            def select(name=name):
                if for_song:
                    self.library.toggle(name, item)
                    self.save_library()
                self.active_list = name
                self.dismiss_dialog()
                if self.section == 'Lists':
                    self.refresh_library()
            content.add_widget(self.button(label, select))
        self.open_dialog(MDDialog(title='Save to a list' if for_song else 'Your lists', type='custom',
            content_cls=content, buttons=[self.button('NEW LIST', lambda: self.new_list(for_song)),
                                         self.button('CLOSE', self.dismiss_dialog)]))

    def new_list(self, for_song=False):
        field = MDTextField(hint_text='List name', max_text_length=40)
        content = MDBoxLayout(orientation='vertical', size_hint_y=None, height=dp(80))
        content.add_widget(field)
        def create():
            name = field.text.strip()
            if not name or len(name) > 40 or name.casefold() in [x.casefold() for x in self.library.data['lists']]:
                field.error = True
                field.helper_text = 'Use a unique name (1–40 characters).'
                field.helper_text_mode = 'on_error'
                return
            self.library.data['lists'][name] = []
            self.active_list = name
            if for_song:
                self.library.toggle(name, {'title': self.song_title, 'artist': self.song_artist})
            self.save_library()
            self.dismiss_dialog()
            if self.section == 'Lists':
                self.refresh_library()
        self.open_dialog(MDDialog(title='New list', type='custom', content_cls=content,
            buttons=[self.button('CANCEL', self.dismiss_dialog), self.button('CREATE', create)]))

    def delete_list(self):
        if self.active_list == 'Favorites':
            self.message('Favorites', 'Keep this default list. Remove songs from the list using the playlist button on a chord sheet.')
            return
        def remove():
            self.library.data['lists'].pop(self.active_list, None)
            self.active_list = 'Favorites'
            self.save_library()
            self.dismiss_dialog()
            self.refresh_library()
        self.open_dialog(MDDialog(title='Delete ' + self.active_list + '?', text='This removes the list from this device.',
            buttons=[self.button('CANCEL', self.dismiss_dialog), self.button('DELETE', remove)]))

    def practice_settings(self):
        content = MDBoxLayout(orientation='vertical', adaptive_height=True, spacing=dp(8))
        content.add_widget(self.button('TUNING: ' + self.tuning, self.choose_tuning))
        row = MDBoxLayout(size_hint_y=None, height=dp(48))
        label = Label(text=f'Capo: {int(self.capo)}')
        def change(amount):
            new = max(0, min(12, self.capo + amount))
            # Preserve sounding pitch while adapting the displayed chord shapes.
            self.transpose_steps -= new - self.capo
            self.capo = new
            label.text = f'Capo: {int(new)}'
            self.queue_render()
        row.add_widget(self.button('-', lambda: change(-1)))
        row.add_widget(label)
        row.add_widget(self.button('+', lambda: change(1)))
        content.add_widget(row)
        self.open_dialog(MDDialog(title='Practice settings', text='Capo changes chord shapes while preserving pitch.\nTuning changes diagrams and tuner targets.', type='custom', content_cls=content,
            buttons=[self.button('RESET KEY', self.reset_key), self.button('DONE', self.dismiss_dialog)]))

    def reset_key(self):
        self.transpose_steps = -self.capo
        self.queue_render()
        self.dismiss_dialog()

    def choose_tuning(self):
        content = MDBoxLayout(orientation='vertical', adaptive_height=True)
        for name, notes in TUNINGS.items():
            def select(name=name):
                self.tuning = name
                self.tuner_target = -1
                self.refresh_diagrams()
                self.refresh_strings()
                self.dismiss_dialog()
            content.add_widget(self.button(name + ' · ' + ' '.join(note_name(n) for n in notes), select))
        self.open_dialog(MDDialog(title='Guitar tuning', type='custom', content_cls=content,
                                  buttons=[self.button('CLOSE', self.dismiss_dialog)]))

    def open_tuner(self):
        self.stop_scroll()
        self.tuner_return = self.root.current
        self.root.current = 'tuner'
        self.refresh_strings()

    def refresh_strings(self):
        row = self.root.get_screen('tuner').ids.strings
        row.clear_widgets()
        for index, note in enumerate(TUNINGS[self.tuning]):
            button = self.button(note_name(note), lambda index=index: setattr(self, 'tuner_target', index))
            button._min_width = dp(36)
            button.padding = [dp(4), 0, dp(4), 0]
            button.size_hint_x = 1
            row.add_widget(button)

    def toggle_microphone(self):
        if self.mic_requested:
            self.stop_microphone()
            return
        try:
            if self.audio is None:
                from opentuna.audio_engine import AudioEngine
                self.audio = AudioEngine()
            self.mic_requested = True
            self.tuner_status = 'Requesting microphone…'
            self.audio.request_permission_and_start(self.audio_status)
        except Exception:
            logging.exception('Tuner unavailable')
            self.mic_requested = False
            self.tuner_status = 'Audio unavailable. Install the desktop audio dependencies.'

    def audio_status(self, message):
        self.tuner_status = message
        if self.audio and not self.audio.audio_enabled and 'Listening' not in message:
            self.mic_requested = False

    def update_tuner(self, dt):
        if not self.root or self.root.current != 'tuner':
            return
        frequency = self.audio.current_freq if self.audio and self.mic_requested else 0
        self.tuner_signal = frequency > 0
        if frequency <= 0:
            self.tuner_note = '--'
            self.tuner_reading = 'Pluck a string' if self.mic_requested else 'Microphone off'
            self.tuner_cents = 0
            return
        midi = 69 + 12 * math.log2(frequency / 440)
        target = round(midi) if self.tuner_target < 0 else TUNINGS[self.tuning][int(self.tuner_target)]
        cents = (midi - target) * 100
        self.tuner_note = note_name(target)
        self.tuner_cents = cents
        direction = 'In tune' if abs(cents) < 5 else 'Tune up' if cents < 0 else 'Tune down'
        self.tuner_reading = f'{frequency:.1f} Hz  ·  {cents:+.0f} cents  ·  {direction}'

    def stop_microphone(self):
        self.mic_requested = False
        if self.audio:
            self.audio.stop()
        self.tuner_status = 'Microphone off.'
        self.tuner_signal = False

    def close_tuner(self):
        self.stop_microphone()
        self.root.current = getattr(self, 'tuner_return', 'search')

    def on_keyboard(self, window, key, *args):
        if key == 27:
            if self.dialog:
                self.dismiss_dialog()
            elif self.root.current == 'tuner':
                self.close_tuner()
            elif self.root.current == 'lyrics':
                self.back_to_search()
            else:
                return False
            return True
        return False

    def on_pause(self):
        self.stop_scroll()
        self.stop_microphone()
        self.save_library()
        return True

    def on_stop(self):
        self.closed = True
        self.service.stopping = self.search_service.stopping = True
        self.stop_scroll()
        self.stop_microphone()
        self.save_library()
        self.search_executor.shutdown(wait=False, cancel_futures=True)
        self.executor.shutdown(wait=False, cancel_futures=True)
        self.diagram_executor.shutdown(wait=False, cancel_futures=True)


if __name__ == '__main__':
    OpenCifraApp().run()
