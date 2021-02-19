#!/usr/bin/python3

import testslide
import unittest
import lib.utils as utils
from pathlib import Path
from testslide import StrictMock
import server
from werkzeug.wrappers import Response


class TestServer(testslide.TestCase):

    def __init__(self, *args, **kwargs):
        super(testslide.TestCase, self).__init__(*args, **kwargs)
        self.fake_token = "fakehask"
        self.not_found_token = "ThisHashDoesntExist"
        self.file_name = "file.mp3"

    def setUp(self) -> None:
        server.app.config['TESTING'] = True
        server.app.config['WTF_CSRF_ENABLED'] = False
        server.app.config['DEBUG'] = False
        self.app = server.app.test_client()
        self.assertEqual(server.app.debug, False)
        super().setUp()
        StrictMock._SETTABLE_MAGICS.append("__fspath__")

    def _get_fake_path(self, file_name):
        fake_path = StrictMock(
            Path, runtime_attrs=["name"]
        )
        fake_path.name = file_name
        return fake_path

    def _mock_get_download_file(self, token, fake_path):
        self.mock_callable(
            utils, "get_download_file"
        ).for_call(
            token
        ).to_return_value(fake_path).and_assert_called_once()

    def _mock_disable_download(self, fake_token):
        self.mock_callable(
            utils, "disable_download"
        ).for_call(
            fake_token
        ).to_return_value(None).and_assert_called_once()

    def _mock_remove_download_file(self, fake_path, response):
        self.mock_callable(
            utils, "remove_download_file"
        ).for_call(
            fake_path
        ).to_return_value(response).and_assert_called_once()

    def _mock_send_file(
            self,
            fake_path,
            as_attachment=True,
            attachment_filename=None,
            mimetype='application/zip',
            response=None
    ):
        self.mock_callable(
            server, "send_file"
        ).for_call(
            fake_path,
            as_attachment=as_attachment,
            attachment_filename=attachment_filename,
            mimetype=mimetype,
        ).to_return_value(response).and_assert_called_once()

    def test_gen_download_ok(self):
        fake_path = self._get_fake_path(self.file_name)
        self._mock_get_download_file(self.fake_token, fake_path)
        self._mock_disable_download(self.fake_token)
        self._mock_remove_download_file(fake_path, Response("File removed!"))
        self._mock_send_file(
            fake_path,
            as_attachment=True,
            attachment_filename=self.file_name,
            mimetype='application/zip',
            response=Response("Yes!")
        )

        response = self.app.get(
            f"/download/{self.fake_token}", follow_redirects=True
        )
        self.assertEqual(response.status_code, 200)

    def test_gen_download_hash_not_found(self):
        self._mock_get_download_file(self.not_found_token, None)

        self.mock_callable(
            utils, "disable_download"
        ).and_assert_not_called()

        self.mock_callable(
            utils, "remove_download_file"
        ).and_assert_not_called()

        self.mock_callable(
            server, "send_file"
        ).and_assert_not_called()

        response = self.app.get(
            f"/download/{self.not_found_token}", follow_redirects=True
        )
        self.assertEqual(response.status_code, 404)

    def test_gen_download_internal_error(self):
        fake_path = self._get_fake_path(self.file_name)
        self._mock_get_download_file(self.fake_token, fake_path)

        self._mock_disable_download(self.fake_token)

        self.mock_callable(
            server, "send_file"
        ).for_call(
            fake_path,
            as_attachment=True,
            attachment_filename=self.file_name,
            mimetype='application/zip',
        ).to_raise(Exception).and_assert_called_once()

        self.mock_callable(
            utils, "remove_download_file"
        ).and_assert_not_called()

        response = self.app.get(
            f"/download/{self.fake_token}", follow_redirects=True
        )
        self.assertEqual(response.status_code, 500)

    def test_gen_download_disable_download_failure(self):
        fake_path = self._get_fake_path(self.file_name)
        self._mock_get_download_file(self.fake_token, fake_path)

        self.mock_callable(
            utils, "disable_download"
        ).for_call(
            self.fake_token
        ).to_raise(Exception).and_assert_called_once()

        self.mock_callable(
            server, "send_file"
        ).and_assert_not_called()

        self.mock_callable(
            utils, "remove_download_file"
        ).and_assert_not_called()

        response = self.app.get(
            f"/download/{self.fake_token}", follow_redirects=True
        )
        self.assertEqual(response.status_code, 500)

    def test_gen_download_remove_download_failure(self):
        fake_path = self._get_fake_path(self.file_name)
        self._mock_get_download_file(self.fake_token, fake_path)
        self._mock_disable_download(self.fake_token)

        self._mock_send_file(
            fake_path,
            as_attachment=True,
            attachment_filename=self.file_name,
            mimetype='application/zip',
            response=Response("Yes!")
        )

        self.mock_callable(
            utils, "remove_download_file"
        ).to_raise(Exception).and_assert_called()

        response = self.app.get(
            f"/download/{self.fake_token}", follow_redirects=True
        )
        # no need to fail the user request due internal error
        # while removing a file.
        self.assertEqual(response.status_code, 200)


if __name__ == '__main__':
    unittest.main(verbosity=2)
