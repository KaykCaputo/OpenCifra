"""Run with xvfb-run -a python tests/ui_smoke.py; no network or microphone."""
from pathlib import Path
import sys
import tempfile
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from kivy.clock import Clock
from kivy.core.window import Window
from main import OpenCifraApp
from songbook import parse_song

app = OpenCifraApp()
app._user_data_dir = tempfile.mkdtemp(prefix='opencifra-ui-')
Window.size = (390, 844)
errors = []

def step(callback):
    def invoke(dt):
        try:
            callback()
        except Exception as error:
            errors.append(error)
            app.stop()
            raise
    return invoke


def home():
    app.root.get_screen('search').ids.results.data = [
        {'title': 'Evening practice', 'artist': 'Demo · original exercise'},
        {'title': 'Open strings', 'artist': 'Demo · guitar warm-up'}]
    app.search_status = '2 songs found'


def sheet():
    app.root.current = 'lyrics'
    app.song_title, app.song_artist = 'Evening practice', 'Original exercise'
    song = parse_song('<pre>[Verse]\n<b>C</b>       <b>G/B</b>     <b>Am7</b>     <b>F</b>\nLet the open strings ring\n\ne|--0--1--3--|\nB|--1-------|\n\n[Practice]\n' + ('<b>C</b>       <b>G</b>\nPlay slowly and let it ring\n' * 30) + '</pre>', 'Evening practice', 'Original exercise', 'https://example.test')
    app.song_done(app.song_generation, song, None)
    assert app.song_ready


def controls():
    app.change_font(2)
    app.change_key(2)
    app.toggle_tabs()
    app.library.toggle('Practice', {'title': app.song_title, 'artist': app.song_artist})
    app.save_library()
    app.search_generation = 4
    app.search_done(3, [{'title': 'Stale', 'artist': 'Wrong'}], None)
    assert all(x['title'] != 'Stale' for x in app.root.get_screen('search').ids.results.data)


def auto_scroll():
    app.toggle_scroll()
    assert app.scrolling
    app.scroll_tick(1)
    assert app.root.get_screen('lyrics').ids.lyrics_scroll.scroll_y < 1
    app.stop_scroll()


def dialog_checks():
    app.practice_settings()
    app.dismiss_dialog()
    app.choose_list(True)
    app.dismiss_dialog()
    app.new_list()
    app.dismiss_dialog()
    app.choose_tuning()
    app.dismiss_dialog()
    app.show_chord('D')


def library():
    app.dismiss_dialog()
    app.back_to_search()
    app.select_section('Lists')
    app.active_list = 'Practice'
    app.refresh_library()
    assert len(app.root.get_screen('search').ids.results.data) == 1


def tuner():
    app.open_tuner()
    assert not app.mic_requested


def capture(name):
    app.root.export_to_png('/tmp/opencifra-' + name + '.png')

actions = [home, lambda: capture('home'), sheet, lambda: capture('song'), controls,
           auto_scroll, dialog_checks, lambda: capture('chord'), library,
           lambda: capture('lists'), tuner, lambda: capture('tuner'),
           lambda: setattr(Window, 'size', (360, 640)), app.close_tuner, sheet,
           lambda: capture('small'), lambda: setattr(Window, 'size', (1280, 800)),
           lambda: capture('desktop'), app.stop]

def next_action(dt):
    if actions:
        step(actions.pop(0))(dt)
        if actions:
            Clock.schedule_once(next_action, .8)

Clock.schedule_once(next_action, 2)
app.run()
if errors:
    raise SystemExit(1)
print('UI smoke passed: navigation, controls, dialogs, lists, stale search and auto-scroll.')
