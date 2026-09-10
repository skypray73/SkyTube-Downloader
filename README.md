# YouTube Downloader

由 Skypray Huang 製作的 Windows 本機 GUI。支援單支影片與播放清單、解析度選擇、MP3／AAC 音訊，以及精準時間裁切。正式版將 yt-dlp、FFmpeg 與 Deno 封裝在單一 EXE，不需要 Python、Docker、API Key 或外掛資料夾。

> 下載功能需要網路。請只下載你擁有權利或已取得許可的內容，並遵守來源平台條款及所在地法律。

## 功能

- 貼上 YouTube 或 youtu.be HTTPS 連結
- 下載單支影片或完整播放清單
- 選擇 480p、720p、1080p、2160p 或最高畫質
- 下載影片＋最佳音訊、MP3，或保留可用的 AAC／M4A
- 以 HH／MM／SS 數字框設定開始與結束時間
- 填寫時間後自動啟用裁切，全部清空後自動取消
- 預設啟用精準裁切，減少非關鍵影格造成的開頭停格
- 顯示目前串流進度、處理狀態與錯誤訊息
- 可取消下載，並可選用本機瀏覽器 Cookie 或 cookies.txt
- 預設儲存至 EXE 同層的 `download` 資料夾

## 下載 Windows 版

前往 [Releases](../../releases/latest) 下載 `YouTubeDownloader.exe`。這是約 100 MB 的單一執行檔，內含：

- FFmpeg 7.1
- Deno 2.9.6
- yt-dlp 2026.08.19

Windows SmartScreen 可能會對沒有程式碼簽章的新應用顯示警告。可用 Release 附帶的 SHA-256 檔案核對下載內容。

## 使用方式

1. 執行 `YouTubeDownloader.exe`。
2. 貼上影片或播放清單網址。
3. 若要下載整個播放清單，勾選播放清單選項。
4. 選擇解析度與輸出格式。
5. 如需裁切，在開始或結束時間輸入 HH、MM、SS；裁切會自動啟用。
6. 按下「開始下載」。

只填開始時間表示下載到片尾；只填結束時間表示從影片開頭下載。播放清單模式會將同一裁切範圍套用至每部影片。

影片以 MKV 保存，以容納來源提供的最佳影音編碼。最高畫質可能使用 AV1 或 VP9，需要相容播放器。AAC 模式會優先保存來源 AAC／M4A；沒有 AAC 時預設失敗，只有勾選允許轉碼後才將其他音訊重新編碼為 AAC。

## Cookie 與 YouTube 限制

預設不讀取登入資料。若影片需要登入，可明確選擇 Firefox、Chrome、Edge，或 Netscape 格式的 `cookies.txt`。Cookie 只在本機處理；選定的檔案會先複製到暫存目錄，避免 yt-dlp 回寫原檔。

Cookie 不保證能解決 HTTP 403、機器人驗證、PO Token 或區域限制。YouTube 介面與驗證方式會改變，遇到問題時可先更新 yt-dlp 並重新建置。請勿把 cookies.txt 提交至 GitHub 或附加到 Issue。

## 從原始碼執行

需求：Windows 10/11、64 位元 Python 3.12 以上。

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe build.py
.\.venv\Scripts\python.exe app.py
```

第一次執行 `build.py` 會從已安裝的 Python 套件取出 FFmpeg 和 Deno，建立本機 `tools` 目錄，再產生 `dist\YouTubeDownloader.exe`。

## 建置單一 EXE

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1
```

建置結果：

```text
dist\YouTubeDownloader.exe
```

GitHub Actions 也會在 Windows runner 執行測試、建置 EXE、產生 SHA-256，並上傳建置產物。推送 `v*` tag 時會自動建立 GitHub Release。

## 測試

```powershell
.\.venv\Scripts\python.exe -m unittest discover -v
```

測試涵蓋解析度選擇、AAC 回退、時間裁切、播放清單、網址驗證及 Cookie 優先順序。網路下載是否成功仍取決於影片、帳號、網路與平台當時的限制。

## 授權

本專案以 [GPL-3.0-or-later](LICENSE) 發佈。內嵌與建置階段使用的第三方元件請參閱 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

製作人：Skypray Huang  
版本：1.1.0  
最新日期：2026/9/9
