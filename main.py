from kivy.lang import Builder
from kivy.clock import Clock
from kivy.properties import StringProperty
from kivymd.app import MDApp
from kivymd.uix.card import MDCard
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.label import MDLabel
from kivy.metrics import dp
import threading
import requests
import json
import re
from bs4 import BeautifulSoup

KV = """
<SongItem@MDCard+ButtonBehavior>:
    title: ""
    artist: ""
    radius: [15]
    padding: "8dp"
    size_hint_y: None
    height: dp(82)
    md_bg_color: app.theme_cls.bg_light
    elevation: 2
    ripple_behavior: True
    on_release: app.open_song(root.title, root.artist)

    MDBoxLayout:
        orientation: "horizontal"
        spacing: "12dp"
        adaptive_height: True
        pos_hint: {"center_y": .5}

        MDIcon:
            icon: "music-note-outline"
            size_hint: None, None
            size: dp(40), dp(40)
            theme_text_color: "Custom"
            text_color: app.theme_cls.primary_color
            pos_hint: {"center_y": .5}

        MDBoxLayout:
            orientation: "vertical"
            spacing: "4dp"
            adaptive_height: True
            pos_hint: {"center_y": .5}

            MDLabel:
                text: root.title
                font_style: "Subtitle1"
                theme_text_color: "Primary"
                shorten: True
                shorten_from: "right"
                adaptive_height: True
                bold: True

            MDLabel:
                text: root.artist
                font_style: "Caption"
                theme_text_color: "Secondary"
                shorten: True
                shorten_from: "right"
                adaptive_height: True

<SearchScreen>:
    name: "search"
    MDBoxLayout:
        orientation: "vertical"
        md_bg_color: app.theme_cls.bg_dark

        MDTopAppBar:
            title: "OpenCifra"
            anchor_title: "center"
            elevation: 4
            md_bg_color: app.theme_cls.primary_color
            left_action_items: [["guitar-pick", lambda x: None]]
            right_action_items: [["", lambda x: None]]

        MDBoxLayout:
            orientation: "vertical"
            padding: "16dp"
            spacing: "12dp"

            MDTextField:
                id: search_field
                hint_text: "Search song or artist"
                mode: "fill"
                size_hint_x: 1
                on_text: app.on_search_text(self.text)
                multiline: False

            MDRecycleView:
                id: rv
                viewclass: "SongItem"
                RecycleBoxLayout:
                    spacing: "12dp"
                    padding: ["4dp", "8dp", "4dp", "40dp"]
                    default_size_hint: 1, None
                    size_hint_y: None
                    height: self.minimum_height
                    orientation: "vertical"

        MDLabel:
            text: "Made by Kayk Caputo"
            size_hint_y: None
            height: dp(40)
            halign: "center"
            theme_text_color: "Hint"
            font_style: "Caption"

<LyricsScreen>:
    name: "lyrics"
    song_title: ""
    song_text: ""
    MDBoxLayout:
        orientation: "vertical"
        md_bg_color: app.theme_cls.bg_dark

        MDTopAppBar:
            title: root.song_title
            anchor_title: "center"
            left_action_items: [["arrow-left", lambda x: app.back_to_search()]]
            right_action_items: [["", lambda x: None]]
            elevation: 4
            md_bg_color: app.theme_cls.primary_color

        MDScrollView:
            id: lyrics_scroll
            do_scroll_x: False
            do_scroll_y: True
            bar_width: dp(4)
            
            MDBoxLayout:
                id: lyrics_container
                orientation: "vertical"
                size_hint: None, None
                height: self.minimum_height
                padding: "8dp"
                spacing: 0
"""


CHUNK_SIZE = 50


class SongItem(MDCard):
    title = StringProperty()
    artist = StringProperty()


class SearchScreen(MDScreen):
    pass


class LyricsScreen(MDScreen):
    song_title = StringProperty()
    song_text = StringProperty()


class OpenCifraApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Blue"
        Builder.load_string(KV)
        self.search_lock = threading.Lock()
        self.sm = MDScreenManager()
        self.sm.add_widget(SearchScreen())
        self.sm.add_widget(LyricsScreen())
        return self.sm

    def on_search_text(self, text):
        if len(text) < 2:
            self.root.get_screen("search").ids.rv.data = []
            return
        if self.search_lock.locked():
            return
        threading.Thread(
            target=self.fetch_suggestions, args=(text,), daemon=True
        ).start()

    def fetch_suggestions(self, query):
        with self.search_lock:
            url = f"https://solr.sscdn.co/cc/h2/?q={query}&limit=8&callback=suggest_callback"
            headers = {"User-Agent": "Mozilla/5.0"}
            try:
                r = requests.get(url, headers=headers, timeout=5)
                raw = r.text.strip().replace("suggest_callback(", "")[:-1]
                data = json.loads(raw)
                results = []
                docs = data.get("response", {}).get("docs", [])
                for item in docs:
                    title = item.get("m")
                    artist = item.get("a")
                    if title and artist:
                        results.append({"title": title, "artist": artist})
                Clock.schedule_once(lambda dt: self.update_list(results), 0)
            except:
                pass

    def update_list(self, data):
        self.root.get_screen("search").ids.rv.data = data

    def open_song(self, title, artist):
        threading.Thread(
            target=self.fetch_song, args=(title, artist), daemon=True
        ).start()

    def normalize(self, text):
        text = text.lower()
        text = re.sub(r"[áàãâä]", "a", text)
        text = re.sub(r"[éèêë]", "e", text)
        text = re.sub(r"[íìîï]", "i", text)
        text = re.sub(r"[óòõôö]", "o", text)
        text = re.sub(r"[úùûü]", "u", text)
        text = re.sub(r"ç", "c", text)
        text = re.sub(r"[^a-z0-9& ]", "", text)
        return text.strip()

    def fetch_song(self, title, artist):
        slug_title = re.sub(r"\s+", "-", self.normalize(title))
        artist_norm = self.normalize(artist)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        variants = []
        if "&" in artist_norm:
            parts = [p.strip() for p in artist_norm.split("&")]
            variants.append("-".join(parts).replace(" ", "-"))
            variants.append("-e-".join(parts).replace(" ", "-"))
        else:
            variants.append(artist_norm.replace(" ", "-"))
        success = False
        for variant in variants:
            variant = re.sub(r"-+", "-", variant)
            url = f"https://www.cifraclub.com.br/{variant}/{slug_title}/"
            try:
                r = requests.get(url, headers=headers, timeout=10)
                if r.status_code == 200:
                    soup = BeautifulSoup(r.text, "html.parser")
                    pre = soup.find("pre")
                    if pre:
                        song_text = self.parse_cifra_html(pre)
                        Clock.schedule_once(
                            lambda dt: self.show_song(title, song_text), 0
                        )
                        success = True
                        break
            except:
                continue
        if not success:
            Clock.schedule_once(lambda dt: self.show_song(title, "Song not found."), 0)

    def parse_cifra_html(self, pre_tag):
        content = str(pre_tag)
        content = re.sub(r"<b>(.*?)</b>", r"CH_START\1CH_END", content)
        soup = BeautifulSoup(content, "html.parser")
        text = soup.get_text()
        text = text.replace("CH_START", "[b][color=44AAFF]").replace(
            "CH_END", "[/color][/b]"
        )
        return text.strip()

    def create_label_chunk(self, text):
        from kivy.uix.label import Label

        label = Label(
            text=text,
            markup=True,
            font_name="RobotoMono-Regular.ttf",
            font_size=dp(9),
            color=(1, 1, 1, 1),
            size_hint=(None, None),
            halign="left",
            valign="top",
        )
        label.texture_update()
        label.size = label.texture_size
        return label

    def show_song(self, title, text):
        screen = self.root.get_screen("lyrics")
        screen.song_title = title
        container = screen.ids.lyrics_container
        container.clear_widgets()
        lines = text.split("\n")
        max_width = 0
        for i in range(0, len(lines), CHUNK_SIZE):
            chunk = "\n".join(lines[i : i + CHUNK_SIZE])
            label = self.create_label_chunk(chunk)
            container.add_widget(label)
            if label.width > max_width:
                max_width = label.width
        container.width = max_width + dp(16)
        self.root.current = "lyrics"
        Clock.schedule_once(self.reset_view, 0.2)

    def reset_view(self, dt):
        scroll = self.root.get_screen("lyrics").ids.lyrics_scroll
        scroll.scroll_y = 1
        scroll.scroll_x = 0

    def back_to_search(self):
        self.root.current = "search"


if __name__ == "__main__":
    OpenCifraApp().run()
