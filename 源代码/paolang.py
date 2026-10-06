#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
泡语言（PaoLang）解释器 —— 语法与 Python 完全一致的中文编程语言。

    打印("吃了吗")            ->  print("吃了吗")
    定义 阶乘(数字): ...       ->  def 阶乘(数字): ...

用法：
    泡语言.exe 程序.pao          运行泡语言程序
    泡语言.exe --run 程序.pao    运行程序（供编辑器调用）
    泡语言.exe --repl            进入交互模式
    泡语言.exe --selfcheck       运行内置自检
    泡语言.exe --help            查看帮助
"""

import builtins as _builtins
import importlib.abc
import importlib.util
import io
import os
import random as _random
import sys
import time as _time
import tokenize
import traceback

LANG_NAME = "泡语言"
__version__ = "1.9.0"


class 泡语言错误(Exception):
    """泡语言面向用户的中文错误。"""


# 常见异常类型 → 中文名
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
    SyntaxError: "语法错误",
    IndentationError: "缩进错误",
    RuntimeError: "运行错误",
    AssertionError: "断言错误",
    StopIteration: "停止迭代",
    EOFError: "文件结束错误",
    OverflowError: "溢出错误",
    MemoryError: "内存错误",
    RecursionError: "递归错误",
    KeyboardInterrupt: "键盘中断",
    OSError: "输入输出错误",
}


def _中文异常名(异常类型) -> str:
    return _中文异常名表.get(异常类型, 异常类型.__name__)


# 常见英文错误信息 → 中文提示（按子串匹配，靠前的优先）
_消息翻译表 = [
    ("division by zero", "除数不能为 0"),
    ("integer division or modulo by zero", "整数除法或取余的除数不能为 0"),
    ("list index out of range", "列表下标超出范围"),
    ("tuple index out of range", "元组下标超出范围"),
    ("string index out of range", "字符串下标超出范围"),
    ("index out of range", "下标超出范围"),
    ("is not defined", "未定义"),
    ("cannot import name", "无法导入"),
    ("unsupported operand type(s)", "不支持的操作数类型"),
    ("object is not callable", "对象不能调用（可能少写了运算符或括号）"),
    ("object is not subscriptable", "对象不能用下标取元素"),
    ("is not subscriptable", "不能用下标取元素"),
    ("missing required positional argument", "缺少必要的参数"),
    ("too many arguments", "参数太多了"),
    ("takes 1 positional argument", "参数数量不对（只需要 1 个参数）"),
    ("takes 2 positional arguments", "参数数量不对（只需要 2 个参数）"),
    ("takes 3 positional arguments", "参数数量不对（只需要 3 个参数）"),
    ("invalid literal for int()", "无法把文字转换成整数"),
    ("invalid literal for float()", "无法把文字转换成小数"),
    ("cannot convert", "无法转换"),
    ("object has no attribute", "没有这个属性"),
    ("can only concatenate", "只能拼接同类型"),
    ("must be str, not", "需要字符串，但给的不是"),
    ("must be int, not", "需要整数，但给的不是"),
    ("must be real number, not", "需要数字，但给的不是"),
    ("keyword can't be an expression", "关键字不能是表达式"),
    ("unexpected indent", "意外的缩进"),
    ("unindent does not match", "缩进与上一行不匹配"),
    ("expected an indented block", "这里需要缩进"),
    ("'return' outside function", "返回 用在了函数外面"),
    ("'break' outside loop", "中断 用在了循环外面"),
    ("'continue' not properly in loop", "继续 用在了循环外面"),
    ("no closing quote", "字符串缺少结束引号"),
    ("cannot assign to", "不能给这个赋值"),
    ("referenced before assignment", "在赋值前就被使用了"),
    ("invalid syntax", "语法不合法"),
]


def _翻译错误消息(e: Exception) -> str:
    原文 = str(e)
    for 英文, 中文 in _消息翻译表:
        if 英文 in 原文:
            return 原文.replace(英文, 中文)
    return 原文


# 括号配对表：闭合符号 -> 对应开启符号；开启符号 -> 对应闭合符号
_开括号 = {")": "(", "]": "[", "}": "{"}
_闭括号 = {"(": ")", "[": "]", "{": "}"}


def _找未闭合括号(source: str):
    """扫描已归一化的源码，找出未闭合的括号。

    跳过字符串与注释；返回 (开启符号, 行号)，找不到返回 None。
    """
    stack = []  # [(符号, 行号)]
    i, n = 0, len(source)
    state = None  # None | "'" | '"' | "'''" | '"""'
    while i < n:
        ch = source[i]
        if state is None:
            if ch in ('"', "'"):
                if source.startswith(ch * 3, i):
                    state = ch * 3
                    i += 3
                    continue
                state = ch
                i += 1
                continue
            if ch == "#":
                j = source.find("\n", i)
                if j < 0:
                    break
                i = j
                continue
            if ch in "([{":
                stack.append((ch, source.count("\n", 0, i) + 1))
                i += 1
                continue
            if ch in ")]}":
                if stack and stack[-1][0] == _开括号[ch]:
                    stack.pop()
                else:
                    return (ch, source.count("\n", 0, i) + 1)
                i += 1
                continue
            i += 1
        else:
            if ch == "\\":
                i += 2
                continue
            if state in ("'''", '"""'):
                if source.startswith(state, i):
                    state = None
                    i += 3
                    continue
            elif ch == state:
                state = None
                i += 1
                continue
            i += 1
    if stack:
        return stack[-1]
    return None

