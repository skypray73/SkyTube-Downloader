from pathlib import Path
import importlib.metadata
import hashlib
import shutil
import subprocess
import tempfile
from urllib.request import urlopen
from zipfile import ZipFile
import PyInstaller.__main__
from tk_runtime import prepare_tk
from runtime_support import ssl_data_files


FFMPEG_VERSION = '9.0.2'
FFMPEG_ARCHIVE = f'ffmpeg-{FFMPEG_VERSION}-essentials_build.zip'
FFMPEG_URL = f'https://github.com/GyanD/codexffmpeg/releases/download/{FFMPEG_VERSION}/{FFMPEG_ARCHIVE}'
FFMPEG_SHA256 = '60f467265b1e312373dbcd92200c2618a74850f98d3d078e94296bb3fa2047ba'


def sha256(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def prepare_ffmpeg(root, tools, licenses):
    cache = root / 'build' / 'ffmpeg'
    cache.mkdir(parents=True, exist_ok=True)
    archive = cache / FFMPEG_ARCHIVE
    if not archive.exists() or sha256(archive) != FFMPEG_SHA256:
        with tempfile.TemporaryDirectory(dir=cache) as temp:
            download = Path(temp) / FFMPEG_ARCHIVE
            with urlopen(FFMPEG_URL, timeout=60) as response, download.open('wb') as target:
                shutil.copyfileobj(response, target)
            if sha256(download) != FFMPEG_SHA256:
                raise RuntimeError('FFmpeg archive SHA-256 did not match the pinned release')
            download.replace(archive)

    prefix = f'ffmpeg-{FFMPEG_VERSION}-essentials_build'
    with ZipFile(archive) as release:
        for member, target in (
            (f'{prefix}/bin/ffmpeg.exe', tools / 'ffmpeg.exe'),
            (f'{prefix}/LICENSE', licenses / 'FFmpeg-GPLv3.txt'),
        ):
            with release.open(member) as source, target.open('wb') as output:
                shutil.copyfileobj(source, output)


def verify_packaged_runtime(portable):
    """Fail the build if the shipped executable cannot initialize verified TLS."""
    with tempfile.TemporaryDirectory(prefix='skytube-runtime-') as temp:
        log = Path(temp) / 'runtime.log'
        result = subprocess.run([
            str(portable / 'SkyTubeDownloader.exe'), '--worker', str(log),
            '--check-runtime'], timeout=60, capture_output=True)
        message = log.read_text(encoding='utf-8') if log.exists() else ''
        if result.returncode or 'RUNTIME_OK:' not in message:
            raise RuntimeError('Packaged HTTPS runtime check failed:\n' + message)
        print(message.strip())


def prepare_tools(root):
    """Prepare the external Windows tools for the distributable folder."""
    import deno

    tools = root / 'tools'
    licenses = tools / 'licenses'
    licenses.mkdir(parents=True, exist_ok=True)
    prepare_ffmpeg(root, tools, licenses)
    shutil.copy2(deno.find_deno_bin(), tools / 'deno.exe')

    dist = importlib.metadata.distribution('deno')
    license_file = next((path for path in dist.files or []
                         if Path(str(path)).name.upper() == 'LICENSE'), None)
    if license_file:
        shutil.copy2(dist.locate_file(license_file), licenses / 'Deno-LICENSE.txt')

    versions = [
        subprocess.check_output([tools / 'ffmpeg.exe', '-version'], text=True,
                                encoding='utf-8', errors='replace').splitlines()[0],
        subprocess.check_output([tools / 'deno.exe', '--version'], text=True,
                                encoding='utf-8', errors='replace').splitlines()[0],
        'Deno Python redistribution: ' + importlib.metadata.version('deno'),
        'yt-dlp: ' + importlib.metadata.version('yt-dlp'),
    ]
    (tools / 'VERSIONS.txt').write_text('\n'.join(versions) + '\n', encoding='utf-8')


if __name__ == '__main__':
    prepare_tk()
    root = Path(__file__).resolve().parent
    prepare_tools(root)
    icon = root / 'assets' / 'skytube-icon.ico'
    data_args = ['--add-data', f'{icon}:assets',
                 '--add-data', f"{icon.with_suffix('.png')}:assets"]
    for source, destination in ssl_data_files():
        data_args += ['--add-data', source + ':' + destination]
    PyInstaller.__main__.run([
        '--noconfirm', '--clean', '--onedir', '--windowed',
        '--name', 'SkyTubeDownloader', '--collect-all', 'yt_dlp',
        '--collect-all', 'yt_dlp_ejs',
        '--icon', str(icon),
        '--version-file', str(root / 'version_info.txt'),
        '--distpath', str(root / 'dist'),
        '--workpath', str(root / 'build'), '--specpath', str(root / 'build'),
        *data_args, str(root / 'app.py'),
    ])
    portable = root / 'dist' / 'SkyTubeDownloader'
    verify_packaged_runtime(portable)
    # Keep large tools outside both the EXE and PyInstaller's runtime folder.
    shutil.copytree(root / 'tools', portable / 'tools', dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns('imageio-ffmpeg-LICENSE.txt'))
    for name in ('README.md', 'LICENSE', 'COPYRIGHT', 'THIRD_PARTY_NOTICES.md'):
        shutil.copy2(root / name, portable / name)
    (portable / 'assets').mkdir(exist_ok=True)
    shutil.copy2(icon.with_suffix('.svg'), portable / 'assets')
    shutil.copytree(root / 'licenses', portable / 'licenses', dirs_exist_ok=True)
    (portable / '使用說明.txt').write_text(
        '請先完整解壓縮 ZIP，再執行 SkyTubeDownloader.exe。\n'
        '請保留同層的 _internal、tools 和授權文件；不要只複製主程式 EXE。\n',
        encoding='utf-8')
    archive = Path(shutil.make_archive(str(root / 'dist' / 'SkyTubeDownloader-Portable'),
                                      'zip', root / 'dist', portable.name))
    digest = sha256(archive)
    archive.with_suffix('.zip.sha256').write_text(
        digest + '  ' + archive.name + '\n', encoding='ascii')
    print('Ready:', archive)
