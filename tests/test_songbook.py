import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

from music import ChordBook, TUNINGS
from songbook import Library, SongService, parse_song, transpose


class SongTests(unittest.TestCase):
    def test_transposition(self):
        for original, amount, expected in [('Bbmaj7/D', 2, 'Cmaj7/E'), ('C', -1, 'B'), ('F#m7', 12, 'F#m7'), ('[Verse]', 2, '[Verse]')]:
            self.assertEqual(transpose(original, amount), expected)

    def test_parser_escapes_markup_and_preserves_chords(self):
        song = parse_song('<pre>[Verse]\n<b class="chord">C</b>    <strong>G/B</strong>\nA &amp; B<br>Last</pre>', 't', 'a', 'url')
        rendered = song.render(2)
        self.assertIn('&bl;Verse&br;', rendered)
        self.assertIn('[ref=D]', rendered)
        self.assertIn('[ref=A/C#]', rendered)
        self.assertIn('A &amp; B\nLast', rendered)

    def test_hide_tabs_keeps_lyrics(self):
        song = parse_song('<pre>Intro\ne|--0-2h3--|\nB|--1-----|\nE|--0-----|\nSing a song\n<b>C</b></pre>', 't', 'a', 'u')
        self.assertIn('2h3', song.render())
        self.assertNotIn('2h3', song.render(hide_tabs=True))
        self.assertIn('Sing a song', song.render(hide_tabs=True))
        self.assertIn('[ref=C]', song.render(hide_tabs=True))

    def test_missing_sheet(self):
        with self.assertRaises(ValueError):
            parse_song('<html>Unavailable</html>', 't', 'a', 'u')

    def test_chord_spacing(self):
        song = parse_song('<pre><b>C</b>    <b>G</b></pre>', 't', 'a', 'u')
        self.assertIn('[/ref]   [ref=G#]', song.render(1))

    def test_search_params_dedup_and_cache(self):
        service = SongService()
        service.session = Mock()
        response = service.session.get.return_value
        response.text = 'suggest_callback(' + json.dumps({'response': {'docs': [
            {'t': '2', 'm': 'Song', 'a': 'Artist'}, {'t': 2, 'm': 'Song', 'a': 'Artist'},
            {'t': '1', 'm': 'Not a song', 'a': 'Artist'}]}}) + ');'
        self.assertEqual(service.search('a & b'), [{'title': 'Song', 'artist': 'Artist'}])
        self.assertEqual(service.session.get.call_args.kwargs['params']['q'], 'a & b')
        service.search('A & B')
        self.assertEqual(service.session.get.call_count, 1)

    def test_fetch_fallback_and_cache(self):
        service = SongService()
        service.session = Mock()
        missing, found = Mock(status_code=404), Mock(status_code=200, text='<pre><b>C</b> Test</pre>')
        service.session.get.side_effect = [missing, found]
        song = service.fetch('Song', 'A & B')
        self.assertIn('/a-e-b/song/', song.url)
        self.assertIs(service.fetch('Song', 'A & B'), song)
        self.assertEqual(service.session.get.call_count, 2)

    def test_cache_bound(self):
        service = SongService()
        for i in range(20):
            service.remember(service.song_cache, i, i, 12)
        self.assertEqual(len(service.song_cache), 12)
        self.assertNotIn(0, service.song_cache)

    def test_library_roundtrip(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'library.json'
            library = Library(path)
            song = {'title': 'Song', 'artist': 'Artist'}
            self.assertTrue(library.toggle('Practice', song))
            library.visit(**song)
            library.visit(**song)
            library.save()
            restored = Library(path)
            self.assertEqual(restored.data['lists']['Practice'], [song])
            self.assertEqual(len(restored.data['recent']), 1)
            self.assertFalse(restored.toggle('Practice', song))
            self.assertNotIn('lyrics', path.read_text())

    def test_corrupt_library(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'library.json'
            for value in ('broken', '[]', '{"recent": 12, "lists": {"Test": [null]}}'):
                path.write_text(value)
                library = Library(path)
                self.assertEqual(library.data['recent'], [])
                self.assertIn('Favorites', library.data['lists'])

    def test_diagrams_preserve_pitches_in_drop_d(self):
        book = ChordBook()
        standard = book.voicing('C')
        drop = book.voicing('C', 'Drop D')
        self.assertIsNotNone(standard)
        self.assertIsNotNone(drop)
        self.assertEqual({(f + n) % 12 for f, n in zip(standard, TUNINGS['Standard']) if f >= 0},
                         {(f + n) % 12 for f, n in zip(drop, TUNINGS['Drop D']) if f >= 0})
        self.assertIsNone(book.voicing('not-a-chord'))