# ---------------------------------------------------------------------------
# 一、语法关键词对照表
#    在词法层面做“整词替换”：只替换被识别为标识符的完整中文词，
#    不影响字符串、注释以及含中文的变量名（例如“打印机”不会被改坏）。
# ---------------------------------------------------------------------------
KEYWORDS = {
    # 语句结构
    "定义": "def",
    "类": "class",
    "返回": "return",
    "如果": "if",
    "否则如果": "elif",
    "否则": "else",
    "对于": "for",
    "当": "while",
    "在": "in",
    "中断": "break",
    "继续": "continue",
    "通过": "pass",
    "尝试": "try",
    "除了": "except",
    "最终": "finally",
    "抛出": "raise",
    "导入": "import",
    "从": "from",
    "为": "as",
    "使用": "with",
    "延迟": "yield",
    "删除": "del",
    "全局": "global",
    "非本地": "nonlocal",
    "断言": "assert",
    "等待": "await",
    "异步": "async",
    # 字面量
    "真": "True",
    "假": "False",
    "无": "None",
    # 逻辑 / 比较
    "和": "and",
    "且": "and",
    "或": "or",
    "非": "not",
    "是": "is",
    "不是": "is not",
    "不在": "not in",
}

# 匹配/情况（match/case）需要 Python 3.10+ 才可用
if sys.version_info >= (3, 10):
    KEYWORDS["匹配"] = "match"
    KEYWORDS["情况"] = "case"

def _pao_input(prompt=""):
    """泡语言的“输入”函数。

    自带提示语并强制刷新输出缓冲：在控制台/编辑器等管道环境下，
    提示文字（如 输入("你好：") 的“你好：”）会立即显示，不会等到
    程序结束才出现。读到文件结束（EOF）时抛出 文件结束错误。
    """
    if prompt:
        sys.stdout.write(str(prompt))
        sys.stdout.flush()
    line = sys.stdin.readline()
    if not line:
        raise EOFError("EOF when reading a line")
    return line.rstrip("\r\n")


def _pao_help(obj=None):
    """泡语言的“帮助”函数：不依赖 site 注入的内置 help（打包环境里不存在）。"""
    if obj is None:
        print("泡语言内置函数：打印 输入 长度 范围 类型 整数 浮点数 字符串 "
              "列表 元组 字典 集合 布尔 枚举 排序 最大值 最小值 绝对值 求和 打开 退出 等。"
              "详细说明见 使用说明.md")
    elif hasattr(obj, "__doc__") and obj.__doc__:
        print(obj.__doc__)
    else:
        print(repr(obj))


class _TeeWriter:
    """同时写往真实流与日志文件的输出包装。

    编辑器用 --run-log 启动解释器时，程序的所有输出（包括 输入() 的提示文字）
    除了写往 stdout/stderr，还会逐次刷新地追加到日志文件里——文件写入不受
    管道缓冲/拦截影响，编辑器轮询文件即可实现“提示文字立刻显示”。
    """

    def __init__(self, real, logf):
        self.real = real
        self.logf = logf

    def write(self, s):
        try:
            self.logf.write(s)
            self.logf.flush()
        except Exception:
            pass
        return self.real.write(s)

    def flush(self):
        try:
            self.logf.flush()
        except Exception:
            pass
        try:
            self.real.flush()
        except Exception:
            pass

    def writable(self):
        return True

    def isatty(self):
        try:
            return self.real.isatty()
        except Exception:
            return False

    @property
    def encoding(self):
        try:
            return self.real.encoding
        except Exception:
            return "utf-8"


