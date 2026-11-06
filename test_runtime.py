from pathlib import Path
import ssl
import tempfile
from types import SimpleNamespace
import unittest

from runtime_support import check_ssl_runtime, ssl_data_files


class RuntimeTests(unittest.TestCase):
    def test_verified_tls_context_loads_certificates(self):
        self.assertGreater(check_ssl_runtime(), 0)

    def test_bundles_custom_python_ssl_resource(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / 'ssl.py'
            source.write_text("load('codex-rejected-cas.pem')", encoding='utf-8')
            resource = source.with_name('codex-rejected-cas.pem')
            resource.write_text('fixture', encoding='ascii')
            self.assertEqual(ssl_data_files(SimpleNamespace(__file__=str(source))),
                             [(str(resource), '.')])

    def test_missing_required_resource_fails_build(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / 'ssl.py'
            source.write_text("load('codex-rejected-cas.pem')", encoding='utf-8')
            with self.assertRaisesRegex(RuntimeError, 'missing'):
                ssl_data_files(SimpleNamespace(__file__=str(source)))

    def test_standard_python_needs_no_extra_resource(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / 'ssl.py'
            source.write_text('class SSLContext: pass', encoding='utf-8')
            self.assertEqual(ssl_data_files(SimpleNamespace(__file__=str(source))), [])

    @unittest.skipUnless((Path(__file__).parent / 'dist' / 'SkyTubeDownloader' /
                         'SkyTubeDownloader.exe').is_file(), 'Build the Portable app first')
    def test_packaged_executable_initializes_verified_tls(self):
        from build import verify_packaged_runtime
        verify_packaged_runtime(Path(__file__).parent / 'dist' / 'SkyTubeDownloader')
