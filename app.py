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
    if sys.argv[worker_index + 2:] == ['--check-runtime']:
        from runtime_support import check_ssl_runtime
        print(f'RUNTIME_OK: verified TLS context; {check_ssl_runtime()} CA certificates')
        raise SystemExit(0)
    import yt_dlp
    from video_output import register_mp4_postprocessor

    register_mp4_postprocessor()
    yt_dlp.main(sys.argv[worker_index + 2:])
    raise SystemExit

from tk_runtime import prepare_tk
prepare_tk()
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
from core import MKV_MODE, OUTPUT_MODES, arguments, output_template, parse_urls

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
        self.title('SkyTube Downloader')
        assets = Path(getattr(sys, '_MEIPASS', BASE)) / 'assets'
        if sys.platform == 'win32':
            self.iconbitmap(default=str(assets / 'skytube-icon.ico'))
        self.geometry('1020x740')
        self.minsize(900, 700)
        self.events = queue.Queue()
        self.proc = None
        self.busy = False
        self.stop_event = threading.Event()
        self.protocol('WM_DELETE_WINDOW', self.close)

        bg, panel, ink, muted, line, blue = (
            '#edf3fa', '#ffffff', '#14243b', '#4c6079', '#ccd8e7', '#0868df')
        self.configure(background=bg)
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure('.', font=('Microsoft JhengHei UI', 10), foreground=ink,
                        background=panel)
        style.configure('Page.TFrame', background=bg)
        style.configure('Page.TLabel', background=bg)
        style.configure('Hint.TLabel', foreground=muted)
        style.configure('Title.Page.TLabel', font=('Segoe UI', 26, 'bold'))
        style.configure('Sub.Page.TLabel', foreground=muted)
        style.configure('Field.TLabel', font=('Microsoft JhengHei UI', 10, 'bold'))
        style.configure('Panel.TFrame', relief='solid', borderwidth=1, bordercolor=line)
        style.configure('TButton', padding=(11, 6), background='#edf3fa',
                        bordercolor=line, lightcolor='#edf3fa', darkcolor='#edf3fa')
        style.map('TButton', background=[('active', '#e1edfc')])
        style.configure('Primary.TButton', font=('Microsoft JhengHei UI', 11, 'bold'),
                        padding=(21, 8), background=blue, foreground='white',
                        bordercolor=blue, lightcolor=blue, darkcolor=blue)
        style.map('Primary.TButton',
                  background=[('disabled', '#dbe5f2'), ('pressed', '#0649a2'), ('active', '#0759c4')],
                  foreground=[('disabled', muted)])
        for control in ('TRadiobutton', 'TCheckbutton'):
            style.configure(control, padding=(1, 3), indicatorbackground=panel,
                            indicatorforeground=blue, indicatormargin=(0, 0, 6, 0))
            style.map(control, indicatorbackground=[('selected', blue)],
                      indicatorforeground=[('selected', 'white')])
        for control in ('TEntry', 'TSpinbox', 'TCombobox'):
            style.configure(control, fieldbackground=panel, bordercolor=line,
                            lightcolor=panel, darkcolor=panel, padding=4)
        style.configure('Horizontal.TProgressbar', background=blue,
                        troughcolor='#dce6f2', bordercolor='#dce6f2',
                        lightcolor=blue, darkcolor=blue, thickness=11)

        main = ttk.Frame(self, padding=(20, 14), style='Page.TFrame')
        main.pack(fill='both', expand=True)
        main.columnconfigure(0, weight=1)
        main.rowconfigure(8, weight=1)
        heading = ttk.Frame(main, style='Page.TFrame')
        heading.grid(row=0, sticky='ew', pady=(0, 13))
        self.brand = tk.PhotoImage(file=str(assets / 'skytube-icon.png'))
        ttk.Label(heading, image=self.brand, style='Page.TLabel').grid(
            row=0, column=0, rowspan=2, padx=(0, 11))
        ttk.Label(heading, text='SkyTube Downloader', style='Title.Page.TLabel').grid(
            row=0, column=1, sticky='w')
        ttk.Label(heading, text='YouTube 影片與音訊下載', style='Sub.Page.TLabel').grid(
            row=1, column=1, sticky='w')

        def card(row):
            frame = ttk.Frame(main, padding=(12, 6), style='Panel.TFrame')
            frame.grid(row=row, column=0, sticky='ew', pady=(0, 7))
            frame.columnconfigure(1, weight=1)
            return frame

        links = card(1)
        ttk.Label(links, text='影片連結', style='Field.TLabel', width=12).grid(
            row=0, column=0, sticky='nw', pady=4)
        self.urls = ScrolledText(links, height=3, wrap='word', font=('Consolas', 10),
                                 relief='flat', padx=7, pady=5, background=panel,
                                 foreground=ink, highlightbackground=line, highlightthickness=1)
        self.urls.grid(row=0, column=1, sticky='ew')
        self.playlist = tk.BooleanVar(value=False)
        ttk.Checkbutton(links, text='下載整個播放清單', variable=self.playlist).grid(
            row=1, column=1, sticky='w', pady=(2, 0))
        ttk.Label(links, text='每行一個連結', style='Hint.TLabel').grid(
            row=1, column=1, sticky='e')

        self.quality = self.radio_row(card(2), '最高解析度', [
            ('480p', '480'), ('720p', '720'), ('1080p', '1080'),
            ('2160p', '2160'), ('最高畫質', '最高畫質')], '1080')
        formats = card(3)
        self.mode = self.radio_row(formats, '輸出類型', [
            ('MKV · 最佳影音', MKV_MODE), *((mode, mode) for mode in OUTPUT_MODES[1:])],
            MKV_MODE)
        self.fallback = tk.BooleanVar()
        aac_option = ttk.Checkbutton(formats, text='AAC 不可用時允許轉碼', variable=self.fallback)
        aac_option.grid(row=1, column=1, sticky='w')
        def sync_aac(*_):
            if self.mode.get() == '原始 AAC / M4A':
                aac_option.grid()
            else:
                aac_option.grid_remove()
        self.mode.trace_add('write', sync_aac)
        sync_aac()

        timing = card(4)
        timing.columnconfigure(1, weight=0)
        timing.columnconfigure(2, weight=1)
        self.crop = tk.BooleanVar()
        self.start = self.time_field(timing, 0, '開始時間')
        self.end = self.time_field(timing, 1, '結束時間')
        for value in (*self.start, *self.end):
            value.trace_add('write', self.sync_crop)
        self.precise = tk.BooleanVar(value=True)
        trim_options = ttk.Frame(timing)
        trim_options.grid(row=0, column=2, sticky='e', padx=(8, 0))
        ttk.Checkbutton(trim_options, text='啟用時間裁切', variable=self.crop).grid(sticky='w')
        ttk.Checkbutton(trim_options, text='精準裁切影片', variable=self.precise).grid(sticky='w')

        storage = card(5)
        self.output = self.field(storage, 0, '儲存資料夾', str(BASE / 'download'), 'folder')
        options = ttk.Frame(storage)
        options.grid(row=2, column=0, columnspan=3, sticky='ew')
        options.columnconfigure(1, weight=1)
        self.browser = self.choice(options, 0, '登入 Cookie', ('不使用', 'firefox', 'chrome', 'edge'), '不使用')
        self.cookie = self.field(options, 1, '或 cookies.txt', '', 'file')
        ttk.Label(options, text='Cookie 檔優先，並且只在本機讀取。', style='Hint.TLabel').grid(
            row=2, column=1, sticky='w', pady=(2, 0))
        options.grid_remove()

        def toggle_cookie():
            if options.winfo_ismapped():
                options.grid_remove()
                cookie_toggle.configure(text='顯示 Cookie 設定')
            else:
                options.grid()
                cookie_toggle.configure(text='收合 Cookie 設定')

        cookie_toggle = ttk.Button(storage, text='顯示 Cookie 設定', command=toggle_cookie)
        cookie_toggle.grid(row=1, column=1, sticky='e', pady=(4, 0))

        actions = ttk.Frame(main, style='Page.TFrame')
        actions.grid(row=6, sticky='ew', pady=(3, 4))
        actions.columnconfigure(4, weight=1)
        self.go = ttk.Button(actions, text='開始下載', command=self.download, style='Primary.TButton')
        self.go.grid(row=0, column=0, padx=(0, 8))
        self.cancel = ttk.Button(actions, text='取消', command=self.stop, state='disabled')
        self.cancel.grid(row=0, column=1, padx=(0, 8))
        ttk.Button(actions, text='開啟資料夾', command=self.open_folder).grid(row=0, column=2)
        self.percent = tk.StringVar(value='目前串流 0%')
        ttk.Label(actions, textvariable=self.percent, width=16, style='Page.TLabel').grid(
            row=0, column=3, padx=(17, 5), sticky='w')
        self.bar = ttk.Progressbar(actions, maximum=100)
        self.bar.grid(row=0, column=4, sticky='ew')
        self.status = tk.StringVar(value='準備就緒')
        ttk.Label(main, textvariable=self.status, style='Sub.Page.TLabel', wraplength=850).grid(
            row=7, sticky='w', pady=(1, 5))

        log_card = ttk.Frame(main, padding=(10, 6), style='Panel.TFrame')
        log_card.grid(row=8, sticky='nsew')
        log_card.columnconfigure(0, weight=1)
        log_card.rowconfigure(1, weight=1)
        ttk.Label(log_card, text='下載記錄', style='Field.TLabel').grid(row=0, sticky='w')
        self.log = ScrolledText(log_card, height=4, wrap='word', font=('Consolas', 10),
                                relief='flat', padx=5, pady=4, background='#f7faff',
                                foreground=ink, state='disabled')
        self.log.grid(row=1, sticky='nsew', pady=(4, 0))
        ttk.Label(main, text='製作人：Skypray Huang  ·  v1.5.0', style='Sub.Page.TLabel').grid(
            row=9, sticky='e', pady=(6, 0))
        self.after(100, self.poll)

    def radio_row(self, frame, label, options, default):
        var = tk.StringVar(value=default)
        ttk.Label(frame, text=label, style='Field.TLabel', width=12).grid(
            row=0, column=0, sticky='w')
        row = ttk.Frame(frame)
        row.grid(row=0, column=1, sticky='ew')
        for column, (text, value) in enumerate(options):
            row.columnconfigure(column, weight=1)
            ttk.Radiobutton(row, text=text, value=value, variable=var).grid(
                row=0, column=column, sticky='w', padx=(0, 8))
        return var


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

    def time_field(self, frame, column, label):
        box = ttk.Frame(frame)
        box.grid(row=0, column=column, sticky='w', padx=(0, 16))
        ttk.Label(box, text=label, style='Field.TLabel').grid(
            row=0, column=0, rowspan=2, padx=(0, 12))
        values = [tk.StringVar() for _ in range(3)]
        for index, (var, limit, name) in enumerate(zip(values, (999, 59, 59), ('HH', 'MM', 'SS')), 1):
            ttk.Label(box, text=name, style='Hint.TLabel').grid(row=0, column=index)
            ttk.Spinbox(box, from_=0, to=limit, textvariable=var, width=4,
                        justify='center', wrap=False).grid(row=1, column=index, padx=2)
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
        self.log.insert('end', f'[{time.strftime("%H:%M:%S")}] {line}\n')
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
        self.set_progress(0)
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

    def set_progress(self, percent):
        percent = max(0, min(100, percent))
        self.bar['value'] = percent
        self.percent.set(f'目前串流 {percent:.0f}%')

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
                    self.set_progress(100)
                    self.status.set(f'批次完成：{value["completed"]}/{value["total"]} 個連結成功，已產生 {value["files"]} 個檔案。路徑見 FILE 訊息。')
                else:
                    self.set_progress(0)
                    self.status.set(f'批次結束：{value["completed"]} 個連結成功、{value["failed"]} 個未完整成功，已產生 {value["files"]} 個檔案。請查看 ERROR。')
                self.append(self.status.get())
            elif kind == 'link':
                self.batch_prefix = f'連結 {value[0]}/{value[1]}'
                self.set_progress(0)
                self.status.set(self.batch_prefix + '；正在取得影片資訊…')
            elif value.startswith('PROGRESS:'):
                match = re.search(r'(\d+(?:\.\d+)?)%', value)
                if match:
                    self.set_progress(float(match.group(1)))
            elif value.startswith('PROCESS:started:') and not value.endswith(':MoveFiles'):
                self.status.set(self.batch_prefix + '；正在處理影音…')
            elif not value.startswith('PROCESS:'):
                self.append(value)
                if value.startswith('ITEM:'):
                    self.set_progress(0)
                    self.status.set(self.batch_prefix + '；正在下載：' + value[5:])
                elif value.startswith('[SkyTubeMP4] '):
                    self.status.set(self.batch_prefix + ' · ' + value.removeprefix('[SkyTubeMP4] '))
                elif value.startswith(('[Merger]', '[ExtractAudio]', '[VideoRemuxer]', '[VideoConvertor]')):
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