def _install_run_log(out_path: str, err_path: str) -> None:
    """把 stdout/stderr 包装成“真流 + 日志文件”双写。"""
    try:
        fout = open(out_path, "a", encoding="utf-8", errors="replace")
        ferr = open(err_path, "a", encoding="utf-8", errors="replace")
        sys.stdout = _TeeWriter(sys.stdout, fout)
        sys.stderr = _TeeWriter(sys.stderr, ferr)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# 中文代理：键盘.xxx / 海龟.xxx 只能访问中文功能，写英文名会得到中文错误
# ---------------------------------------------------------------------------
class _中文代理:
    def __init__(self, 模块名, 名称):
        self._模块名 = 模块名
        self._名称 = 名称

    def __getattr__(self, 属性):
        if 属性.startswith("_"):
            raise AttributeError(属性)
        模块 = __import__(self._模块名)
        值 = vars(模块).get(属性)
        if 值 is not None:
            return 值
        raise 泡语言错误(
            f"{self._名称} 里没有中文功能「{属性}」。泡语言全部用中文，"
            f"不写英文名；需要这个功能就告诉我，我来加中文名。"
        )


# ---------------------------------------------------------------------------
# 二、内置函数对照表（以“中文名 -> Python 对象”的方式注入运行环境，
#     源码里保留中文名，报错信息更直观，也允许用户自行覆盖）
#     注意：不用 exit/help 等 site 注入的“伪内置函数”，打包后不可用。
# ---------------------------------------------------------------------------
BUILTIN_ALIASES = {
    "打印": print,
    "输入": _pao_input,
    "长度": len,
    "范围": range,
    "类型": type,
    "整数": int,
    "浮点数": float,
    "字符串": str,
    "列表": list,
    "元组": tuple,
    "字典": dict,
    "集合": set,
    "布尔": bool,
    "字节": bytes,
    "字节数组": bytearray,
    "复数": complex,
    "枚举": enumerate,
    "排序": sorted,
    "反转": reversed,
    "最大值": max,
    "最小值": min,
    "绝对值": abs,
    "求和": sum,
    "幂": pow,
    "四舍五入": round,
    "除余": divmod,
    "打开": open,
    "退出": sys.exit,   # 用 sys.exit 而不是内置 exit（site 伪内置，打包环境不存在）
    "帮助": _pao_help,
    "迭代": iter,
    "下一个": next,
    "切片": slice,
    "格式": format,
    "映射": map,
    "过滤": filter,
    "压缩": zip,
    "任意": any,
    "全部": all,
    "哈希": hash,
    "对象": object,
    "目录": dir,
    "调用": callable,
    "本地变量": locals,
    "全局变量": globals,
    "获取属性": getattr,
    "设置属性": setattr,
    "拥有属性": hasattr,
    # 随机数（内部用 Python 标准库 random 实现）
    "随机整数": _random.randint,   # 随机整数(最小, 最大)，两端都包含
    "随机小数": _random.random,    # 随机小数()，0 到 1 之间
    "随机选择": _random.choice,    # 随机选择(序列)，从序列里随机挑一个
    "随机打乱": _random.shuffle,   # 随机打乱(序列)，原地打乱列表
    # 时间（无需 导入 time）
    "暂停": _time.sleep,           # 暂停(秒)，如 暂停(0.5)；注意"等待"是关键字不能用
    "当前时间": lambda: _time.strftime("%Y-%m-%d %H:%M:%S"),
    "时间戳": _time.time,          # 时间戳()，从 1970 年 1 月 1 日以来的秒数
    # 键盘/海龟 中文入口：键盘.阻止按键("a")、海龟.前进(100)，写英文名会提示中文错误
    "键盘": _中文代理("pao_keyboard", "键盘"),
    "海龟": _中文代理("pao_turtle", "海龟"),
}


def _gui_窗口(标题=""):
    """懒加载图形界面模块（避免解释器启动时加载 tkinter）。"""
    import pao_gui
    return pao_gui.窗口(标题)


def _gui_弹窗提示(文字, 标题="泡语言"):
    import pao_gui
    return pao_gui.弹窗提示(文字, 标题)


def _gui_弹窗警告(文字, 标题="泡语言"):
    import pao_gui
    return pao_gui.弹窗警告(文字, 标题)


def _gui_弹窗错误(文字, 标题="泡语言"):
    import pao_gui
    return pao_gui.弹窗错误(文字, 标题)


def _gui_弹窗确认(文字, 标题="泡语言"):
    import pao_gui
    return pao_gui.弹窗确认(文字, 标题)


