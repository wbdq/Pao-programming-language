#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
泡语言编辑器 —— 专为「泡语言（中文Python）」设计的轻量 IDE，界面风格类似 PyCharm。

功能：
  * 代码编辑：语法高亮（关键词/内置函数/字符串/注释/数字）、行号、Tab 自动缩进
  * 文件管理：左侧文件列表（.pao / .zy）、新建 / 打开 / 保存 / 另存为
  * 运行调试：一键运行（调用同目录的 泡语言.exe）、停止按钮、输出控制台、程序输入框
  * 内置自检：一键验证语言环境是否正常

运行方式：
  源码：  python paolang_ide.py
  打包：  PyInstaller 打包为 泡语言编辑器.exe（无需安装 Python 环境）
"""

import codecs
import os
import queue
import re
import subprocess
import sys
import tempfile
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import paolang

APP_NAME = "泡语言编辑器"


def _查找图标():
    """定位 泡.ico：打包后位于 _MEIPASS，源码运行时位于脚本旁边。"""
    if getattr(sys, "frozen", False):
        base = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base, "泡.ico")
    return path if os.path.exists(path) else None
LANG_NAME = paolang.LANG_NAME
VERSION = "1.0.3"

# ---------------------------------------------------------------------------
# 语法高亮
# ---------------------------------------------------------------------------
def _esc(k: str) -> str:
    return re.escape(k)

KW_KEYS = sorted(paolang.KEYWORDS.keys(), key=len, reverse=True)
BI_KEYS = sorted({**paolang.BUILTIN_ALIASES, **paolang.EXCEPTION_ALIASES}.keys(), key=len, reverse=True)

RE_KEYWORD = re.compile(r"(?<![\w])(" + "|".join(_esc(k) for k in KW_KEYS) + r")(?![\w])")
RE_BUILTIN = re.compile(r"(?<![\w])(" + "|".join(_esc(k) for k in BI_KEYS) + r")(?![\w])")
RE_STRING = re.compile(r'"(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\'')
RE_COMMENT = re.compile(r"#[^\n]*")
RE_NUMBER = re.compile(r"(?<![\w.])\d+(?:\.\d+)?(?![\w])")

# 主题（暗色，参考 PyCharm）
COLORS = {
    "bg": "#282C34",
    "fg": "#ABB2BF",
    "gutter_bg": "#21252B",
    "gutter_fg": "#5C6370",
    "console_bg": "#1E1F22",
    "console_fg": "#D4D4D4",
    "keyword": "#C678DD",
    "builtin": "#61AFEF",
    "string": "#98C379",
    "comment": "#5C6370",
    "number": "#D19A66",
    "err": "#F44747",
    "info": "#61AFEF",
    "sel": "#3E4451",
    "line": "#3E4451",
}

FONT_UI = ("Microsoft YaHei UI", 9)
FONT_CODE = ("Consolas", 12)
FILE_EXTS = (".pao", ".zy")


class PaoLangIDE:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry("1120x720")
        self.root.minsize(820, 520)

        self.current_path = None
        self.folder = None
        self.proc = None
        self.out_q = queue.Queue()
        self.font_size = 12
        # 运行日志轮询状态
        self.log_out_path = None
        self.log_err_path = None
        self.log_fh_out = None
        self.log_fh_err = None
        self.log_pos_out = 0
        self.log_pos_err = 0
        self.log_dec_out = None
        self.log_dec_err = None

        self._build_menu()
        self._build_toolbar()
        self._build_body()
        self._build_statusbar()
        self._bind_shortcuts()
        self._init_theme()

        # 初始文件夹：程序所在目录；若有演示文件则自动打开
        base = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, "frozen", False) else __file__))
        self.folder = base
        self.refresh_tree()
        demo = os.path.join(base, "演示.pao")
        if os.path.exists(demo):
            self.open_file(demo)
        else:
            self._set_status("就绪")

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ------------------------------------------------------------------
    # 界面搭建
    # ------------------------------------------------------------------
    def _build_menu(self):
        m = tk.Menu(self.root)
        fm = tk.Menu(m, tearoff=0)
        fm.add_command(label="新建（Ctrl+N）", command=self.new_file)
        fm.add_command(label="打开（Ctrl+O）", command=self.open_file_dialog)
        fm.add_command(label="保存（Ctrl+S）", command=self.save_file_dialog)
        fm.add_command(label="另存为", command=self.save_as)
        fm.add_separator()
        fm.add_command(label="退出", command=self._on_close)
        m.add_cascade(label="文件", menu=fm)

        rm = tk.Menu(m, tearoff=0)
        rm.add_command(label="运行程序（Ctrl+R）", command=self.run_current)
        rm.add_command(label="停止运行", command=self.stop)
        rm.add_separator()
        rm.add_command(label="运行内置自检", command=self.run_selfcheck)
        m.add_cascade(label="运行", menu=rm)

        vm = tk.Menu(m, tearoff=0)
        vm.add_command(label="增大字号", command=lambda: self._change_font(1))
        vm.add_command(label="减小字号", command=lambda: self._change_font(-1))
        vm.add_command(label="重置字号", command=lambda: self._change_font(0))
        m.add_cascade(label="视图", menu=vm)

        hm = tk.Menu(m, tearoff=0)
        hm.add_command(label="快速上手", command=self.show_guide)
        hm.add_command(label="关于", command=self.show_about)
        m.add_cascade(label="帮助", menu=hm)
        self.root.config(menu=m)

    def _build_toolbar(self):
        bar = tk.Frame(self.root, bg="#21252B")
        bar.pack(side="top", fill="x")
        style = ttk.Style()
        try:
            style.theme_use("vista")
        except tk.TclError:
            pass

        for text, cmd in (
            ("新建", self.new_file), ("打开", self.open_file_dialog),
            ("保存", self.save_file_dialog), ("运行", self.run_current),
            ("停止", self.stop), ("自检", self.run_selfcheck),
        ):
            b = ttk.Button(bar, text=text, command=cmd, width=6)
            b.pack(side="left", padx=3, pady=3)
        ttk.Button(bar, text="选择文件夹", command=self.choose_folder, width=10).pack(side="left", padx=3)

    def _build_body(self):
        # 左右分栏：左文件列表，右编辑区+控制台
        outer = ttk.PanedWindow(self.root, orient="horizontal")
        outer.pack(fill="both", expand=True)

        # ---- 左侧：文件列表 ----
        left = tk.Frame(outer, bg="#21252B")
        outer.add(left, weight=1)
        up_btn = ttk.Button(left, text="↑ 上级目录", command=self.go_up)
        up_btn.pack(fill="x", padx=3, pady=(3, 0))
        self.tree = ttk.Treeview(left, show="tree", selectmode="browse")
        self.tree.pack(fill="both", expand=True, padx=3, pady=3)
        self.tree.tag_configure("dir", foreground="#61AFEF")
        self.tree.tag_configure("file", foreground="#D4D4D4")
        self.tree.bind("<Double-1>", self._on_tree_double)

        # ---- 右侧：编辑区 + 控制台 ----
        right = ttk.PanedWindow(outer, orient="vertical")
        outer.add(right, weight=4)

        edit_frame = tk.Frame(right, bg=COLORS["bg"])
        right.add(edit_frame, weight=3)

        # 行号栏 + 编辑器（共享纵向滚动）
        scroll = ttk.Scrollbar(edit_frame, orient="vertical")
        scroll.pack(side="right", fill="y")
        self.gutter = tk.Text(
            edit_frame, width=5, bg=COLORS["gutter_bg"], fg=COLORS["gutter_fg"],
            font=FONT_CODE, padx=4, pady=4, state="disabled", takefocus=0,
            highlightthickness=0, borderwidth=0, wrap="none", cursor="arrow",
        )
        self.gutter.pack(side="left", fill="y")
        self.editor = tk.Text(
            edit_frame, bg=COLORS["bg"], fg=COLORS["fg"], font=FONT_CODE,
            insertbackground=COLORS["fg"], selectbackground=COLORS["sel"],
            padx=6, pady=4, undo=True, wrap="none", highlightthickness=0,
            borderwidth=0, yscrollcommand=lambda a, b: (
                self.gutter.yview_moveto(a), scroll.set(a, b)),
        )
        self.editor.pack(side="left", fill="both", expand=True)
        scroll.config(command=self.editor.yview)
        self.editor.bind("<<Modified>>", self._on_modified)
        self.editor.bind("<Tab>", self._on_tab)
        self.editor.bind("<KeyRelease>", self._update_cursor)
        self.editor.bind("<ButtonRelease>", self._update_cursor)

        # 控制台区
        console_frame = tk.Frame(right, bg="#1E1F22")
        right.add(console_frame, weight=1)
        self.console = tk.Text(
            console_frame, bg=COLORS["console_bg"], fg=COLORS["console_fg"],
            font=("Consolas", 11), padx=6, pady=4, state="disabled",
            wrap="none", highlightthickness=0, borderwidth=0,
        )
        self.console.pack(fill="both", expand=True)
        input_row = tk.Frame(console_frame, bg="#1E1F22")
        input_row.pack(fill="x", padx=6, pady=4)
        tk.Label(input_row, text="程序输入:", bg="#1E1F22", fg="#9DA5B4",
                 font=FONT_UI).pack(side="left")
        self.input_entry = tk.Entry(
            input_row, bg="#32363D", fg="#D4D4D4", insertbackground="#D4D4D4",
            font=("Consolas", 11), relief="flat",
        )
        self.input_entry.pack(side="left", fill="x", expand=True, padx=6)
        self.input_entry.bind("<Return>", self.send_input)
        self.input_entry.config(state="disabled")
        ttk.Button(input_row, text="发送", width=6, command=self.send_input).pack(side="left")

    def _build_statusbar(self):
        bar = tk.Frame(self.root, bg="#21252B")
        bar.pack(side="bottom", fill="x")
        self.lbl_file = tk.Label(bar, text="未命名", bg="#21252B", fg="#9DA5B4",
                                 font=FONT_UI, anchor="w")
        self.lbl_file.pack(side="left", padx=8)
        self.lbl_pos = tk.Label(bar, text="行:1 列:1", bg="#21252B", fg="#9DA5B4",
                                font=FONT_UI)
        self.lbl_pos.pack(side="left", padx=8)
        self.lbl_state = tk.Label(bar, text="就绪", bg="#21252B", fg="#61AFEF",
                                  font=FONT_UI, anchor="e")
        self.lbl_state.pack(side="right", padx=8)

    def _init_theme(self):
        self.editor.tag_configure("keyword", foreground=COLORS["keyword"])
        self.editor.tag_configure("builtin", foreground=COLORS["builtin"])
        self.editor.tag_configure("string", foreground=COLORS["string"])
        self.editor.tag_configure("comment", foreground=COLORS["comment"])
        self.editor.tag_configure("number", foreground=COLORS["number"])
        self.console.tag_configure("out", foreground=COLORS["console_fg"])
        self.console.tag_configure("err", foreground=COLORS["err"])
        self.console.tag_configure("info", foreground=COLORS["info"])

    def _bind_shortcuts(self):
        for seq, fn in (
            ("<Control-n>", lambda e: self.new_file()),
            ("<Control-o>", lambda e: self.open_file_dialog()),
            ("<Control-s>", lambda e: self.save_file_dialog()),
            ("<Control-r>", lambda e: self.run_current()),
            ("<Control-z>", lambda e: self._undo(e)),
        ):
            self.root.bind_all(seq, fn)

    # ------------------------------------------------------------------
    # 文件操作
    # ------------------------------------------------------------------
    def new_file(self):
        if self._confirm_discard():
            if self.proc and self.proc.poll() is None:
                messagebox.showwarning(APP_NAME, "程序正在运行，请先停止。")
                return
            self.editor.delete("1.0", "end")
            self.current_path = None
            self._update_title()
            self._set_status("就绪")

    def open_file_dialog(self):
        path = filedialog.askopenfilename(
            title="打开泡语言程序",
            defaultextension=".pao",
            filetypes=[("泡语言程序", "*.pao *.zy"), ("所有文件", "*.*")],
        )
        if path:
            self.open_file(path)

    def open_file(self, path):
        if not os.path.exists(path):
            messagebox.showerror(APP_NAME, f"文件不存在：\n{path}")
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except OSError as e:
            messagebox.showerror(APP_NAME, f"打开失败：{e}")
            return
        self.editor.delete("1.0", "end")
        self.editor.insert("1.0", content)
        self.editor.edit_reset()
        self.editor.edit_modified(False)
        self.current_path = path
        folder = os.path.dirname(path)
        if folder != self.folder:
            self.folder = folder
            self.refresh_tree()
        self._update_title()
        self._highlight()
        self._set_status("就绪")

    def save_file_dialog(self):
        if self.current_path is None:
            return self.save_as()
        return self._write_file(self.current_path)

    def save_as(self):
        path = filedialog.asksaveasfilename(
            title="保存泡语言程序",
            defaultextension=".pao",
            filetypes=[("泡语言程序", "*.pao"), ("所有文件", "*.*")],
        )
        if not path:
            return False
        self.current_path = path
        folder = os.path.dirname(path)
        if folder != self.folder:
            self.folder = folder
            self.refresh_tree()
        return self._write_file(path)

    def _write_file(self, path):
        try:
            content = self.editor.get("1.0", "end-1c")
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
        except OSError as e:
            messagebox.showerror(APP_NAME, f"保存失败：{e}")
            return False
        self.editor.edit_modified(False)
        self._update_title()
        self._set_status("已保存")
        return True

    def _confirm_discard(self):
        if self.editor.edit_modified():
            return messagebox.askyesno(APP_NAME, "当前文件有未保存的修改，确定放弃吗？")
        return True

    # ------------------------------------------------------------------
    # 文件列表
    # ------------------------------------------------------------------
    def choose_folder(self):
        folder = filedialog.askdirectory(title="选择程序文件夹")
        if folder:
            self.folder = folder
            self.refresh_tree()
            self._set_status(f"文件夹：{folder}")

    def go_up(self):
        if self.folder:
            parent = os.path.dirname(self.folder.rstrip("\\/"))
            if parent and os.path.isdir(parent):
                self.folder = parent
                self.refresh_tree()

    def refresh_tree(self):
        self.tree.delete(*self.tree.get_children())
        if not self.folder or not os.path.isdir(self.folder):
            return
        try:
            entries = sorted(os.listdir(self.folder), key=str.lower)
        except OSError:
            return
        for name in entries:
            full = os.path.join(self.folder, name)
            if os.path.isdir(full):
                self.tree.insert("", "end", iid="d:" + full, text="▸ " + name,
                                 values=("dir", full), tags=("dir",))
            elif name.lower().endswith(FILE_EXTS):
                self.tree.insert("", "end", iid="f:" + full, text=name,
                                 values=("file", full), tags=("file",))

    def _on_tree_double(self, event):
        item = self.tree.identify_row(event.y)
        if not item:
            return
        kind, full = self.tree.item(item, "values")
        if kind == "dir":
            self.folder = full
            self.refresh_tree()
        else:
            self.open_file(full)

    # ------------------------------------------------------------------
    # 编辑辅助
    # ------------------------------------------------------------------
    def _on_tab(self, event):
        self.editor.insert("insert", "    ")
        return "break"

    def _undo(self, event):
        try:
            self.editor.edit_undo()
        except tk.TclError:
            pass
        return "break"

    def _on_modified(self, event=None):
        if not self.editor.edit_modified():
            return
        self.editor.edit_modified(False)
        self._update_title()
        self._update_gutter()
        self.root.after(120, self._highlight)

    def _update_title(self):
        name = os.path.basename(self.current_path) if self.current_path else "未命名"
        star = "*" if self.editor.edit_modified() else ""
        self.root.title(f"{APP_NAME} — {name}{star}")
        self.lbl_file.config(text=(self.current_path or "未命名"))

    def _update_gutter(self):
        try:
            lines = int(self.editor.index("end-1c").split(".")[0])
        except tk.TclError:
            lines = 1
        self.gutter.config(state="normal")
        self.gutter.delete("1.0", "end")
        self.gutter.insert("1.0", "\n".join(str(i) for i in range(1, lines + 1)))
        self.gutter.config(state="disabled")

    def _update_cursor(self, event=None):
        try:
            pos = self.editor.index("insert")
            row, col = pos.split(".")
            self.lbl_pos.config(text=f"行:{row} 列:{int(col) + 1}")
        except tk.TclError:
            pass

    def _change_font(self, delta):
        if delta == 0:
            self.font_size = 12
        else:
            self.font_size = max(9, min(24, self.font_size + delta))
        for w in (self.editor, self.gutter):
            w.config(font=("Consolas", self.font_size))
        self.console.config(font=("Consolas", max(9, self.font_size - 1)))

    def _highlight(self):
        text = self.editor
        content = text.get("1.0", "end-1c")
        if len(content) > 500_000:  # 超大文件暂不高亮，保证流畅
            return
        for tag in ("keyword", "builtin", "string", "comment", "number"):
            text.tag_remove(tag, "1.0", "end")

        def add(regex, tag):
            for m in regex.finditer(content):
                try:
                    text.tag_add(tag, "1.0+" + str(m.start()) + "c",
                                 "1.0+" + str(m.end()) + "c")
                except tk.TclError:
                    break

        add(RE_NUMBER, "number")
        add(RE_BUILTIN, "builtin")
        add(RE_KEYWORD, "keyword")
        add(RE_STRING, "string")
        add(RE_COMMENT, "comment")
        text.tag_raise("comment")
        text.tag_raise("string")

    # ------------------------------------------------------------------
    # 运行
    # ------------------------------------------------------------------
    def _interpreter_cmd(self):
        if getattr(sys, "frozen", False):
            exe = os.path.join(os.path.dirname(os.path.abspath(sys.executable)), "泡语言.exe")
            if not os.path.exists(exe):
                messagebox.showerror(
                    APP_NAME,
                    f"找不到解释器 泡语言.exe。\n请把它和编辑器放在同一文件夹。\n\n当前查找位置：\n{exe}")
                return None
            return [exe]
        return [sys.executable, "-u", os.path.abspath(paolang.__file__)]

    def run_current(self, event=None):
        if self.proc and self.proc.poll() is None:
            messagebox.showinfo(APP_NAME, "程序正在运行中，请先停止。")
            return
        path = self.current_path
        if path is None:
            if not self.save_as():
                return
            path = self.current_path
        if not self._write_file(path):
            return

        base = self._interpreter_cmd()
        if base is None:
            return
        if not self._prepare_logs():
            return
        # 解释器把输出实时追加到日志文件，编辑器轮询文件来显示——
        # 不受管道缓冲影响，输入() 的提示文字能立刻出现
        cmd = base + ["--run-log", self.log_out_path, self.log_err_path, "--run", path]
        self._clear_console()
        self._append_console(f"▶ 运行 {path}\n", "info")
        env = dict(os.environ)
        env["PYTHONUNBUFFERED"] = "1"  # 子进程输出无缓冲
        env["PYTHONUTF8"] = "1"       # 子进程按 UTF-8 读写，中文不乱码
        try:
            kwargs = {}
            if os.name == "nt":
                # 子进程不弹黑色控制台窗口（图形界面程序尤其需要）
                kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
            self.proc = subprocess.Popen(
                cmd, cwd=os.path.dirname(path) or ".",
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                stdin=subprocess.PIPE, env=env, **kwargs,
            )
        except Exception as e:
            self._append_console(f"启动失败：{e}\n", "err")
            self._close_logs()
            self.proc = None
            self._set_status("启动失败")
            return
        self.input_entry.config(state="normal")
        self.input_entry.focus_set()
        self._set_status("运行中…")
        self.root.after(60, self._poll_log)

    def _prepare_logs(self):
        """新建一对运行日志文件并打开只读句柄，供轮询。"""
        try:
            stamp = f"{os.getpid()}_{id(self)}"
            self.log_out_path = os.path.join(tempfile.gettempdir(), f"paolang_{stamp}_out.log")
            self.log_err_path = os.path.join(tempfile.gettempdir(), f"paolang_{stamp}_err.log")
            for p in (self.log_out_path, self.log_err_path):
                with open(p, "w", encoding="utf-8"):
                    pass
            self.log_fh_out = open(self.log_out_path, "rb")
            self.log_fh_err = open(self.log_err_path, "rb")
            self.log_pos_out = 0
            self.log_pos_err = 0
            self.log_dec_out = codecs.getincrementaldecoder("utf-8")(errors="replace")
            self.log_dec_err = codecs.getincrementaldecoder("utf-8")(errors="replace")
            return True
        except Exception as e:
            self._append_console(f"准备运行日志失败：{e}\n", "err")
            return False

    def _poll_log(self):
        if self.proc is None:
            return
        self._drain_logs()
        code = self.proc.poll()
        if code is not None:
            # 稍等片刻，让子进程把最后的输出写完
            self.root.after(150, self._finalize_proc, code)
            return
        self.root.after(60, self._poll_log)

    def _drain_logs(self):
        for fh, pos_attr, dec_attr, tag in (
            (self.log_fh_out, "log_pos_out", "log_dec_out", "out"),
            (self.log_fh_err, "log_pos_err", "log_dec_err", "err"),
        ):
            if not fh:
                continue
            try:
                fh.seek(getattr(self, pos_attr))
                while True:
                    chunk = fh.read(4096)
                    if not chunk:
                        break
                    text = getattr(self, dec_attr).decode(chunk)
                    if text:
                        self._append_console(text, tag)
                    setattr(self, pos_attr, fh.tell())
            except Exception:
                pass

    def _finalize_proc(self, code):
        self._drain_logs()
        for dec_attr, tag in (("log_dec_out", "out"), ("log_dec_err", "err")):
            dec = getattr(self, dec_attr, None)
            if dec is not None:
                try:
                    tail = dec.decode(b"", final=True)
                    if tail:
                        self._append_console(tail, tag)
                except Exception:
                    pass
        self._append_console(f"（程序结束，退出码 {code}）\n", "info")
        self.input_entry.delete(0, "end")
        self.input_entry.config(state="disabled")
        self._close_logs()
        self.proc = None
        self._set_status("已结束")

    def _close_logs(self):
        for attr in ("log_fh_out", "log_fh_err"):
            fh = getattr(self, attr, None)
            if fh:
                try:
                    fh.close()
                except Exception:
                    pass
                setattr(self, attr, None)
        for p in (getattr(self, "log_out_path", None),
                  getattr(self, "log_err_path", None)):
            if p:
                try:
                    os.remove(p)
                except Exception:
                    pass

    def send_input(self, event=None):
        if not self.proc or self.proc.poll() is not None:
            return
        s = self.input_entry.get()
        self.input_entry.delete(0, "end")
        if s:
            try:
                self.proc.stdin.write((s + "\n").encode("utf-8"))
                self.proc.stdin.flush()
            except Exception:
                pass

    def stop(self):
        if self.proc and self.proc.poll() is None:
            try:
                self.proc.terminate()
            except Exception:
                pass
            self._append_console("（程序已被停止）\n", "err")
            self._set_status("已停止")
        else:
            self._set_status("没有正在运行的程序")

    def run_selfcheck(self):
        if self.proc and self.proc.poll() is None:
            messagebox.showinfo(APP_NAME, "程序正在运行中，请先停止。")
            return
        base = self._interpreter_cmd()
        if base is None:
            return
        self._clear_console()
        self._append_console("▶ 运行泡语言内置自检…\n", "info")
        try:
            result = subprocess.run(base + ["--selfcheck"],
                                    capture_output=True, text=True,
                                    encoding="utf-8", errors="replace",
                                    timeout=60)
            self._append_console(result.stdout, "out")
            if result.stderr:
                self._append_console(result.stderr, "err")
            self._append_console(f"（自检结束，退出码 {result.returncode}）\n", "info")
        except Exception as e:
            self._append_console(f"自检失败：{e}\n", "err")
        self._set_status("自检完成")

    # ------------------------------------------------------------------
    # 控制台
    # ------------------------------------------------------------------
    def _clear_console(self):
        self.console.config(state="normal")
        self.console.delete("1.0", "end")
        self.console.config(state="disabled")

    def _append_console(self, text, tag="out"):
        self.console.config(state="normal")
        self.console.insert("end", text, tag)
        self.console.see("end")
        self.console.config(state="disabled")

    def _set_status(self, text):
        self.lbl_state.config(text=text)

    # ------------------------------------------------------------------
    # 帮助 / 退出
    # ------------------------------------------------------------------
    def show_guide(self):
        win = tk.Toplevel(self.root)
        win.title("快速上手 — 泡语言")
        win.geometry("620x520")
        txt = tk.Text(win, bg="#282C34", fg="#ABB2BF", font=("Consolas", 11),
                      padx=12, pady=12, wrap="word")
        txt.pack(fill="both", expand=True)
        guide = f"""泡语言（{LANG_NAME}）—— 语法与 Python 完全一致的中文编程语言

