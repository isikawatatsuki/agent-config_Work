import http.client
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).parents[1]))
from library import Library
from server import ExplorerServer, instance_identity, matching_server, serve


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.library = Library(self.root / "artifacts", self.root / "state/index.sqlite")
        (self.library.root / "test.html").write_text("<script>fetch('/api/library')</script><p>Sample</p>")
        self.library.scan()
        self.server = ExplorerServer(("127.0.0.1", 0), self.library)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.library.close()
        self.temporary.cleanup()

    def request(self, method, path, data=None, headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port)
        connection.request(method, path, json.dumps(data) if data is not None else None, headers or {})
        response = connection.getresponse()
        result = response.status, dict(response.getheaders()), response.read()
        connection.close()
        return result

    def test_read_and_sandbox_preview(self):
        status, _, body = self.request("GET", "/api/library")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)['stats']['html'], 1)
        status, headers, _ = self.request("GET", "/content/test.html")
        self.assertEqual(status, 200)
        self.assertIn("sandbox allow-scripts", headers['Content-Security-Policy'])
        self.assertIn("connect-src 'none'", headers['Content-Security-Policy'])
        self.assertNotIn("allow-same-origin", headers['Content-Security-Policy'])

    def test_csrf_and_host_protection(self):
        for headers in ({}, {"Host": "evil.example"}, {"X-Artifact-Token": self.server.token, "Origin": "https://evil.example"}):
            self.assertEqual(self.request("POST", "/api/folder", {"parent": "", "name": "unsafe"}, headers)[0], 403)
        self.assertFalse((self.library.root / "unsafe").exists())
        self.assertEqual(self.request("GET", "/api/bootstrap", headers={"Host": "evil.example"})[0], 403)

    def test_separate_library_and_viewer_pages(self):
        status, _, body = self.request("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn(b'id="document-list"', body)
        self.assertNotIn(b'id="preview-pane"', body)
        self.assertNotIn(b'<iframe', body)
        status, headers, body = self.request("GET", "/viewer.html?id=1")
        self.assertEqual(status, 200)
        self.assertIn(b'id="file-stage"', body)
        self.assertNotIn(b'id="document-list"', body)
        self.assertIn("blob:", headers['Content-Security-Policy'])
        for path in ("/viewer.js", "/viewer.css"):
            self.assertEqual(self.request("GET", path)[0], 200)

    def test_authorized_folder_and_invalid_paths(self):
        headers = {"Content-Type": "application/json", "X-Artifact-Token": self.server.token}
        self.assertEqual(self.request("POST", "/api/folder", {"parent": "", "name": "new"}, headers)[0], 200)
        self.assertTrue((self.library.root / "new").exists())
        self.assertEqual(self.request("POST", "/api/folder", {"parent": "../", "name": "outside"}, headers)[0], 400)
        self.assertEqual(self.request("GET", "/content/%2E%2E/state/index.sqlite")[0], 400)
        self.assertEqual(self.request("GET", "/content/test.py")[0], 404)

    def test_reuse_only_matching_instance_without_opening_database(self):
        identity = instance_identity(self.library.root, self.root / "state")
        self.server.identity = identity
        self.assertTrue(matching_server(self.server.server_port, identity))
        self.assertFalse(matching_server(self.server.server_port, "another-workspace"))
        with patch("server.Library") as factory:
            self.assertEqual(serve(self.library.root, self.root / "state", self.server.server_port, True), 0)
            self.assertEqual(serve(self.library.root, self.root / "other-state", self.server.server_port, True), 1)
            factory.assert_not_called()
        status, _, body = self.request("GET", "/api/health", headers={"Host": "evil.example"})
        self.assertEqual(status, 403)
        self.assertNotIn(self.server.token.encode(), body)

    def test_delete_and_restore_api(self):
        headers = {"Content-Type": "application/json", "X-Artifact-Token": self.server.token}
        self.assertEqual(self.request("POST", "/api/delete", {"source": "test.html"}, headers)[0], 200)
        self.assertEqual(json.loads(self.request("GET", "/api/library")[2])['items'], [])
        status, _, body = self.request("GET", "/api/trash")
        self.assertEqual(status, 200)
        identity = json.loads(body)['items'][0]['id']
        self.assertNotIn(b'"records"', body)
        self.assertEqual(self.request("GET", f"/content/.trash/{identity}/payload")[0], 400)
        self.assertEqual(self.request("GET", f"/api/download?path=.trash/{identity}/manifest.json")[0], 400)
        self.assertEqual(self.request("POST", "/api/restore", {"id": identity}, headers)[0], 200)
        self.assertTrue((self.library.root / "test.html").exists())
        self.assertEqual(json.loads(self.request("GET", "/api/trash")[2])['items'], [])
        self.assertEqual(self.request("POST", "/api/delete", {"source": ""}, headers)[0], 400)
        self.assertEqual(self.request("POST", "/api/restore", {"id": "../outside"}, headers)[0], 400)

    def test_delete_restore_csrf_and_origin_protection(self):
        for path, data in (("/api/delete", {"source": "test.html"}), ("/api/restore", {"id": "0" * 32})):
            for headers in ({}, {"X-Artifact-Token": self.server.token, "Host": "evil.example"}, {"X-Artifact-Token": self.server.token, "Origin": "https://evil.example"}):
                with self.subTest(path=path, headers=list(headers)):
                    self.assertEqual(self.request("POST", path, data, headers)[0], 403)
        self.assertTrue((self.library.root / "test.html").exists())

    def test_unavailable_or_unrelated_health_endpoint_is_not_reused(self):
        with patch("server.http.client.HTTPConnection") as factory:
            response = factory.return_value.getresponse.return_value
            response.status = 200
            response.read.return_value = b'{"app":"other-app"}'
            self.assertFalse(matching_server(8765, "expected"))
            response.read.return_value = b'not json'
            self.assertFalse(matching_server(8765, "expected"))
            response.read.side_effect = TimeoutError
            self.assertFalse(matching_server(8765, "expected"))

    def test_windows_exclusive_bind(self):
        server = object.__new__(ExplorerServer)
        server.socket = Mock()
        with patch("server.os.name", "nt"), patch("server.socket.SO_EXCLUSIVEADDRUSE", -5, create=True), patch("server.ThreadingHTTPServer.server_bind") as bind:
            server.server_bind()
            self.assertFalse(server.allow_reuse_address)
            server.socket.setsockopt.assert_called_once()
            self.assertEqual(server.socket.setsockopt.call_args.args[1:], (-5, 1))
            bind.assert_called_once()


if __name__ == "__main__":
    unittest.main()