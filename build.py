from pathlib import Path
import importlib.metadata
import shutil
import subprocess
import PyInstaller.__main__
from tk_runtime import prepare_tk


def prepare_tools(root):
    """Copy the pip-provided Windows runtimes into the distributable folder."""
    import deno
    import imageio_ffmpeg

    tools = root / 'tools'
    licenses = tools / 'licenses'
    licenses.mkdir(parents=True, exist_ok=True)
    shutil.copy2(imageio_ffmpeg.get_ffmpeg_exe(), tools / 'ffmpeg.exe')
    shutil.copy2(deno.find_deno_bin(), tools / 'deno.exe')

    for package, target in (
        ('imageio-ffmpeg', 'imageio-ffmpeg-LICENSE.txt'),
        ('deno', 'Deno-LICENSE.txt'),
    ):
        dist = importlib.metadata.distribution(package)
        license_files = [path for path in (dist.files or [])
                         if Path(str(path)).name.upper() == 'LICENSE']
        if license_files:
            shutil.copy2(dist.locate_file(license_files[0]), licenses / target)

    # The bundled imageio-ffmpeg Windows binary is a GPLv3 FFmpeg build.
    gpl = licenses / 'FFmpeg-GPLv3.txt'
    shutil.copy2(root / 'LICENSE', gpl)

    versions = [
        subprocess.check_output([tools / 'ffmpeg.exe', '-version'], text=True,
                                encoding='utf-8', errors='replace').splitlines()[0],
        subprocess.check_output([tools / 'deno.exe', '--version'], text=True,
                                encoding='utf-8', errors='replace').splitlines()[0],
        'Deno Python redistribution: ' + importlib.metadata.version('deno'),
        'imageio-ffmpeg: ' + importlib.metadata.version('imageio-ffmpeg'),
    ]
    (tools / 'VERSIONS.txt').write_text('\n'.join(versions) + '\n', encoding='utf-8')


if __name__ == '__main__':
    prepare_tk()
    root = Path(__file__).resolve().parent
    prepare_tools(root)
    PyInstaller.__main__.run([
        '--noconfirm', '--clean', '--onefile', '--windowed',
        '--name', 'YouTubeDownloader', '--collect-all', 'yt_dlp',
        '--collect-all', 'yt_dlp_ejs',
        '--add-binary', str(root / 'tools' / 'ffmpeg.exe') + ';tools',
        '--add-binary', str(root / 'tools' / 'deno.exe') + ';tools',
        '--add-data', str(root / 'tools' / 'licenses') + ';tools/licenses',
        '--add-data', str(root / 'tools' / 'VERSIONS.txt') + ';tools',
        '--version-file', str(root / 'version_info.txt'),
        '--distpath', str(root / 'dist'),
        '--workpath', str(root / 'build'), '--specpath', str(root / 'build'),
        str(root / 'app.py'),
    ])
    print('Ready:', root / 'dist' / 'YouTubeDownloader.exe')
