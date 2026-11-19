"""Offline integration: the real yt-dlp engine downloads local test media."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

try:
    import yt_dlp
    from yt_dlp.extractor.common import InfoExtractor
    from yt_dlp.networking import Response
    from yt_dlp.utils import ExtractorError
except ImportError:
    yt_dlp = None
    InfoExtractor = object

from core import MKV_MODE, arguments, output_template


class FixtureIE(InfoExtractor):
    _VALID_URL = r'skytubefixture:(?P<id>[^/]+)'
    media_url = ''

    def _real_extract(self, url):
        video_id = self._match_id(url)
        if video_id in ('playlist', 'partial'):
            ids = ['one', 'missing', 'two'] if video_id == 'partial' else ['one', 'two']
            return self.playlist_result([
                self.url_result('skytubefixture:' + item, ie=FixtureIE.ie_key())
                for item in ids], playlist_id=video_id, playlist_title='測試清單')
        if video_id == 'missing':
            raise ExtractorError('Test unavailable video', expected=True)
        return dict(id=video_id, title='測試 ' + video_id, url=self.media_url,
                    ext='mp4', vcodec='h264', acodec='opus' if video_id == 'opus' else 'aac', height=144)


@unittest.skipIf(yt_dlp is None, 'Install requirements.txt for engine integration tests')
class EngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        bundled = Path(__file__).resolve().parent / 'tools' / 'ffmpeg.exe'
        cls.ffmpeg = str(bundled) if bundled.is_file() else shutil.which('ffmpeg')
        if not cls.ffmpeg:
            raise unittest.SkipTest('Run build.py to prepare FFmpeg or put ffmpeg on PATH')
        cls.temp = tempfile.TemporaryDirectory(prefix='skytube-engine-')
        cls.root = Path(cls.temp.name)
        subprocess.run([cls.ffmpeg, '-v', 'error', '-f', 'lavfi', '-i',
                        'color=c=blue:s=256x144:r=10', '-f', 'lavfi', '-i',
                        'sine=frequency=440', '-t', '0.3', '-c:v', 'libx264',
                        '-c:a', 'aac', str(cls.root / 'sample.mp4')], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        FixtureIE.media_url = (cls.root / 'sample.mp4').as_uri()

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def download(self, fixture, mode=MKV_MODE, extension='mkv', sample=None):
        out = self.root / (fixture + mode)
        url = 'https://www.youtube.com/playlist?list=PLfixture'
        args = arguments(url, '480', mode, '', '', False,
                         str(out), self.ffmpeg, playlist=True)
        args[args.index('-o') + 1] = output_template(url, True, 'fixture')
        params = yt_dlp.parse_options(args).ydl_opts
        params.update(quiet=True, noprogress=True)
        sample = sample or (self.root / 'sample.mp4')
        def local_response(request):
            self.assertEqual(request.url, FixtureIE.media_url)
            return Response(sample.open('rb'), request.url,
                            {'Content-Length': str(sample.stat().st_size)})
        with yt_dlp.YoutubeDL(params, auto_init=False) as engine:
            engine.add_info_extractor(FixtureIE())
            # Replace only transport; extraction, downloads and FFmpeg remain real.
            with patch.object(engine, 'urlopen', side_effect=local_response):
                code = engine.download(['skytubefixture:' + fixture])
        return code, sorted(out.rglob('*.' + extension))

    def test_playlist_downloads_all_entries_and_remuxes(self):
        code, files = self.download('playlist')
        self.assertEqual(code, 0)
        self.assertEqual(len(files), 2)
        self.assertTrue(files[0].name.startswith('001 - '))
        self.assertTrue(files[1].name.startswith('002 - '))
        self.assertTrue(all(path.stat().st_size > 1000 for path in files))

    def test_unavailable_entry_continues_and_reports_failure(self):
        code, files = self.download('partial')
        self.assertNotEqual(code, 0)
        self.assertEqual(len(files), 2)
        self.assertTrue(files[1].name.startswith('003 - '))

    def test_mp4_encodes_requested_video_codec_and_aac(self):
        from video_output import register_mp4_postprocessor

        register_mp4_postprocessor()
        for mode, codec, tag in (
            ('MP4（H.264）', 'h264', 'avc1'),
            ('MP4（H.265）', 'hevc', 'hvc1'),
        ):
            with self.subTest(mode=mode):
                code, files = self.download('playlist', mode, 'mp4')
                self.assertEqual(code, 0)
                self.assertEqual(len(files), 2)
                for path in files:
                    result = subprocess.run(
                        [self.ffmpeg, '-hide_banner', '-i', str(path),
                         '-f', 'null', '-'],
                        capture_output=True, check=True, text=True, errors='replace')
                    self.assertRegex(result.stderr, rf'Video: {codec} .*{tag}')
                    self.assertIn('Audio: aac', result.stderr)
                    self.assertEqual(self.audio_hash(path), self.audio_hash(self.root / 'sample.mp4'))

    def audio_hash(self, path):
        return subprocess.check_output([
            self.ffmpeg, '-v', 'error', '-i', str(path), '-map', '0:a:0',
            '-c:a', 'copy', '-f', 'hash', '-'])

    def test_mp4_transcodes_opus_when_aac_is_unavailable(self):
        from video_output import register_mp4_postprocessor

        register_mp4_postprocessor()
        source = self.root / 'sample-opus.mp4'
        subprocess.run([self.ffmpeg, '-v', 'error', '-i', str(self.root / 'sample.mp4'),
                        '-c:v', 'copy', '-c:a', 'libopus', str(source)], check=True)
        code, files = self.download('opus', 'MP4（H.264）', 'mp4', sample=source)
        self.assertEqual(code, 0)
        self.assertEqual(len(files), 1)
        result = subprocess.run([self.ffmpeg, '-hide_banner', '-i', str(files[0]),
                                 '-f', 'null', '-'],
                                capture_output=True, check=True, text=True, errors='replace')
        self.assertIn('Audio: aac', result.stderr)