def _gui_选择文件(标题="选择文件", 类型=None):
    import pao_gui
    return pao_gui.选择文件(标题, 类型)


def _gui_保存文件(标题="保存文件", 类型=None):
    import pao_gui
    return pao_gui.保存文件(标题, 类型)


def _gui_选择文件夹(标题="选择文件夹"):
    import pao_gui
    return pao_gui.选择文件夹(标题)


# 图形界面内置函数（懒加载，用到才导入 tkinter）
GUI_ALIASES = {
    "新建窗口": _gui_窗口,
    "弹窗提示": _gui_弹窗提示,
    "弹窗警告": _gui_弹窗警告,
    "弹窗错误": _gui_弹窗错误,
    "弹窗确认": _gui_弹窗确认,
    "选择文件": _gui_选择文件,
    "保存文件": _gui_保存文件,
    "选择文件夹": _gui_选择文件夹,
}


# 海龟画图内置函数（懒加载，用到才导入 turtle）
def _海龟调用(名字):
    def 调用(*参数, **关键字):
        import pao_turtle
        return getattr(pao_turtle, 名字)(*参数, **关键字)
    return 调用


TURTLE_ALIASES = {
    名字: _海龟调用(名字) for 名字 in (
        "前进", "后退", "左转", "右转", "画圆", "画点", "开始填充", "结束填充",
        "抬起笔", "落下笔", "隐藏海龟", "显示海龟", "去", "设置速度", "设置颜色",
        "设置画笔粗细", "设置背景色", "重置", "清屏", "设置方向", "方向", "位置",
        "横坐标", "纵坐标", "距离", "朝向", "海龟大小", "倾斜", "复制", "撤销",
        "设横坐标", "设纵坐标", "设置位置", "回家", "传送", "图章", "清除图章",
        "清除所有图章", "是否画线", "笔状态", "笔颜色", "填充颜色", "是否填充中",
        "颜色模式", "开始记录多边形", "结束记录多边形", "获得多边形",
        "设置撤销缓冲区", "撤销记录条数", "形状", "注册形状", "添加形状", "现有形状",
        "缩放模式", "形状变换", "剪切因子", "倾斜角度", "是否可见",
        "重置屏幕", "清空屏幕", "屏幕尺寸", "设置世界坐标", "轨迹", "更新", "动画延迟",
        "开始监听", "注册按键", "注册按下按键", "注册松开按键", "注册点击",
        "注册屏幕点击", "注册拖拽", "注册松开", "定时器", "输入文字", "输入数字",
        "窗口标题", "窗口设置", "窗口宽度", "窗口高度", "画布", "画笔对象",
        "屏幕对象", "全部海龟", "模式", "角度制", "弧度制", "写字",
        "完成", "关闭",
    )
}


# 键盘检测内置函数（懒加载，用到才导入 keyboard）—— keyboard 完整 API
def _键盘调用(名字):
    def 调用(*参数, **关键字):
        import pao_keyboard
        return getattr(pao_keyboard, 名字)(*参数, **关键字)
    return 调用


KEYBOARD_ALIASES = {
    名字: _键盘调用(名字) for 名字 in (
        "按键按下", "等待按键", "读取按键", "读取快捷键", "读取事件",
        "按下", "松开", "发送按键", "发送", "键入",
        "注册快捷键", "移除快捷键", "注册热键", "注销快捷键", "清除快捷键",
        "清除所有快捷键", "移除所有快捷键", "取消所有快捷键", "注销所有快捷键",
        "阻止按键", "解除阻止", "重新映射按键", "取消重新映射按键",
        "重新映射快捷键", "取消重新映射快捷键",
        "注册按下回调", "注册松开回调", "注册按键按下回调", "注册按键松开回调",
        "挂接", "取消挂接", "取消所有挂接", "挂接按键", "取消挂接按键",
        "开始记录", "停止记录", "记录", "回放", "重放",
        "添加缩写", "移除缩写", "注册缩写",
        "添加词语监听", "移除词语监听", "注册词语监听", "获得输入文字",
        "解析快捷键", "解析快捷键组合", "规范化", "规范化名称",
        "按键转扫描码", "全部修饰键", "单侧修饰键", "是否修饰键", "获得快捷键名",
        "延时调用", "暂存状态", "恢复状态", "恢复修饰键", "版本",
    )
}


