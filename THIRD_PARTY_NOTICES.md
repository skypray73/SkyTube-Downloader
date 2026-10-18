# Third-party notices

Portable 版將 FFmpeg、Deno 獨立存放於 tools，Python 與 yt-dlp 依賴存放於 _internal，和主程式一起壓成 ZIP。它們不是本專案作者自行開發的元件。

## FFmpeg

- 封裝版本：FFmpeg 7.1 essentials build
- 二進位來源：`imageio-ffmpeg==0.6.0` Windows wheel，其 FFmpeg build 來源標示為 gyan.dev
- 專案：https://ffmpeg.org/
- Windows build：https://www.gyan.dev/ffmpeg/builds/
- 授權：此 build 啟用 GPLv3 元件；GPLv3 完整文字見專案根目錄 `LICENSE`

散布含 FFmpeg 的二進位 Release 時，維護者應確認並提供該 build 對應的完整來源或有效書面提供方式。這包含 FFmpeg、使用的建置腳本與適用的 GPL 相依元件。授權義務應以實際 Release 內的 build 為準。

## Deno

- 封裝版本：2.9.6
- Python redistribution：`deno==2.9.6`
- 專案：https://deno.com/
- 原始碼：https://github.com/denoland/deno
- 授權：MIT，文字見 `licenses/Deno-LICENSE.txt`

## yt-dlp

- 封裝版本：2026.08.19
- 專案：https://github.com/yt-dlp/yt-dlp
- 授權：The Unlicense

## imageio-ffmpeg

- 封裝版本：0.6.0
- 專案：https://github.com/imageio/imageio-ffmpeg
- 授權：BSD-2-Clause，文字見 `licenses/imageio-ffmpeg-LICENSE.txt`

## PyInstaller

- 建置版本：6.22.2
- 專案：https://pyinstaller.org/
- 用途：建立 Windows onedir 資料夾式可攜程式

每次建置會在 `tools/VERSIONS.txt` 記錄實際工具版本，並將版本與授權資料放入 Portable ZIP 的 tools 目錄。
