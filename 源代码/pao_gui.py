# -*- coding: utf-8 -*-
"""泡语言图形界面模块：用中文调用 tkinter，不用写 tk.Tk() 等英文代码。

用法示例：
    窗口 = 新建窗口("我的程序")
    窗口.大小(400, 300)
    窗口.添加文本("你好，泡语言！")
    名字 = 窗口.添加输入框()
    定义 打招呼():
        弹窗提示("你好，" + 名字.取值())
    窗口.添加按钮("打招呼", 打招呼)
    窗口.开始()
"""

import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox


def _查找图标():
    """定位 泡.ico：打包后位于 _MEIPASS，源码运行时位于本文件旁边。"""
    if getattr(sys, "frozen", False):
        base = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base, "泡.ico")
    return path if os.path.exists(path) else None


# 中文颜色名 → tkinter 认识的颜色
_tk颜色表 = {
    "红": "red", "橙": "orange", "黄": "yellow", "绿": "green",
    "青": "cyan", "蓝": "blue", "紫": "purple", "粉": "pink",
    "黑": "black", "白": "white", "灰": "gray", "棕": "brown",
    "金": "gold", "银": "silver", "天蓝": "skyblue", "深蓝": "navy",
    "深绿": "darkgreen", "酒红": "crimson", "浅蓝": "lightblue",
}


def _转tk颜色(颜色):
    if isinstance(颜色, str):
        return _tk颜色表.get(颜色, 颜色)
    return 颜色

# 按钮回调里出错时（tkinter 会绕过主程序的报错处理）给出中文提示
_中文异常名表 = {
    ZeroDivisionError: "零除错误",
    ValueError: "值错误",
    TypeError: "类型错误",
    IndexError: "索引错误",
    KeyError: "键错误",
    NameError: "名称错误",
    AttributeError: "属性错误",
    FileNotFoundError: "文件未找到错误",
    PermissionError: "权限错误",
    ImportError: "导入错误",
    RuntimeError: "运行错误",
    AssertionError: "断言错误",
    OverflowError: "溢出错误",
    RecursionError: "递归错误",
    OSError: "输入输出错误",
}

_消息翻译表 = [
    ("division by zero", "除数不能为 0"),
    ("list index out of range", "列表下标超出范围"),
    ("index out of range", "下标超出范围"),
    ("is not defined", "未定义"),
    ("object has no attribute", "对象没有这个属性"),
    ("is not callable", "对象不能调用"),
    ("is not subscriptable", "不能用下标取元素"),
    ("missing required positional argument", "缺少必要的参数"),
    ("too many arguments", "参数太多了"),
    ("cannot convert", "无法转换"),
    ("can only concatenate", "只能拼接同类型"),
    ("invalid literal for int()", "无法把文字转换成整数"),
]


def _中文错误文本(e: Exception) -> str:
    名称 = _中文异常名表.get(type(e), type(e).__name__)
    消息 = str(e)
    for 英文, 中文 in _消息翻译表:
        if 英文 in 消息:
            消息 = 消息.replace(英文, 中文)
            break
    return f"错误：{名称}：{消息}"


def _包装命令(命令):
    """把按钮回调包一层：出错时弹中文提示，而不是英文回溯。"""
    if 命令 is None:
        return None

    def 执行():
        try:
            return 命令()
        except Exception as e:
            try:
                messagebox.showerror("泡语言", _中文错误文本(e))
            except Exception:
                pass
    return 执行


class 文本控件:
    """标签（显示一行文字）。"""

    def __init__(self, widget):
        self._w = widget

    def 设置(self, 文字):
        self._w.config(text=str(文字))

    def 设置文本(self, 文字):
        self.设置(文字)

    def 取值(self):
        return self._w.cget("text")

    def 获取文本(self):
        return self.取值()

    def 颜色(self, 文字色=None, 背景色=None):
        if 文字色 is not None:
            self._w.config(fg=文字色)
        if 背景色 is not None:
            self._w.config(bg=背景色)

    def 隐藏(self):
        self._w.pack_forget()

    def 显示(self):
        self._w.pack(pady=4)