# 常用异常的中文别名
EXCEPTION_ALIASES = {
    "异常": Exception,
    "值错误": ValueError,
    "类型错误": TypeError,
    "索引错误": IndexError,
    "键错误": KeyError,
    "零除错误": ZeroDivisionError,
    "文件未找到错误": FileNotFoundError,
    "属性错误": AttributeError,
    "名称错误": NameError,
    "语法错误": SyntaxError,
    "运行错误": RuntimeError,
    "停止迭代": StopIteration,
    "断言错误": AssertionError,
    "溢出错误": OverflowError,
    "内存错误": MemoryError,
    "递归错误": RecursionError,
    "文件结束错误": EOFError,
    "键盘中断": KeyboardInterrupt,
    "输入输出错误": OSError,
}

# 泡语言程序能看到的 Python 内置对象。
# 只暴露没有中文别名的“安全”内置项；有中文别名的（打印/输入/长度/范围/
# 打开/退出/…）以及危险或开发用内置项（eval/exec/compile/breakpoint 等）
# 一律不暴露——这样用户误写英文 input/print 会立即得到清晰报错，
# 而不是悄悄调用到 Python 原生实现（如 input() 会永久阻塞等待输入）。
SAFE_BUILTINS = {}
for _safe_name in (
    # 类/类机制与面向对象
    "object", "super", "property", "classmethod", "staticmethod",
    "isinstance", "issubclass", "id", "vars",
    # 类型（无中文别名者）
    "frozenset", "memoryview",
    # 工具函数
    "ascii", "bin", "hex", "oct", "repr", "delattr",
):
    SAFE_BUILTINS[_safe_name] = getattr(_builtins, _safe_name)
# 解释器内部机制必需项（import / class / assert 语句依赖它们）
SAFE_BUILTINS["__import__"] = _builtins.__import__
SAFE_BUILTINS["__build_class__"] = _builtins.__build_class__
SAFE_BUILTINS["__debug__"] = True

# ---------------------------------------------------------------------------
# 三、全角标点对照表（只在“非字符串内”的位置生效，字符串里的中文标点不受影响）
# ---------------------------------------------------------------------------
FULLWIDTH_MAP = {
    "：": ":",
    "，": ",",
    "；": ";",
    "（": "(",
    "）": ")",
    "【": "[",
    "】": "]",
    "｛": "{",
    "｝": "}",
    "＝": "=",
    "！": "!",
    "？": "?",
    "＋": "+",
    "－": "-",
    "＊": "*",
    "／": "/",
    "％": "%",
    "＜": "<",
    "＞": ">",
    "≤": "<=",
    "≥": ">=",
    "≠": "!=",
    "“": '"',
    "”": '"',
    "‘": "'",
    "’": "'",
    "＃": "#",
}


def _normalize_fullwidth(source: str) -> str:
    """把代码中“字符串与注释之外”的全角标点替换为半角。

    用简单的状态机跟踪字符串（含三引号）与注释：字符串内的中文标点
    原样保留（例如 "他说：“你好”" 不会被改），注释里的内容也不动。
    Python 3.12+ 会把全角符号并入标识符词，因此必须在分词前处理。
    """
    out = []
    i, n = 0, len(source)
    state = None  # None | "'" | '"' | "'''" | '"""'
    while i < n:
        ch = source[i]
        if state is None:
            if ch in ('"', "'"):
                if source.startswith(ch * 3, i):
                    state = ch * 3
                    out.append(ch * 3)
                    i += 3
                    continue
                state = ch
                out.append(ch)
                i += 1
                continue
            if ch == "#":
                j = source.find("\n", i)
                if j == -1:
                    out.append(source[i:])
                    break
                out.append(source[i:j])
                i = j
                continue
            out.append(FULLWIDTH_MAP.get(ch, ch))
            i += 1
        else:
            if ch == "\\":
                out.append(source[i:i + 2])
                i += 2
                continue
            if state in ("'''", '"""'):
                if source.startswith(state, i):
                    out.append(state)
                    i += 3
                    state = None
                    continue
            elif ch == state:
                state = None
            out.append(ch)
            i += 1
    return "".join(out)