【基本用法】
  打印("吃了吗")
  定义 问候(名字):
      如果 名字 == "小明":
          打印("你好呀！")
      否则:
          打印("你好，" + 名字)
  问候("小明")

【快捷键】
  Ctrl+N 新建    Ctrl+O 打开    Ctrl+S 保存
  Ctrl+R 运行    Ctrl+Z 撤销

【运行】
  1. 在左侧文件列表双击 .pao 文件打开（或 文件→打开）
  2. 点击工具栏的「运行」按钮（或 Ctrl+R）
  3. 输出显示在下方的控制台里
  4. 程序用到 输入() 时，在「程序输入」框输入内容后回车

【停止】
  程序死循环或卡住时，点「停止」按钮即可强制结束。

【保存】
  扩展名用 .pao（也兼容 .zy），文件按 UTF-8 保存。
  点击「选择文件夹」可以浏览其它目录的程序。

【环境自检】
  点「自检」按钮，如果显示“全部通过，泡语言工作正常”，
  说明解释器工作正常，可以放心写程序。
"""
        txt.insert("1.0", guide)
        txt.config(state="disabled")

    def show_about(self):
        messagebox.showinfo(
            "关于", f"{APP_NAME} {VERSION}\n\n"
                    f"解释器：{LANG_NAME} {paolang.__version__}\n"
                    "无需安装 Python，双击即可使用。\n\n"
                    "一款语法与 Python 一致的中文编程语言。")

    def _on_close(self):
        if self.proc and self.proc.poll() is None:
            try:
                self.proc.terminate()
            except Exception:
                pass
        if self._confirm_discard():
            self.root.destroy()


def main():
    root = tk.Tk()
    icon = _查找图标()
    if icon:
        try:
            root.iconbitmap(icon)
        except Exception:
            pass
    PaoLangIDE(root)
    root.mainloop()


if __name__ == "__main__":
    main()