class 按钮控件:
    def __init__(self, widget):
        self._w = widget

    def 设置文字(self, 文字):
        self._w.config(text=str(文字))

    def 设置文本(self, 文字):
        self.设置文字(文字)

    def 取值(self):
        return self._w.cget("text")

    def 获取文本(self):
        return self.取值()

    def 禁用(self):
        self._w.config(state="disabled")

    def 启用(self):
        self._w.config(state="normal")


class 输入框控件:
    """单行输入框。"""

    def __init__(self, widget):
        self._w = widget

    def 取值(self):
        return self._w.get()

    def 获取文本(self):
        return self.取值()

    def 设置(self, 文字):
        self._w.delete(0, "end")
        self._w.insert(0, str(文字))

    def 设置文本(self, 文字):
        self.设置(文字)

    def 清除(self):
        self._w.delete(0, "end")


class 文本框控件:
    """多行文本框。"""

    def __init__(self, widget):
        self._w = widget

    def 取值(self):
        return self._w.get("1.0", "end-1c")

    def 获取文本(self):
        return self.取值()

    def 设置(self, 文字):
        self._w.delete("1.0", "end")
        self._w.insert("1.0", str(文字))

    def 设置文本(self, 文字):
        self.设置(文字)

    def 添加(self, 文字):
        self._w.insert("end", str(文字))

    def 清除(self):
        self._w.delete("1.0", "end")


