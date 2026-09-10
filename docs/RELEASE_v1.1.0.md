## YouTube Downloader v1.1.0

第一個公開 Windows 版本。單一 EXE 已內嵌 yt-dlp、FFmpeg 與 Deno，不需要另外安裝 Python 或外掛工具。

### 功能

- 單支影片與播放清單下載
- 480p、720p、1080p、2160p、最高畫質
- 影片＋最佳音訊、MP3、原始 AAC／M4A
- HH／MM／SS 時間裁切；輸入時間後自動啟用
- 精準裁切預設開啟，減少開頭停格
- 下載進度、錯誤訊息與取消下載
- 選用 Firefox、Chrome、Edge 或 cookies.txt
- 預設輸出至 EXE 同層 `download` 資料夾

### 下載

一般使用者下載 `YouTubeDownloader.exe` 即可。也可下載 `YouTubeDownloader-Windows.zip`，其中包含 EXE、SHA-256、README 與授權文件。

Windows SmartScreen 可能因程式尚未簽署而顯示警告。請從本專案 Release 下載並核對 SHA-256。

### 已知限制

- YouTube 的 403、機器人驗證、PO Token、地區或帳號限制不一定能以 Cookie 解決。
- 精準裁切需要重新編碼，速度較慢且可能輕微影響畫質。
- 單一 EXE 啟動時需解壓內嵌元件至暫存區，首次啟動可能需要數秒。
- 最高畫質影片可能使用 AV1／VP9，需要相容播放器。

請只下載你有權使用的內容。回報問題時不要附加 Cookie、Token 或私人影片資訊。
