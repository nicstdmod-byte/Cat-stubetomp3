"""Tests for helper/naming.py. Run: python3 -m unittest discover tests"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "helper"))
import naming  # noqa: E402

DEFAULTS = {"namePattern": "{artist} - {title}", "subfolderPattern": "{playlist}", "cleanJunk": True}


def name(title, channel="Some Channel", **settings):
    return naming.build_filename({"title": title, "channel": channel, "index": 3, "total": 12, "id": "abc"},
                                 {**DEFAULTS, **settings})


class CleanTitle(unittest.TestCase):
    def test_removes_junk_brackets(self):
        self.assertEqual(naming.clean_title("Song (Official Video)"), "Song")
        self.assertEqual(naming.clean_title("Song [Lyrics]"), "Song")
        self.assertEqual(naming.clean_title("Song (Official Music Video) [HD]"), "Song")
        self.assertEqual(naming.clean_title("Song (Audio)"), "Song")

    def test_keeps_meaningful_brackets(self):
        self.assertEqual(naming.clean_title("Song (feat. Someone)"), "Song (feat. Someone)")
        self.assertEqual(naming.clean_title("Song (Remix)"), "Song (Remix)")
        self.assertEqual(naming.clean_title("Song (Acoustic)"), "Song (Acoustic)")


class ArtistTitle(unittest.TestCase):
    def test_splits_dash_titles(self):
        self.assertEqual(naming.split_artist_title("Artist - Song (Official Video)", "X"), ("Artist", "Song"))
        self.assertEqual(naming.split_artist_title("Artist – Song", "X"), ("Artist", "Song"))

    def test_falls_back_to_channel(self):
        self.assertEqual(naming.split_artist_title("Song", "Artist - Topic"), ("Artist", "Song"))
        self.assertEqual(naming.split_artist_title("Song", "ArtistVEVO"), ("Artist", "Song"))
        self.assertEqual(naming.split_artist_title("Song", ""), ("Unknown Artist", "Song"))

    def test_clean_off_keeps_junk(self):
        self.assertEqual(naming.split_artist_title("A - Song (Official Video)", "X", clean=False),
                         ("A", "Song (Official Video)"))


class Filenames(unittest.TestCase):
    def test_default_pattern(self):
        self.assertEqual(name("Artist - Song (Official Video)"), "Artist - Song")

    def test_other_patterns(self):
        self.assertEqual(name("Artist - Song", namePattern="{track} - {title}"), "03 - Song")
        self.assertEqual(name("Artist - Song", namePattern="{title} [{id}]"), "Song [abc]")

    def test_windows_unsafe_characters(self):
        self.assertEqual(name('AC/DC - What? "Yes": <No>*'), "AC-DC - What Yes No")

    def test_reserved_names_and_trailing_dots(self):
        self.assertEqual(naming.sanitize_component("CON"), "_CON")
        self.assertEqual(naming.sanitize_component("Song..."), "Song")

    def test_long_names_are_cut(self):
        self.assertLessEqual(len(name("A - " + "x" * 400)), naming.MAX_NAME_LENGTH)

    def test_empty_result_falls_back(self):
        # Pattern renders empty and the title has no safe characters left, so the video ID is used.
        self.assertEqual(name("???", channel="", namePattern="{date}"), "abc")


class Subfolders(unittest.TestCase):
    def test_patterns(self):
        self.assertEqual(naming.build_subfolder("My List", "Chan", DEFAULTS), ["My List"])
        self.assertEqual(naming.build_subfolder("My List", "Chan", {"subfolderPattern": "{channel}/{playlist}"}),
                         ["Chan", "My List"])
        self.assertEqual(naming.build_subfolder("", "Chan", DEFAULTS), [])
        self.assertEqual(naming.build_subfolder("A/B: C", "Chan", DEFAULTS), ["A-B C"])


if __name__ == "__main__":
    unittest.main()
