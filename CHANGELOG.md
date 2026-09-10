# Changelog

所有重要變更都記錄在此文件。本專案版本採用 Semantic Versioning。

## [1.1.0] - 2026-09-09

### Added

- Windows 單一 EXE，內嵌 yt-dlp、FFmpeg 與 Deno
- 480p、720p、1080p、2160p 與最高畫質選項
- MP3、原始 AAC／M4A，以及明確允許 AAC 轉碼的選項
- 單支影片與播放清單下載
- HH／MM／SS 裁切數字框與自動啟用裁切
- 下載進度、處理狀態、錯誤訊息與取消功能
- Firefox、Chrome、Edge 與 cookies.txt 選用支援

### Fixed

- 精準裁切預設開啟，減少非關鍵影格造成的開頭停格
- Cookie 檔以暫存副本交給 yt-dlp，避免回寫使用者原檔
