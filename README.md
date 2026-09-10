# SkyTube Downloader

由 Skypray Huang 製作的 Windows 本機 YouTube 下載 GUI，使用 yt-dlp、FFmpeg 與 Deno。

> YouTube 是 Google LLC 的商標。本專案與 YouTube 無關，也未獲其背書。

## 功能

- 影片與播放清單下載
- 480p、720p、1080p、2160p 或最高畫質
- 影片＋最佳音訊、MP3、來源 AAC／M4A
- HH／MM／SS 開始與結束時間裁切
- 填寫時間後自動啟用裁切，預設精準裁切以減少開頭停格
- 下載進度、錯誤訊息與本機 Cookie 選項
- 單一 EXE 內含 FFmpeg 7.1、Deno 2.9.6、yt-dlp 2026.08.19

## 下載

前往 Releases 下載 SkyTubeDownloader.exe。預設會將檔案儲存到 EXE 同層的 download 資料夾。

## 使用

1. 執行 SkyTubeDownloader.exe。
2. 貼上 YouTube 影片或播放清單網址。
3. 選擇畫質、輸出格式；需要裁切時輸入開始／結束 HH、MM、SS。
4. 按「開始下載」。

下載功能需要網路。請只下載你擁有權利或已取得許可的內容，並遵守平台條款及所在地法律。Cookie 不應提交到 GitHub。

## 建置

需求：Windows 10/11、64 位元 Python 3.12+。執行 build.py 可產生 dist\SkyTubeDownloader.exe；FFmpeg、Deno、yt-dlp 與授權文件會嵌入 EXE。

## 授權

GPL-3.0-or-later。第三方元件請參閱 THIRD_PARTY_NOTICES.md。

版本：1.2.0 · 最新日期：2026/9/10
