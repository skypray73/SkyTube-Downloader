"""MP4 conversion within yt-dlp's per-video postprocessing pipeline."""
from pathlib import Path

from yt_dlp.globals import postprocessors
from yt_dlp.postprocessor.ffmpeg import FFmpegPostProcessor
from yt_dlp.utils import PostProcessingError


class SkyTubeMP4PP(FFmpegPostProcessor):
    def __init__(self, downloader, encoder):
        super().__init__(downloader)
        self.encoder = encoder

    def run(self, info):
        source = Path(info['filepath'])
        output = source.with_suffix('.mp4')
        temporary = output.with_suffix('.converting.mp4')
        codec = 'H.265' if self.encoder == 'libx265' else 'H.264'
        self.to_screen(f'正在轉碼 MP4（{codec}）：{output.name}', quiet=False)
        audio_codec = self.get_audio_codec(str(source))
        audio_options = ['-c:a', 'copy'] if audio_codec == 'aac' else ['-c:a', 'aac', '-b:a', '192k']
        options = [
            '-map', '0:v:0', '-map', '0:a:0?',
            '-c:v', self.encoder, '-preset', 'fast',
            '-crf', '24' if self.encoder == 'libx265' else '20',
            '-pix_fmt', 'yuv420p', *audio_options,
            '-movflags', '+faststart',
        ]
        if self.encoder == 'libx265':
            options += ['-tag:v', 'hvc1']
        if source != output and output.exists():
            raise PostProcessingError(f'MP4 檔案已存在：{output}')
        try:
            self.run_ffmpeg(str(source), str(temporary), options)
            temporary.replace(output)
        except OSError as exc:
            raise PostProcessingError(f'無法儲存 MP4：{exc}') from exc
        finally:
            temporary.unlink(missing_ok=True)
        info.update(filepath=str(output), ext='mp4', format='mp4')
        return ([] if source == output else [str(source)]), info


def register_mp4_postprocessor():
    postprocessors.value['SkyTubeMP4PP'] = SkyTubeMP4PP