class 窗口:
    """泡语言的主窗口。"""

    def __init__(self, 标题=""):
        self._tk = tk.Tk()
        self._tk.title(str(标题))
        _图标 = _查找图标()
        if _图标:
            try:
                self._tk.iconbitmap(_图标)
            except Exception:
                pass

    def 标题(self, 文字):
        self._tk.title(str(文字))

    def 大小(self, 宽, 高):
        self._tk.geometry(f"{int(宽)}x{int(高)}")

    def 居中(self, 宽=400, 高=300):
        w, h = int(宽), int(高)
        x = (self._tk.winfo_screenwidth() - w) // 2
        y = (self._tk.winfo_screenheight() - h) // 2
        self._tk.geometry(f"{w}x{h}+{x}+{y}")

    def 添加文本(self, 文字="", 字号=12, 颜色=None):
        label = tk.Label(self._tk, text=str(文字), font=("Microsoft YaHei UI", int(字号)))
        if 颜色 is not None:
            label.config(fg=颜色)
        label.pack(pady=4)
        return 文本控件(label)

    def 添加按钮(self, 文字, 命令=None):
        btn = tk.Button(self._tk, text=str(文字), command=_包装命令(命令),
                        font=("Microsoft YaHei UI", 11))
        btn.pack(pady=4)
        return 按钮控件(btn)

    def 添加输入框(self, 宽度=20):
        entry = tk.Entry(self._tk, width=int(宽度), font=("Consolas", 12))
        entry.pack(pady=4)
        return 输入框控件(entry)

    def 添加文本框(self, 宽=40, 高=8, 只读=False):
        txt = tk.Text(self._tk, width=int(宽), height=int(高),
                      font=("Consolas", 11))
        if 只读:
            txt.config(state="disabled")
        txt.pack(pady=4)
        return 文本框控件(txt)

    def 开始(self):
        self._tk.mainloop()

    def 定时(self, 毫秒, 函数):
        """过多少毫秒后执行一个函数（如 定时(3000, 窗口.关闭) 3 秒后自动关窗）。"""
        self._tk.after(int(毫秒), 函数)

    def 关闭(self):
        self._tk.destroy()

    def 属性(self, 名称, 值=None):
        """设置或读取窗口属性。不传 值 时读取。
        例：属性("-fullscreen", 真) 全屏、属性("-topmost", 真) 置顶、
        属性("-alpha", 0.5) 半透明、属性("-toolwindow", 真) 无任务栏按钮。"""
        if 值 is None:
            return self._tk.attributes(名称)
        return self._tk.attributes(名称, 值)

    def 获取属性(self, 名称):
        """读取窗口属性。例：获取属性("-alpha")"""
        return self._tk.attributes(名称)

    def 配置(self, 名称=None, 值=None, **选项):
        """设置窗口外观选项（窗口本身支持的选项）。中文选项名自动翻译：
        背景色→bg 宽度→width 高度→height 边框→bd 光标→cursor。
        例：配置("背景色", "#000000")、配置("bg", "black")、配置(背景色="黑色")。
        注意：前景色/字体 是控件的属性，请用控件的 颜色()/设置() 方法。"""
        翻译 = {"背景色": "bg", "宽度": "width", "高度": "height",
                "边框": "bd", "光标": "cursor"}
        try:
            if 名称 is not None and 值 is not None:
                self._tk.configure(**{翻译.get(名称, 名称): _转tk颜色(值)})
            else:
                self._tk.configure(**{翻译.get(k, k): v for k, v in 选项.items()})
        except tk.TclError as e:
            raise RuntimeError(f"窗口配置失败：{e}（窗口本身只支持 背景色/宽度/高度/边框/光标 等选项）") from None

    def 全屏(self, 是否=True):
        """全屏显示窗口。全屏(假) 退出全屏。"""
        self._tk.attributes("-fullscreen", bool(是否))

    def 置顶(self, 是否=True):
        """窗口总是显示在最前面。置顶(假) 取消。"""
        self._tk.attributes("-topmost", bool(是否))

    def 透明度(self, 值):
        """窗口整体透明度：0.0（完全透明）~ 1.0（不透明）。例：透明度(0.5)"""
        self._tk.attributes("-alpha", float(值))

    def 最小大小(self, 宽, 高):
        """设置窗口最小尺寸。"""
        self._tk.minsize(int(宽), int(高))

    def 最大大小(self, 宽, 高):
        """设置窗口最大尺寸。"""
        self._tk.maxsize(int(宽), int(高))

    def 可调整(self, 水平=True, 垂直=True):
        """是否允许拖拽调整窗口大小。例：可调整(假) 锁定大小。"""
        self._tk.resizable(bool(水平), bool(垂直))

    def 图标化(self):
        """最小化到任务栏。"""
        self._tk.iconify()

    def 恢复(self):
        """从最小化恢复显示。"""
        self._tk.deiconify()

    def 隐藏(self):
        """隐藏窗口（任务栏也消失）。"""
        self._tk.withdraw()

    def 显示(self):
        """重新显示被隐藏的窗口。"""
        self._tk.deiconify()

    def 置前(self):
        """把窗口放到所有窗口最前面。"""
        self._tk.lift()

    def 聚焦(self):
        """强制让窗口获得输入焦点。"""
        self._tk.focus_force()


def 弹窗提示(文字, 标题="泡语言"):
    messagebox.showinfo(str(标题), str(文字))


def 弹窗警告(文字, 标题="泡语言"):
    messagebox.showwarning(str(标题), str(文字))


def 弹窗错误(文字, 标题="泡语言"):
    messagebox.showerror(str(标题), str(文字))


def 弹窗确认(文字, 标题="泡语言"):
    """询问“是/否”，返回 真 或 假。"""
    return messagebox.askyesno(str(标题), str(文字))


def 选择文件(标题="选择文件", 类型=None):
    """打开文件选择框，返回完整路径；取消返回空字符串。"""
    if 类型:
        kinds = [(str(t[0]), str(t[1])) for t in 类型]
    else:
        kinds = [("所有文件", "*.*")]
    return filedialog.askopenfilename(title=str(标题), filetypes=kinds) or ""


def 保存文件(标题="保存文件", 类型=None):
    kinds = [(str(t[0]), str(t[1])) for t in 类型] if 类型 else [("所有文件", "*.*")]
    return filedialog.asksaveasfilename(title=str(标题), filetypes=kinds) or ""


def 选择文件夹(标题="选择文件夹"):
    return filedialog.askdirectory(title=str(标题)) or ""