def translate(source: str) -> str:
    """把泡语言源码翻译成等价的标准Python源码。

    步骤：先把代码（字符串、注释之外）的全角标点归一化为半角；
    再用 Python 自带的 tokenize 把源码切成词法单元，只对“完整的
    标识符词”做替换；替换时按 token 的起止位置重建源码，原样保留
    词间空格、缩进与换行。字符串、注释、数字、运算符不受影响，
    含中文的变量名/函数名也完全不受影响。
    """
    source = _normalize_fullwidth(source)

    # 先算每一行的起始偏移量，用于把 (行, 列) 换算成绝对下标
    offsets = []
    total = 0
    for ln in source.splitlines(keepends=True):
        offsets.append(total)
        total += len(ln)

    try:
        tokens = tokenize.generate_tokens(io.StringIO(source).readline)
    except (tokenize.TokenError, IndentationError, SyntaxError):
        # 词法解析失败时原样返回，让编译阶段给出报错
        return source

    out = []
    prev_end = 0
    try:
        for tok in tokens:
            ttype, tstr = tok.type, tok.string
            if ttype == tokenize.ENCODING:
                continue
            start_row = tok.start[0] - 1
            if start_row >= len(offsets):  # ENDMARKER 行号可能多出一行
                start_row = len(offsets) - 1
            start = offsets[start_row] + tok.start[1]
            end_row = tok.end[0] - 1
            if end_row >= len(offsets):
                end_row = len(offsets) - 1
            end = offsets[end_row] + tok.end[1]
            if start < prev_end:  # 防御：位置重叠时避免重复输出
                start = prev_end
            if end < start:       # 防御：防止 prev_end 回退导致内容重复
                end = start
            out.append(source[prev_end:start])  # 词与词之间的原始空白
            prev_end = end
            if ttype == tokenize.NAME and tstr in KEYWORDS:
                out.append(KEYWORDS[tstr])
            elif ttype == tokenize.ERRORTOKEN and tstr in FULLWIDTH_MAP:
                out.append(FULLWIDTH_MAP[tstr])
            else:
                out.append(tstr)
    except tokenize.TokenError as e:
        # 词法错误（如括号/引号未闭合）→ 给出中文定位，不再漏英文回溯
        消息 = e.args[0] if e.args else "词法错误"
        行 = e.args[1][0] if len(e.args) > 1 and e.args[1] else None
        if "EOF in multi-line statement" in 消息:
            未闭合 = _找未闭合括号(source)
            if 未闭合:
                raise 泡语言错误(
                    f"语法错误：第 {未闭合[1]} 行的 “{未闭合[0]}” 没有对应的"
                    f"“{_闭括号[未闭合[0]]}”——少写了一个右括号/右中括号/右花括号"
                ) from None
            raise 泡语言错误(
                f"语法错误：第 {行} 行附近有未闭合的括号或引号（文件在语句中间就结束了）"
            ) from None
        raise 泡语言错误(f"语法错误：第 {行} 行：{消息}") from None
    except IndentationError as e:
        raise 泡语言错误(f"缩进错误：第 {e.lineno} 行：{_翻译错误消息(e)}") from None
    except SyntaxError as e:
        raise 泡语言错误(f"语法错误：第 {e.lineno} 行：{_翻译错误消息(e)}") from None
    out.append(source[prev_end:])
    return "".join(out)


def make_globals() -> dict:
    """构造泡语言程序的全局运行环境（只暴露受限内置，防英文名泄漏）。"""
    g = {"__name__": "__main__", "__builtins__": SAFE_BUILTINS}
    g.update(BUILTIN_ALIASES)
    g.update(GUI_ALIASES)
    g.update(TURTLE_ALIASES)
    g.update(KEYBOARD_ALIASES)
    g.update(EXCEPTION_ALIASES)
    return g


# ---------------------------------------------------------------------------
# 自定义库：`导入 我的库` 会加载同目录（或 sys.path 里）的 我的库.pao
# ---------------------------------------------------------------------------
class _泡语言查找器(importlib.abc.MetaPathFinder):
    """兜底查找器：标准库找不到的名字，去 sys.path 里找同名 .pao 文件。"""

    def find_spec(self, fullname, path=None, target=None):
        if "." in fullname:  # 只支持顶层库（如 导入 我的库）
            return None
        for 基 in list(sys.path) + [os.getcwd()]:
            if not 基:
                基 = "."
            库路径 = os.path.join(基, fullname + ".pao")
            if os.path.isfile(库路径):
                return importlib.util.spec_from_file_location(
                    fullname, 库路径, loader=_泡语言加载器(库路径))
        return None


class _泡语言加载器(importlib.abc.Loader):
    """把 .pao 库文件翻译成 Python 并当作模块加载。"""

    def __init__(self, 路径):
        self._路径 = 路径

    def create_module(self, spec):
        return None  # 用默认模块对象

    def exec_module(self, module):
        with open(self._路径, "r", encoding="utf-8") as f:
            源码 = f.read()
        代码 = translate(源码)  # 库文件里也可以写中文语法
        g = make_globals()
        g["__name__"] = module.__name__  # 库里能看到 __name__，且不等于 __main__
        module.__dict__.update(g)
        exec(compile(代码, self._路径, "exec"), module.__dict__)


