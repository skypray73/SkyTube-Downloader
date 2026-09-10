$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
python -m venv .venv
if ($LASTEXITCODE -ne 0) { throw 'Unable to create Python environment' }
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install --upgrade -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed' }
& .\.venv\Scripts\python.exe build.py
if ($LASTEXITCODE -ne 0) { throw 'Packaging failed' }
Write-Host 'Ready: dist\YouTubeDownloader.exe (single-file build)'
