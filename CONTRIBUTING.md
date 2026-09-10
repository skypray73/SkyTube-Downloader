# Contributing

感謝你協助改善本專案。

## 開發流程

1. Fork 專案並建立功能分支。
2. 使用 Windows 與 Python 3.12 以上建立 `.venv`。
3. 安裝 `requirements.txt`。
4. 修改後執行測試。
5. 提交 Pull Request，說明問題、變更行為與驗證方式。

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m unittest discover -v
```

不要提交 `.venv`、`tools`、`dist`、下載內容、Cookie、登入資訊或受版權保護的測試影片。新增第三方依賴時，請同步更新 `THIRD_PARTY_NOTICES.md` 並確認其授權與重新散布條件。

回報下載問題時，請附上 GUI 中的錯誤文字、Windows 版本與可公開測試的網址；先移除 Cookie、Token、私人網址參數和帳號資訊。