def _装keyboard():
    """键盘按键检测（keyboard 库，随解释器一起打包）。"""
    import keyboard  # noqa: F401  (让 PyInstaller 把 keyboard 打进去)
    return keyboard


if not any(isinstance(f, _泡语言查找器) for f in sys.meta_path):
    sys.meta_path.append(_泡语言查找器())


def run_source(source: str, filename: str = "<泡语言程序>", globals_dict: dict = None) -> None:
    """翻译并执行一段泡语言源码。"""
    code = translate(source)
    g = globals_dict if globals_dict is not None else make_globals()
    try:
        compiled = compile(code, filename, "exec")
    except SyntaxError as e:
        raise 泡语言错误(f"语法错误：第 {e.lineno} 行：{_翻译错误消息(e)}") from None
    exec(compiled, g)


def run_file(path: str) -> None:
    """运行一个 .pao 泡语言程序文件（也兼容 .zy）。"""
    # 把程序所在文件夹加进搜索路径，让 `导入 我的库` 能找到旁边的 .pao 库文件
    程序目录 = os.path.dirname(os.path.abspath(path))
    if 程序目录 not in sys.path:
        sys.path.insert(0, 程序目录)
    with open(path, "r", encoding="utf-8") as f:
        src = f.read()
    run_source(src, filename=path)


# ---------------------------------------------------------------------------
# 四、交互模式（REPL）
# ---------------------------------------------------------------------------
def _exec_chunk(lines: list, g: dict) -> None:
    src = "\n".join(lines)
    code = translate(src)
    # 交互模式优先按 single 编译：单独的表达式会自动显示结果
    # （和 Python 自带的 REPL 行为一致）
    try:
        compiled = compile(code, "<交互>", "single")
        exec(compiled, g)
        return
    except SyntaxError:
        pass
    # 多语句/复合语句整体则按普通语句执行
    try:
        compiled = compile(code, "<交互>", "exec")
        exec(compiled, g)
    except SystemExit:
        raise
    except NameError as e:
        print(f"名称错误：{e}")
        print("提示：泡语言内置函数/类型/异常都要用中文名（如 输入、打印、长度、值错误）。输入 帮助() 查看全部。")
    except 泡语言错误 as e:
        print(f"错误：{e}")
    except Exception as e:
        print(f"错误：{_中文异常名(type(e))}：{_翻译错误消息(e)}")


def _finish_repl(lines: list, g: dict) -> None:
    if lines:
        _exec_chunk(lines, g)
    print("再见！")


def repl() -> None:
    g = make_globals()
    print(f"{LANG_NAME} {__version__} 交互模式 —— 输入「退出()」或 Ctrl+C 结束")
    print("多行代码请连续输入，最后留一个空行执行。")
    lines = []
    while True:
        try:
            line = input("… " if lines else "泡> ")
        except (EOFError, KeyboardInterrupt):
            _finish_repl(lines, g)
            return
        stripped = line.strip()
        if not stripped:
            if lines:
                _exec_chunk(lines, g)
                lines = []
            continue
        if stripped in ("退出", "退出()", "quit", "exit"):
            _finish_repl(lines, g)
            return
        lines.append(line)


# ---------------------------------------------------------------------------
# 五、内置自检
# ---------------------------------------------------------------------------
SELFCHECK = """\
# 泡语言内置自检程序
断言(1 + 1 == 2)
断言(长度([1, 2, 3]) == 3)
断言(整数("42") == 42)
断言(类型(真) 是 布尔)
断言(真 和 假 == 假)
断言(非 假)
断言(假 不是 真)
断言(3 不在 [1, 2])
断言(2 在 [1, 2])
断言(最大值([3, 9, 5]) == 9)
断言(求和(范围(1, 6)) == 15)
断言(字符串(3.14) == "3.14")
断言 3 * 7 == 21, "带信息的断言要用不带括号的写法"

定义 阶乘(数字):
    如果 数字 <= 1:
        返回 1
    返回 数字 * 阶乘(数字 - 1)
断言(阶乘(5) == 120)

断言([x * 2 对于 x 在 范围(4)] == [0, 2, 4, 6])

尝试:
    1 / 0
除了 零除错误:
    通过

断言(1 <= 随机整数(1, 100) <= 100)
断言(0 <= 随机小数() < 1)
断言(随机选择([1, 2, 3]) 在 [1, 2, 3])

断言(时间戳() > 1000000000)
断言(长度(当前时间()) == 19)

打印（"全角括号冒号小于号：2 ＜ 3"）
如果 1 ＜ 2 且 3 ≥ 3：
    打印（"全角标点判定通过"）

打印("全部通过，泡语言工作正常")
"""


