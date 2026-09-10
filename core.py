"""Pure command construction, shared by GUI and tests."""
import re
from urllib.parse import urlsplit


def seconds(value):
    if not re.fullmatch(r"\d{1,4}:[0-5]\d:[0-5]\d", value):
        raise ValueError("時間格式必須是 HH:MM:SS，例如 00:05:30")
    h, m, s = map(int, value.split(':'))
    return h * 3600 + m * 60 + s


def arguments(url, quality, mode, start, end, precise, output, ffmpeg,
              cookie='', browser='', aac_fallback=False, deno='', playlist=False):
    parsed = urlsplit(url.strip())
    host = (parsed.hostname or '').lower()
    if parsed.scheme != 'https' or host not in ('youtube.com', 'www.youtube.com',
            'm.youtube.com', 'music.youtube.com', 'youtu.be') or parsed.username:
        raise ValueError('請輸入 https://www.youtube.com 或 https://youtu.be 影片連結')
    if quality not in ('480', '720', '1080', '2160', '最高畫質'):
        raise ValueError('不支援的畫質')
    if mode not in ('影片＋最佳音訊', 'MP3 音訊', '原始 AAC / M4A'):
        raise ValueError('不支援的輸出模式')
    args = ['--ignore-config', '--yes-playlist' if playlist else '--no-playlist',
            '--newline', '--no-color',
            '--encoding', 'utf-8', '--no-overwrites', '--windows-filenames',
            '--socket-timeout', '25', '--retries', '3', '--fragment-retries', '3',
            '--ffmpeg-location', ffmpeg, '-P', output,
            '-o', '%(title).120B [%(id)s].%(ext)s',
            '--progress-template', 'download:PROGRESS:%(progress._percent_str)s',
            '--print', 'after_move:FILE:%(filepath)s']
    if deno:
        args += ['--js-runtimes', 'deno:' + deno]
    if cookie:
        args += ['--cookies', cookie]
    elif browser:
        args += ['--cookies-from-browser', browser]
    if mode == '影片＋最佳音訊':
        cap = '' if quality == '最高畫質' else '[height<=' + quality + ']'
        args += ['-f', f'bv{cap}+ba/b{cap}', '--merge-output-format', 'mkv',
                 '--remux-video', 'mkv']
    elif mode == 'MP3 音訊':
        args += ['-f', 'ba', '-x', '--audio-format', 'mp3', '--audio-quality', '0']
    else:
        fmt = 'ba[acodec^=mp4a]/ba[acodec=aac]'
        if aac_fallback:
            fmt += '/ba'
        args += ['-f', fmt, '-x', '--audio-format', 'm4a']
    if start or end:
        begin = seconds(start) if start else 0
        finish = seconds(end) if end else None
        if finish is not None and finish <= begin:
            raise ValueError('結束時間必須大於開始時間')
        args += ['--download-sections', f'*{begin}-{finish if finish is not None else "inf"}']
        if precise:
            args += ['--force-keyframes-at-cuts']
    return args + ['--', url.strip()]
