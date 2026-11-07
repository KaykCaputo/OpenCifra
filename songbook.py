"""Network, chord formatting and local library; independent of the UI."""
from collections import OrderedDict
from dataclasses import dataclass
import json
from pathlib import Path
import re
import unicodedata

from bs4 import BeautifulSoup, NavigableString
import requests

NOTES = ('C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B')
FLATS = {'Db': 'C#', 'Eb': 'D#', 'Gb': 'F#', 'Ab': 'G#', 'Bb': 'A#', 'Cb': 'B', 'Fb': 'E', 'E#': 'F', 'B#': 'C'}
CHORD = re.compile(r'^([A-G](?:##|bb|#|b)?)([^\s]*?)(?:/([A-G](?:##|bb|#|b)?))?$')
TAB = re.compile(r'^\s*(?:[A-Ga-g][#b]?)?\s*[|:]\s*[-─–0-9xhHpPbBrR~()/\\<>. =|:]+$')


def escape(text):
    return text.replace('&', '&amp;').replace('[', '&bl;').replace(']', '&br;')


def transpose(chord, steps):
    match = CHORD.fullmatch(chord)
    if not match or not steps:
        return chord
    def shift(note):
        natural = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
        return NOTES[(natural[note[0]] + note[1:].count('#') - note[1:].count('b') + steps) % 12]
    root, suffix, bass = match.groups()
    return shift(root) + suffix + ('/' + shift(bass) if bass else '')


def slug(text):
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'-+', '-', re.sub(r'[^a-z0-9]+', '-', text)).strip('-')


@dataclass
class Song:
    title: str
    artist: str
    url: str
    lines: list
    credits: str = ''

    def render(self, steps=0, hide_tabs=False):
        output = []
        for line in self.lines:
            plain = ''.join(text for text, _ in line)
            if hide_tabs and TAB.fullmatch(plain):
                continue
            pieces = []
            debt = 0
            for text, is_chord in line:
                if is_chord:
                    changed = transpose(text, steps)
                    safe = escape(changed)
                    pieces.append(f'[ref={safe}][b][color=B388FF]{safe}[/color][/b][/ref]')
                    debt += len(changed) - len(text)
                else:
                    # Absorb chord-width changes in following whitespace.
                    spaces = len(text) - len(text.lstrip(' '))
                    if spaces and debt:
                        adjusted = max(1, spaces - debt)
                        text = ' ' * adjusted + text[spaces:]
                        debt = 0
                    pieces.append(escape(text))
            output.append(''.join(pieces))
        return '\n'.join(output)


def parse_song(html, title, artist, url):
    soup = BeautifulSoup(html, 'html.parser')
    pre = soup.find('pre')
    if pre is None:
        raise ValueError('This page has no chord sheet available.')
    lines = [[]]
    for node in pre.descendants:
        if getattr(node, 'name', None) == 'br':
            lines.append([])
        elif isinstance(node, NavigableString):
            chord = any(parent.name in ('b', 'strong') for parent in node.parents)
            for index, part in enumerate(str(node).replace('\r', '').split('\n')):
                if index:
                    lines.append([])
                if part:
                    # Each chord is independently transposable and clickable.
                    for token in re.split(r'(\s+)', part) if chord else [part]:
                        if token:
                            lines[-1].append((token, chord and bool(CHORD.fullmatch(token))))
    footer = soup.find(class_='cifra-footer')
    credits = footer.get_text(' ', strip=True) if footer else ''
    return Song(title, artist, url, lines, credits)


class SongService:
    """Used by a single worker, with bounded session-only caches."""
    def __init__(self):
        self.stopping = False
        self.session = requests.Session()
        self.session.headers['User-Agent'] = 'Mozilla/5.0 (OpenCifra songbook)'
        self.search_cache = OrderedDict()
        self.song_cache = OrderedDict()

    @staticmethod
    def remember(cache, key, value, limit):
        cache[key] = value
        cache.move_to_end(key)
        while len(cache) > limit:
            cache.popitem(last=False)
        return value

    def search(self, query):
        key = query.strip().casefold()
        if key in self.search_cache:
            return self.search_cache[key]
        response = self.session.get('https://solr.sscdn.co/cc/h2/', params={
            'q': query, 'limit': 30, 'callback': 'suggest_callback'}, timeout=(4, 8))
        response.raise_for_status()
        raw = response.text.strip()
        if raw.startswith('suggest_callback('):
            raw = raw[len('suggest_callback('):].rstrip(';').rstrip().removesuffix(')')
        docs = json.loads(raw).get('response', {}).get('docs', [])
        results, seen = [], set()
        for item in docs:
            title, artist = item.get('m'), item.get('a')
            if str(item.get('t')) == '2' and isinstance(title, str) and isinstance(artist, str):
                pair = (title, artist)
                if pair not in seen:
                    seen.add(pair)
                    results.append({'title': title, 'artist': artist})
        return self.remember(self.search_cache, key, results, 40)

    def fetch(self, title, artist):
        key = (title, artist)
        if key in self.song_cache:
            self.song_cache.move_to_end(key)
            return self.song_cache[key]
        artists = list(dict.fromkeys([slug(artist), slug(artist.replace('&', ' e '))]))
        artists += [a.replace('-a-', '-') for a in artists if '-a-' in a]
        titles = list(dict.fromkeys([slug(title), slug(title).replace('-a-', '-')]))
        for artist_slug in artists:
            for title_slug in titles:
                if self.stopping:
                    raise ValueError('Request cancelled.')
                url = f'https://www.cifraclub.com.br/{artist_slug}/{title_slug}/'
                response = self.session.get(url, timeout=(4, 10))
                if response.status_code == 404:
                    continue
                response.raise_for_status()
                try:
                    song = parse_song(response.text, title, artist, url)
                except ValueError:
                    continue
                return self.remember(self.song_cache, key, song, 12)
        raise ValueError('No chord sheet found. Try another version or song.')


class Library:
    def __init__(self, path):
        self.path = Path(path)
        self.data = {'lists': {'Favorites': []}, 'recent': [], 'settings': {}}
        try:
            data = json.loads(self.path.read_text(encoding='utf-8'))
            if not isinstance(data, dict):
                return
            def valid(items):
                return [x for x in items if isinstance(x, dict) and all(
                    isinstance(x.get(k), str) for k in ('title', 'artist'))] if isinstance(items, list) else []
            lists = data.get('lists', {})
            if isinstance(lists, dict):
                self.data['lists'].update({k: valid(v) for k, v in lists.items() if k.strip()})
            self.data['recent'] = valid(data.get('recent'))[:30]
            if isinstance(data.get('settings'), dict):
                self.data['settings'] = data['settings']
        except (OSError, ValueError):
            pass

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix('.tmp')
        temporary.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding='utf-8')
        temporary.replace(self.path)

    def visit(self, title, artist):
        item = {'title': title, 'artist': artist}
        self.data['recent'] = [item] + [x for x in self.data['recent'] if x != item][:29]

    def toggle(self, name, item):
        items = self.data['lists'].setdefault(name, [])
        if item in items:
            items.remove(item)
            return False
        items.append(item)
        return True
