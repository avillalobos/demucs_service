#!/usr/bin/python3

from sqlite3.dbapi2 import Cursor
from typing import Iterator
import zipfile
import testslide
import unittest
import pytube
from testslide.strict_mock import StrictMock
import lib.utils as utils
import pathlib
from unittest.mock import patch
import os
import sqlite3


class FakeIterator(Iterator):
    pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self


class TestUtils(testslide.TestCase):

    def __init__(self, methodName: str) -> None:
        super().__init__(methodName=methodName)
        self.fake_url = "https://youtu.be/NotARealURL_sad_face"
        self.fake_youtube_song_name = \
            "This is an amazing song from youtube.mp4"
        self.fake_youtube_song_mp3 = \
            "songs/This is an amazing song from youtube.mp3"
        self.fake_model = "notreal"
        self.fake_song_path = \
            pathlib.Path('separated') /\
            pathlib.Path(self.fake_model) /\
            pathlib.Path(self.fake_youtube_song_mp3).name
        self.fake_download_path = pathlib.Path("downloads") / pathlib.Path(
            f"{self.fake_song_path.stem}.zip"
        )
        self.fake_download_url = "ThisIsAHashBelieveMe!"
        self.fake_download_db = pathlib.Path('models/database.db')
        self.fake_query = """
INSERT INTO downloads (song_path, download_url, accessed)
values (?, ?, False)"""
        self.fake_parameters = (self.fake_song_path, self.fake_download_url,)

    def test_video_to_mp3_successful(self):
        fake_youtube_instance = StrictMock(
            pytube.YouTube, runtime_attrs=["streams"]
        )

        fake_strean_query = StrictMock(
            pytube.query.StreamQuery, runtime_attrs=["filter"]
        )
        fake_sorted_stream_query = StrictMock(
            pytube.query.StreamQuery,
            runtime_attrs=[
                "order_by",
                "desc",
                "first",
                "download"
            ]
        )
        fake_stream = StrictMock(
            pytube.streams.Stream, runtime_attrs=["download"]
        )
        fake_sorted_stream_query.order_by = lambda x: fake_sorted_stream_query
        fake_sorted_stream_query.desc = lambda: fake_sorted_stream_query
        fake_sorted_stream_query.first = lambda: fake_stream
        fake_stream.download = lambda output_path: self.fake_youtube_song_name
        fake_strean_query.filter = \
            lambda progressive, file_extension: fake_sorted_stream_query
        fake_youtube_instance.streams = fake_strean_query

        self.mock_constructor(
            pytube, "YouTube"
        ).for_call(
            self.fake_url
        ).to_return_value(
            fake_youtube_instance
        )

        self.mock_callable(
            utils, "mp4_to_mp3"
        ).for_call(
            self.fake_youtube_song_name
        ).to_return_value(
            self.fake_youtube_song_mp3
        ).and_assert_called_once()

        self.assertEqual(
            utils.video_to_mp3(self.fake_url), self.fake_youtube_song_mp3
        )

    def test_video_to_mp3_failure(self):
        self.mock_constructor(
            pytube, "YouTube"
        ).for_call(
            self.fake_url
        ).to_raise(Exception)

        self.assertRaises(Exception, utils.video_to_mp3(self.fake_url))

    @patch('moviepy.editor.VideoFileClip', autospec=True)
    @patch('moviepy.editor.AudioFileClip', autospec=True)
    def test_mp4_to_mp3_successful(
        self,
        fake_audio_clip,
        fake_video_file_clip
    ):
        # coldn't use StrictMock because __new__ is not supported and
        # it was constantly failing when mocking VideoFileClip
        with patch.object(pathlib.Path, "unlink") as fake_path:
            fake_path.unlink.return_value = True
            fake_video_file_clip.return_value.audio = fake_audio_clip
            fake_audio_clip.return_value.write_audiofile = lambda x: True
            self.assertEqual(
                utils.mp4_to_mp3(self.fake_youtube_song_name),
                self.fake_youtube_song_mp3
            )

    @patch('moviepy.editor.VideoFileClip', autospec=True)
    def test_mp4_to_mp3_failure(self, fake_video_file_clip):
        # coldn't use StrictMock because __new__ is not supported and
        # it was constantly failing when mocking VideoFileClip
        fake_video_file_clip.side_effect = IOError("Boom!")
        self.assertIsNone(
            utils.mp4_to_mp3(self.fake_youtube_song_name)
        )

    @patch('moviepy.editor.VideoFileClip', autospec=True)
    @patch('moviepy.editor.AudioFileClip', autospec=True)
    def test_mp4_to_mp3_file_not_found(
        self,
        fake_audio_clip,
        fake_video_file_clip
    ):
        # coldn't use StrictMock because __new__ is not supported and
        # it was constantly failing when mocking VideoFileClip
        with patch.object(pathlib.Path, "unlink") as fake_path:
            fake_path.unlink.side_effect = FileNotFoundError()
            fake_video_file_clip.return_value.audio = fake_audio_clip
            fake_audio_clip.return_value.write_audiofile = lambda x: True
            self.assertEqual(
                utils.mp4_to_mp3(self.fake_youtube_song_name),
                self.fake_youtube_song_mp3
            )

    def _fake_iter(self):
        for dir in ["bass.wav", "voice.wav", "drums.wav", "other.wav"]:
            tmp_dir = StrictMock(os.DirEntry, runtime_attrs=["path", "name"])
            tmp_dir.path = dir
            tmp_dir.name = dir
            yield tmp_dir

    def test_zip_files_successful(self):
        fake_zipfile_manager = StrictMock(
            zipfile.ZipFile,
            runtime_attrs=["write"],
            default_context_manager=True
        )
        fake_zipfile_manager.write = lambda x, arcname: True
        self.mock_constructor(
            zipfile, "ZipFile"
        ).for_call(
            self.fake_download_path, 'w'
        ).to_return_value(fake_zipfile_manager)

        fake_zipfile_manager.__enter__ = lambda: fake_zipfile_manager

        scandir_iterator = StrictMock(
            FakeIterator,
            default_context_manager=True,
            runtime_attrs=["__iter__"]
        )

        fake_song_path = pathlib.Path(
            str(self.fake_song_path).replace(".mp3", "")
        )
        scandir_iterator.__iter__ = self._fake_iter
        self.mock_callable(
            os, "scandir"
        ).for_call(
            fake_song_path
        ).to_return_value(
            scandir_iterator
        )

        download_path = utils.zip_files(
            self.fake_model, self.fake_song_path.stem
        )

        # we want to know if we can resolve the same path we expect
        self.assertEqual(
            download_path.resolve(), self.fake_download_path.resolve()
        )

    def test_zip_files_failure(self):
        fake_zipfile_manager = StrictMock(
            zipfile.ZipFile,
            runtime_attrs=["write"],
            default_context_manager=True
        )
        fake_zipfile_manager.write = lambda x, arcname: True
        self.mock_constructor(
            zipfile, "ZipFile"
        ).for_call(
            self.fake_download_path, 'w'
        ).to_return_value(fake_zipfile_manager)

        fake_zipfile_manager.__enter__ = lambda: fake_zipfile_manager

        scandir_iterator = StrictMock(
            FakeIterator,
            default_context_manager=True,
            runtime_attrs=["__iter__"]
        )

        fake_song_path = pathlib.Path(
            str(self.fake_song_path).replace(".mp3", "")
        )
        scandir_iterator.__iter__ = self._fake_iter
        self.mock_callable(
            os, "scandir"
        ).for_call(
            fake_song_path
        ).to_raise(FileNotFoundError)
        # we want to know if we can resolve the same path we expect
        self.assertIsNone(
            utils.zip_files(
                self.fake_model, self.fake_song_path.stem
            )
        )

    def test_db_execute(self):

        fake_db = StrictMock(
            sqlite3.Connection, runtime_attrs=["execute", "commit"],
            default_context_manager=True
        )
        fake_db.execute = lambda: True
        fake_db.commit = lambda: True
        self.mock_callable(fake_db, "execute").for_call(
            """
INSERT INTO downloads (song_path, download_url, accessed)
values (?, ?, False)""",
            (self.fake_song_path, self.fake_download_url,)
        ).to_return_value(None).and_assert_called_once()
        self.mock_callable(
            fake_db, "commit"
        ).for_call().to_return_value(None).and_assert_called_once()
        self.mock_callable(
            sqlite3, "connect"
        ).for_call(
            self.fake_download_db
        ).to_return_value(fake_db)

        with patch.object(pathlib.Path, "exists") as fake_download_db:
            fake_download_db.return_value = True
            utils.db_execute(
                self.fake_query, self.fake_parameters
            )

    def test_db_exceute_no_db_file(self):
        with patch.object(pathlib.Path, "exists") as fake_download_db:
            fake_download_db.return_value = False
            with self.assertRaises(FileNotFoundError):
                utils.db_execute(
                    self.fake_query, self.fake_parameters
                )

    def test_db_exceute_failed_to_execute(self):

        fake_db = StrictMock(
            sqlite3.Connection, runtime_attrs=["execute"],
            default_context_manager=True
        )
        fake_db.execute = lambda: True
        self.mock_callable(fake_db, "execute").for_call(
            """
INSERT INTO downloads (song_path, download_url, accessed)
values (?, ?, False)""",
            (self.fake_song_path, self.fake_download_url,)
        ).to_raise(Exception).and_assert_called_once()
        self.mock_callable(
            sqlite3, "connect"
        ).for_call(
            self.fake_download_db
        ).to_return_value(fake_db)

        with patch.object(pathlib.Path, "exists") as fake_download_db:
            fake_download_db.return_value = True
            with self.assertRaises(Exception):
                utils.db_execute(
                    self.fake_query, self.fake_parameters
                )

    def test_db_exceute_failed_to_commit(self):

        fake_db = StrictMock(
            sqlite3.Connection, runtime_attrs=["execute", "commit"],
            default_context_manager=True
        )
        fake_db.execute = lambda: True
        fake_db.commit = lambda: True
        self.mock_callable(fake_db, "execute").for_call(
            """
INSERT INTO downloads (song_path, download_url, accessed)
values (?, ?, False)""",
            (self.fake_song_path, self.fake_download_url,)
        ).to_return_value(None).and_assert_called_once()
        self.mock_callable(
            fake_db, "commit"
        ).for_call().to_raise(
            Exception
        ).and_assert_called_once()
        self.mock_callable(
            sqlite3, "connect"
        ).for_call(
            self.fake_download_db
        ).to_return_value(fake_db)

        with patch.object(pathlib.Path, "exists") as fake_download_db:
            fake_download_db.return_value = True
            with self.assertRaises(Exception):
                utils.db_execute(
                    self.fake_query, self.fake_parameters
                )

    def test_create_new_download_successful(self):
        self.mock_callable(utils, "db_execute").for_call(
            """
INSERT INTO downloads (song_path, download_url, accessed)
values (?, ?, False)""",
            (self.fake_song_path, self.fake_download_url,)
        ).to_return_value(None).and_assert_called_once()

        with patch.object(pathlib.Path, "exists") as fake_download_db:
            fake_download_db.return_value = True
            utils.create_new_download(
                self.fake_song_path, self.fake_download_url
            )

    def test_disable_download_successful(self):
        self.mock_callable(utils, "db_execute").for_call(
            """
UPDATE downloads SET accessed = True
WHERE download_url = ? AND accessed = False""",
            (self.fake_download_url,)
        ).to_return_value(None).and_assert_called_once()

        with patch.object(pathlib.Path, "exists") as fake_download_db:
            fake_download_db.return_value = True
            utils.disable_download(
                self.fake_download_url
            )

    def test_get_download_file_successful(self):
        fake_song = 'path/to/song1'
        fake_cursor = StrictMock(Cursor, runtime_attrs=["fetchone"])
        fake_cursor.fetchone = lambda: [(fake_song)]

        self.mock_callable(utils, "db_execute").for_call(
            """
"SELECT song_path \
FROM downloads \
WHERE download_url=? AND accessed=False""",
            (self.fake_download_url,)
        ).to_return_value(fake_cursor).and_assert_called_once()

        with patch.object(pathlib.Path, "exists") as fake_download_db:
            fake_download_db.return_value = True
            self.assertEqual(
                pathlib.Path(fake_song),
                utils.get_download_file(self.fake_download_url)
            )

    def test_get_download_file_not_found(self):
        fake_cursor = StrictMock(Cursor, runtime_attrs=["fetchone"])
        fake_cursor.fetchone = lambda: []

        self.mock_callable(utils, "db_execute").for_call(
            """
"SELECT song_path \
FROM downloads \
WHERE download_url=? AND accessed=False""",
            (self.fake_download_url,)
        ).to_return_value(fake_cursor).and_assert_called_once()

        with patch.object(pathlib.Path, "exists") as fake_download_db:
            fake_download_db.return_value = True
            self.assertIsNone(
                utils.get_download_file(self.fake_download_url)
            )

    def test_get_download_file_exception(self):
        fake_cursor = StrictMock(Cursor, runtime_attrs=["fetchone"])
        fake_cursor.fetchone = lambda: []

        self.mock_callable(utils, "db_execute").for_call(
            """
"SELECT song_path \
FROM downloads \
WHERE download_url=? AND accessed=False""",
            (self.fake_download_url,)
        ).to_raise(FileNotFoundError).and_assert_called_once()

        with patch.object(pathlib.Path, "exists") as fake_download_db:
            fake_download_db.return_value = True
            self.assertIsNone(
                utils.get_download_file(self.fake_download_url)
            )

    def test_remove_download_file_successful(self):
        # tried to use compound with but pylance complained
        with patch.object(pathlib.Path, "exists") as fake_exists:
            with patch.object(
                pathlib.Path, "unlink"
            ) as fake_unlink:
                fake_exists.return_value = True
                fake_unlink.return_value = True
                self.assertIsNone(
                    utils.remove_download_file(self.fake_download_path)
                )
                fake_unlink.assert_called_once()

    def test_remove_download_file_failed(self):
        with patch.object(
            pathlib.Path, "unlink"
        ) as fake_unlink:
            fake_unlink.return_value = True
            self.assertIsNone(
                utils.remove_download_file(None)
            )
            fake_unlink.assert_not_called()

    def test_remove_download_file_not_found(self):
        # tried to use compound with but pylance complained
        with patch.object(pathlib.Path, "exists") as fake_exists:
            with patch.object(
                pathlib.Path, "unlink"
            ) as fake_unlink:
                fake_exists.return_value = True
                fake_unlink.side_effect = FileNotFoundError()
                with self.assertRaises(FileNotFoundError):
                    self.assertIsNone(
                        utils.remove_download_file(self.fake_download_path)
                    )


if __name__ == '__main__':
    unittest.main(verbosity=2)