# ---------------------------------------------------------------------------
# 六、入口
# ---------------------------------------------------------------------------
HELP = f"""\
{LANG_NAME} {__version__} —— 语法与 Python 一致的中文编程语言

用法：
    泡语言.exe 程序.pao          运行泡语言程序文件
    泡语言.exe --run 程序.pao    运行程序（编辑器内部调用）
    泡语言.exe --repl            进入交互模式
    泡语言.exe --selfcheck       运行内置自检
    泡语言.exe --version         查看版本
    泡语言.exe --help            查看帮助

示例（演示.pao）：
    打印("吃了吗")
    定义 问候(名字):
        打印("你好，" + 名字)
    问候("小明")

支持的中文关键词包括：
    定义 类 返回 如果 否则如果 否则 对于 当 在 中断 继续 通过
    尝试 除了 最终 抛出 导入 从 为 使用 延迟 删除 全局 断言
    真 假 无 和 或 非 是 不是 不在 等待 异步 匹配 情况

支持的中文内置函数包括：
    打印 输入 长度 范围 类型 整数 浮点数 字符串 列表 元组 字典
    集合 布尔 枚举 排序 反转 最大值 最小值 绝对值 求和 打开 退出

同时支持全角标点：： ， ； （ ） ＜ ＞ ≤ ≥ ≠ 等
"""


def main(argv=None) -> int:
    argv = list(sys.argv[1:]) if argv is None else argv

    # Windows 控制台/管道编码兜底，避免中文乱码
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    # --run-log 输出日志 错误日志：供编辑器实时轮询（必须放在 --run 之前）
    log_out = log_err = None
    if argv and argv[0] == "--run-log":
        if len(argv) < 3:
            print("用法：泡语言.exe --run-log 输出日志 错误日志 --run 程序.pao",
                  file=sys.stderr)
            return 2
        log_out, log_err = argv[1], argv[2]
        argv = argv[3:]

    if not argv:
        repl()
        return 0

    arg = argv[0]
    if arg in ("-h", "--help", "/?"):
        print(HELP)
        return 0
    if arg in ("-v", "--version"):
        print(f"{LANG_NAME} {__version__}")
        return 0
    if arg == "--selfcheck":
        try:
            run_source(SELFCHECK, filename="<自检>")
        except Exception:
            traceback.print_exc()
            return 1
        return 0
    if arg == "--repl":
        repl()
        return 0
    if arg == "--run":
        if len(argv) < 2:
            print("缺少程序文件名：泡语言.exe --run 程序.pao", file=sys.stderr)
            return 2
        arg = argv[1]
        if log_out or log_err:  # 编辑器模式：输出同时写日志文件供轮询
            _install_run_log(log_out, log_err)
    if arg.startswith("-"):
        print(f"未知选项：{arg}（试试 泡语言.exe --help）", file=sys.stderr)
        return 2

    try:
        run_file(arg)
    except SystemExit:
        raise
    except KeyboardInterrupt:
        print("\n（程序被中断）", file=sys.stderr)
        return 130
    except NameError as e:
        # 误用英文内置名（如 input/print）时给出直观提示，而不是一长串回溯
        tb = traceback.extract_tb(sys.exc_info()[2])
        if tb:
            fr = tb[-1]
            loc = f"{fr.filename} 第 {fr.lineno} 行"
        else:
            loc = "程序中"
        print(f"名称错误：{e}（{loc}）", file=sys.stderr)
        print("提示：泡语言的内置函数、类型、异常都要用中文名"
              "（如 输入、打印、长度、值错误）；英文 input/print/open 等不再可用。"
              "输入 帮助() 查看完整列表。", file=sys.stderr)
        return 1
    except 泡语言错误 as e:
        print(f"错误：{e}", file=sys.stderr)
        return 1
    except Exception as e:
        tb = traceback.extract_tb(sys.exc_info()[2])
        行 = tb[-1].lineno if tb else None
        名称 = _中文异常名(type(e))
        消息 = _翻译错误消息(e)
        if 行:
            print(f"错误：{名称}：{消息}（第 {行} 行）", file=sys.stderr)
        else:
            print(f"错误：{名称}：{消息}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
