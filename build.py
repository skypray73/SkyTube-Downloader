from pathlib import Path
import importlib.metadata
import hashlib
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
        '--noconfirm', '--clean', '--onedir', '--windowed',
        '--name', 'SkyTubeDownloader', '--collect-all', 'yt_dlp',
        '--collect-all', 'yt_dlp_ejs',
        '--version-file', str(root / 'version_info.txt'),
        '--distpath', str(root / 'dist'),
        '--workpath', str(root / 'build'), '--specpath', str(root / 'build'),
        str(root / 'app.py'),
    ])
    portable = root / 'dist' / 'SkyTubeDownloader'
    # Keep large tools outside both the EXE and PyInstaller's runtime folder.
    shutil.copytree(root / 'tools', portable / 'tools', dirs_exist_ok=True)
    for name in ('README.md', 'LICENSE', 'COPYRIGHT', 'THIRD_PARTY_NOTICES.md'):
        shutil.copy2(root / name, portable / name)
    shutil.copytree(root / 'licenses', portable / 'licenses', dirs_exist_ok=True)
    (portable / '使用說明.txt').write_text(
        '請先完整解壓縮 ZIP，再執行 SkyTubeDownloader.exe。\n'
        '請保留同層的 _internal、tools 和授權文件；不要只複製主程式 EXE。\n',
        encoding='utf-8')
    archive = Path(shutil.make_archive(str(root / 'dist' / 'SkyTubeDownloader-Portable'),
                                      'zip', root / 'dist', portable.name))
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    archive.with_suffix('.zip.sha256').write_text(
        digest + '  ' + archive.name + '\n', encoding='ascii')
    print('Ready:', archive)
