import os
import queue
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from pathlib import Path

# Re-enter the packaged executable as a console-free download worker.
if '--worker' in sys.argv:
    worker_index = sys.argv.index('--worker')
    sys.stdout = open(sys.argv[worker_index + 1], 'w', encoding='utf-8', buffering=1)
    sys.stderr = sys.stdout
    import yt_dlp
    yt_dlp.main(sys.argv[worker_index + 2:])
    raise SystemExit

from tk_runtime import prepare_tk
prepare_tk()
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
from core import arguments, output_template, parse_urls

BASE = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).parent


def binary(name):
    for root in (BASE / 'tools', Path(getattr(sys, '_MEIPASS', BASE)) / 'tools'):
        target = root / (name + '.exe')
        if target.exists():
            return str(target)
    return shutil.which(name) or ''


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('SkyTube Downloader · Skypray Huang')
        self.geometry('850x930')
        self.minsize(800, 880)
        self.events = queue.Queue()
        self.proc = None
        self.busy = False
        self.stop_event = threading.Event()
        self.protocol('WM_DELETE_WINDOW', self.close)
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure('.', font=('Microsoft JhengHei UI', 10))
        style.configure('TButton', padding=7)
        main = ttk.Frame(self, padding=20)
        main.pack(fill='both', expand=True)
        main.columnconfigure(1, weight=1)
        ttk.Label(main, text='SkyTube Downloader', font=('Segoe UI', 22, 'bold')).grid(row=0, column=0, columnspan=3, sticky='w')
        ttk.Label(main, text='Portable 本機版 • 多連結／播放清單批次下載 • 內含 FFmpeg、Deno 與 yt-dlp').grid(row=1, column=0, columnspan=3, sticky='w', pady=(0, 16))
        ttk.Label(main, text='影片／播放清單\n每行一個連結').grid(row=2, column=0, sticky='nw', pady=5)
        self.urls = ScrolledText(main, height=4, wrap='word', font=('Consolas', 10))
        self.urls.grid(row=2, column=1, columnspan=2, sticky='ew', pady=5)
        self.playlist = tk.BooleanVar(value=True)
        ttk.Checkbutton(main, text='下載整個播放清單（未勾選時只下載目前影片）', variable=self.playlist).grid(row=3, column=1, columnspan=2, sticky='w')
        self.quality = self.choice(main, 4, '最高解析度', ('480', '720', '1080', '2160', '最高畫質'), '1080')
        self.mode = self.choice(main, 5, '輸出類型', ('影片＋最佳音訊', 'MP3 音訊', '原始 AAC / M4A'), '影片＋最佳音訊')
        self.fallback = tk.BooleanVar()
        ttk.Checkbutton(main, text='AAC 不可用時允許轉碼（不再是原始 AAC）', variable=self.fallback).grid(row=6, column=1, columnspan=2, sticky='w')
        self.crop = tk.BooleanVar()
        ttk.Checkbutton(main, text='啟用時間裁切（套用到本批次每一部影片）', variable=self.crop).grid(row=7, column=1, columnspan=2, sticky='w')
        self.start = self.time_field(main, 8, '開始時間', (None, None, None))
        self.end = self.time_field(main, 9, '結束時間', (None, None, None))
        for value in (*self.start, *self.end):
            value.trace_add('write', self.sync_crop)
        self.precise = tk.BooleanVar(value=True)
        ttk.Checkbutton(main, text='精準裁切影片（避免開頭停格，會重新編碼）', variable=self.precise).grid(row=10, column=1, columnspan=2, sticky='w')
        self.output = self.field(main, 11, '儲存資料夾', str(BASE / 'download'), 'folder')
        self.browser = self.choice(main, 12, '登入 Cookie', ('不使用', 'firefox', 'chrome', 'edge'), '不使用')
        self.cookie = self.field(main, 13, '或 cookies.txt', '', 'file')
        ttk.Label(main, text='Cookie 檔優先；只在本機讀取。Chrome / Edge 可能無法解密，Cookie 不保證解除阻擋。', wraplength=780).grid(row=14, column=0, columnspan=3, sticky='w', pady=6)
        actions = ttk.Frame(main)
        actions.grid(row=15, column=0, columnspan=3, sticky='ew', pady=8)
        self.go = ttk.Button(actions, text='開始下載', command=self.download)
        self.go.pack(side='left')
        self.cancel = ttk.Button(actions, text='取消', command=self.stop, state='disabled')
        self.cancel.pack(side='left', padx=8)
        ttk.Button(actions, text='開啟資料夾', command=self.open_folder).pack(side='left')
        self.bar = ttk.Progressbar(main, maximum=100)
        self.bar.grid(row=16, column=0, columnspan=3, sticky='ew')
        self.status = tk.StringVar(value='準備就緒 · 影片以 MKV 保存最佳影音；AAC 以 M4A 保存。')
        ttk.Label(main, textvariable=self.status, wraplength=790).grid(row=17, column=0, columnspan=3, sticky='w', pady=5)
        self.log = ScrolledText(main, height=10, wrap='word', font=('Consolas', 10), state='disabled')
        self.log.grid(row=18, column=0, columnspan=3, sticky='nsew')
        main.rowconfigure(18, weight=1)
        ttk.Label(main, text='製作人：Skypray Huang  •  v1.3.0  •  2026/11/06', foreground='#666666').grid(row=19, column=0, columnspan=3, sticky='e', pady=(8, 0))
        self.after(100, self.poll)

    def field(self, frame, row, label, default, picker=None):
        var = tk.StringVar(value=default)
        ttk.Label(frame, text=label).grid(row=row, column=0, sticky='w', padx=(0, 12), pady=5)
        ttk.Entry(frame, textvariable=var).grid(row=row, column=1, sticky='ew', pady=5)
        if picker:
            def choose():
                value = filedialog.askdirectory() if picker == 'folder' else filedialog.askopenfilename()
                if value:
                    var.set(value)
            ttk.Button(frame, text='選擇', command=choose).grid(row=row, column=2, padx=(8, 0))
        return var

    def choice(self, frame, row, label, options, default):
        var = tk.StringVar(value=default)
        ttk.Label(frame, text=label).grid(row=row, column=0, sticky='w', pady=5)
        ttk.Combobox(frame, values=options, textvariable=var, state='readonly').grid(row=row, column=1, sticky='ew', pady=5)
        return var

    def time_field(self, frame, row, label, default):
        ttk.Label(frame, text=label).grid(row=row, column=0, sticky='w', padx=(0, 12), pady=5)
        box = ttk.Frame(frame)
        box.grid(row=row, column=1, columnspan=2, sticky='w', pady=5)
        values = [tk.StringVar(value='' if value is None else f'{value:02d}') for value in default]
        for index, (var, limit, name) in enumerate(zip(values, (999, 59, 59), ('HH', 'MM', 'SS'))):
            ttk.Spinbox(box, from_=0, to=limit, textvariable=var,
                        width=5 if index == 0 else 3, justify='center', wrap=False).grid(
                            row=0, column=index * 2, padx=(0, 4))
            ttk.Label(box, text=name).grid(row=0, column=index * 2 + 1, padx=(0, 10))
        return values

    @staticmethod
    def format_time(values):
        raw = [value.get().strip() for value in values]
        if not any(raw):
            return ''
        try:
            h, m, s = (int(value or 0) for value in raw)
        except ValueError:
            raise ValueError('時間欄位只能輸入數字。')
        if not 0 <= h <= 999 or not 0 <= m <= 59 or not 0 <= s <= 59:
            raise ValueError('小時需為 0–999，分鐘與秒需為 0–59。')
        return f'{h:02d}:{m:02d}:{s:02d}'

    def sync_crop(self, *_):
        self.crop.set(any(value.get().strip() for value in (*self.start, *self.end)))

    def append(self, line):
        self.log.configure(state='normal')
        self.log.insert('end', line + '\n')
        if int(self.log.index('end-1c').split('.')[0]) > 1500:
            self.log.delete('1.0', '300.0')
        self.log.see('end')
        self.log.configure(state='disabled')

    def download(self):
        if self.busy:
            return
        try:
            urls = parse_urls(self.urls.get('1.0', 'end'))
            ffmpeg = binary('ffmpeg')
            deno = binary('deno')
            if not ffmpeg or not deno:
                raise ValueError('內嵌的 FFmpeg 或 Deno 無法載入，請重新取得完整程式。')
            cookie = self.cookie.get().strip()
            if cookie and not Path(cookie).is_file():
                raise ValueError('找不到 Cookie 檔案。')
            out = self.output.get().strip()
            if not out:
                raise ValueError('請選擇儲存資料夾。')
            start = self.format_time(self.start) if self.crop.get() else ''
            end = self.format_time(self.end) if self.crop.get() else ''
            if self.crop.get() and not start and not end:
                raise ValueError('請填寫開始或結束時間，或取消勾選時間裁切。')
            commands = []
            for url in urls:
                args = arguments(url, self.quality.get(), self.mode.get(),
                    start, end, self.precise.get(), out, str(Path(ffmpeg).parent), cookie,
                    '' if self.browser.get() == '不使用' else self.browser.get(),
                    self.fallback.get(), deno, self.playlist.get())
                args[args.index('-o') + 1] = output_template(
                    url, self.playlist.get(), uuid.uuid4().hex[:10])
                commands.append(args)
            Path(out).mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            messagebox.showerror('無法開始', str(exc))
            return
        self.busy = True
        self.stop_event.clear()
        self.go.configure(state='disabled')
        self.cancel.configure(state='normal')
        self.bar['value'] = 0
        self.batch_prefix = f'共 {len(commands)} 個連結'
        self.urls.configure(state='disabled')
        self.status.set(self.batch_prefix + '；正在取得影片資訊…')
        self.append(f'開始批次：{len(commands)} 個連結（已移除完全相同的重複連結）。各連結依序下載；百分比為目前串流進度。')
        threading.Thread(target=self.run, args=(commands,), daemon=True).start()

    def run(self, commands):
        result = dict(total=len(commands), completed=0, failed=0, files=0)
        try:
            for index, args in enumerate(commands, 1):
                if self.stop_event.is_set():
                    break
                self.events.put(('link', (index, len(commands))))
                self.events.put(('line', f'── 連結 {index}/{len(commands)}：{args[-1]}'))
                code, files = self.run_one(args)
                result['files'] += files
                if self.stop_event.is_set():
                    break
                result['completed' if code == 0 else 'failed'] += 1
                if code:
                    self.events.put(('line', f'ERROR: 連結 {index}/{len(commands)} 未完整成功，繼續下一個連結。'))
        except Exception as exc:
            result['failed'] += 1
            self.events.put(('line', 'ERROR: ' + str(exc)))
        finally:
            self.events.put(('done', result))

    def run_one(self, args):
        args = list(args)
        code = 1
        files = 0
        try:
            # yt-dlp may save its cookie jar; work on a temporary copy only.
            with tempfile.TemporaryDirectory(prefix='ytd-gui-') as temp:
                if '--cookies' in args:
                    index = args.index('--cookies') + 1
                    target = str(Path(temp) / 'cookies.txt')
                    shutil.copyfile(args[index], target)
                    args[index] = target
                logfile = Path(temp) / 'worker.log'
                logfile.touch()
                command = [sys.executable, '--worker', str(logfile)] if getattr(sys, 'frozen', False) else [sys.executable, '-u', str(Path(__file__).resolve()), '--worker', str(logfile)]
                env = dict(os.environ, PYTHONIOENCODING='utf-8', PYTHONUNBUFFERED='1')
                self.proc = subprocess.Popen(command + args, stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL, env=env,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                if self.stop_event.is_set():
                    self.kill()
                with logfile.open(encoding='utf-8', errors='replace') as stream:
                    while True:
                        line = stream.readline()
                        if line:
                            self.events.put(('line', line.rstrip()))
                            files += int(line.startswith('FILE:'))
                        elif self.proc.poll() is not None:
                            for tail in stream:
                                self.events.put(('line', tail.rstrip()))
                                files += int(tail.startswith('FILE:'))
                            break
                        else:
                            time.sleep(0.1)
                code = self.proc.wait()
        except Exception as exc:
            self.events.put(('line', 'ERROR: ' + str(exc)))
        finally:
            self.proc = None
        return code, files

    def kill(self):
        proc = self.proc
        if proc and proc.poll() is None:
            if os.name == 'nt':
                subprocess.run(['taskkill', '/PID', str(proc.pid), '/T', '/F'],
                    capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                proc.terminate()

    def stop(self):
        self.stop_event.set()
        self.cancel.configure(state='disabled')
        self.status.set('正在取消…')
        threading.Thread(target=self.kill, daemon=True).start()

    def poll(self):
        while True:
            try:
                kind, value = self.events.get_nowait()
            except queue.Empty:
                break
            if kind == 'done':
                self.busy = False
                self.urls.configure(state='normal')
                self.go.configure(state='normal')
                self.cancel.configure(state='disabled')
                if self.stop_event.is_set():
                    self.status.set(f'已取消；已產生 {value["files"]} 個檔案。下載資料夾可能留有未完成檔案。')
                elif value['failed'] == 0:
                    self.bar['value'] = 100
                    self.status.set(f'批次完成：{value["completed"]}/{value["total"]} 個連結成功，已產生 {value["files"]} 個檔案。路徑見 FILE 訊息。')
                else:
                    self.bar['value'] = 0
                    self.status.set(f'批次結束：{value["completed"]} 個連結成功、{value["failed"]} 個未完整成功，已產生 {value["files"]} 個檔案。請查看 ERROR。')
                self.append(self.status.get())
            elif kind == 'link':
                self.batch_prefix = f'連結 {value[0]}/{value[1]}'
                self.bar['value'] = 0
                self.status.set(self.batch_prefix + '；正在取得影片資訊…')
            elif value.startswith('PROGRESS:'):
                match = re.search(r'(\d+(?:\.\d+)?)%', value)
                if match:
                    self.bar['value'] = float(match.group(1))
                    self.status.set(self.batch_prefix + '；目前串流 ' + match.group(0) + '；後續可能仍需合併／裁切')
            else:
                self.append(value)
                if value.startswith('ITEM:'):
                    self.bar['value'] = 0
                    self.status.set(self.batch_prefix + '；正在下載：' + value[5:])
                if value.startswith(('[Merger]', '[ExtractAudio]', '[VideoRemuxer]', '[VideoConvertor]')):
                    self.status.set(self.batch_prefix + '；正在處理影音，請稍候…')
        self.after(100, self.poll)

    def open_folder(self):
        path = Path(self.output.get())
        if path.is_dir():
            os.startfile(str(path.resolve()))

    def close(self):
        if self.busy:
            if not messagebox.askyesno('結束程式', '下載仍在進行，要取消並關閉嗎？'):
                return
            self.stop()
            self.after(200, self.wait_close)
        else:
            self.destroy()

    def wait_close(self):
        if self.busy:
            self.after(200, self.wait_close)
        else:
            self.destroy()


if __name__ == '__main__':
    App().mainloop()
