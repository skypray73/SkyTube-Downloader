import unittest
from core import arguments, seconds, parse_urls, output_template

class SelectionTests(unittest.TestCase):
    def args(self, **kw):
        data = dict(url='https://www.youtube.com/watch?v=test', quality='1080',
            mode='影片＋最佳音訊', start='', end='', precise=False, output='out', ffmpeg='tools')
        data.update(kw)
        return arguments(**data)

    def test_caps(self):
        for quality in ('480', '720', '1080', '2160'):
            args = self.args(quality=quality)
            self.assertEqual(args[args.index('-f') + 1], f'bv[height<={quality}]+ba/b[height<={quality}]')
        self.assertIn('bv+ba/b', self.args(quality='最高畫質'))

    def test_audio(self):
        self.assertIn('mp3', self.args(mode='MP3 音訊'))
        strict = self.args(mode='原始 AAC / M4A')
        self.assertEqual(strict[strict.index('-f') + 1], 'ba[acodec^=mp4a]/ba[acodec=aac]')
        fallback = self.args(mode='原始 AAC / M4A', aac_fallback=True)
        self.assertTrue(fallback[fallback.index('-f') + 1].endswith('/ba'))

    def test_time(self):
        self.assertEqual(seconds('01:12:45'), 4365)
        self.assertIn('*330-4365', self.args(start='00:05:30', end='01:12:45'))
        self.assertIn('--force-keyframes-at-cuts', self.args(start='00:00:01', precise=True))
        self.assertIn('*30-inf', self.args(start='00:00:30'))
        for value in ('1:99:00', '-1:00:00', 'abc'):
            with self.assertRaises(ValueError): seconds(value)
        with self.assertRaises(ValueError): self.args(start='00:01:00', end='00:00:30')

    def test_url_and_cookie(self):
        for url in ('https://youtube.com.evil.test/a', 'file:///secret', 'http://youtu.be/a'):
            with self.assertRaises(ValueError): self.args(url=url)
        args = self.args(cookie='private.txt', browser='chrome')
        self.assertIn('--cookies', args)
        self.assertNotIn('--cookies-from-browser', args)
        self.assertEqual(args[-2], '--')

    def test_playlist(self):
        self.assertIn('--no-playlist', self.args())
        args = self.args(playlist=True)
        self.assertIn('--yes-playlist', args)
        self.assertNotIn('--no-playlist', args)

    def test_multiple_urls(self):
        a = 'https://youtu.be/one'
        b = 'https://www.youtube.com/playlist?list=PLtest'
        self.assertEqual(parse_urls(f'  {a}\r\n\n{b}\t{a}  '), [a, b])
        for text in ('', ' \n ', a + '\nhttps://evil.test/watch'):
            with self.assertRaises(ValueError):
                parse_urls(text)
        with self.assertRaisesRegex(ValueError, '第 2 個'):
            parse_urls(a + '\n--exec=bad')

    def test_playlist_only_requires_enabled_option(self):
        url = 'https://www.youtube.com/playlist?list=PLtest'
        with self.assertRaisesRegex(ValueError, '勾選'):
            self.args(url=url)
        args = self.args(url=url, playlist=True)
        self.assertIn('--no-abort-on-error', args)
        self.assertNotIn('--ignore-errors', args)
        self.assertIn('--no-simulate', args)
        self.assertEqual(args[-2:], ['--', url])

    def test_mixed_output_paths(self):
        single = 'https://youtu.be/test'
        playlist = 'https://www.youtube.com/watch?v=test&list=PLtest'
        for enabled in (True, False):
            self.assertNotIn('/', output_template(single, enabled, 'unique'))
        self.assertNotIn('/', output_template(playlist, False, 'unique'))
        grouped = output_template(playlist, True, 'unique')
        self.assertIn('%(playlist_index)03d', grouped)
        self.assertIn('playlist_id', grouped)
        self.assertIn('unique', grouped)

    def test_single_argument_rejects_accidental_multiple_urls(self):
        with self.assertRaises(ValueError):
            self.args(url='https://youtu.be/one https://youtu.be/two')

if __name__ == '__main__':
    unittest.main()
