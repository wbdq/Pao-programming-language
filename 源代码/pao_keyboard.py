# -*- coding: utf-8 -*-
"""泡语言键盘检测：keyboard 库的完整中文封装。

覆盖 keyboard 的全部公开函数，一条不漏；另外还有兜底对象 `键盘`
（raw keyboard 模块），任何漏网的功能都可以 键盘.xxx 直达。

常用示例：
    如果 按键按下("a"):              # 检测 A 键有没有被按下
        打印("按了 A")
    等待按键("空格")                # 程序停下来等按空格
    发送按键("ctrl+c")              # 模拟按下快捷键
    键入("你好")                    # 模拟打字
    句柄 = 注册快捷键("ctrl+s", 保存)
    移除快捷键(句柄)
"""

import keyboard as _键盘


# ---- 检测类 ----
def 按键按下(键):
    """检测某个键当前是否被按下，返回 真/假。例：按键按下("a")"""
    return _键盘.is_pressed(键)


def 等待按键(键):
    """程序停下来，等用户按下指定键后再继续。例：等待按键("空格")"""
    return _键盘.wait(键)


def 读取按键():
    """等待用户按下一个键，返回该键的名字（如 "enter"、"a"）。"""
    return _键盘.read_key()


def 读取快捷键():
    """等待用户按下一个组合键，返回组合键名（如 "ctrl+shift+a"）。"""
    return _键盘.read_hotkey()


def 读取事件():
    """等待并返回下一个键盘事件对象（含 名称、事件类型、扫描码）。"""
    return _键盘.read_event()


# ---- 模拟输入类 ----
def 按下(键):
    """按住一个键不放。例：按下("a")"""
    return _键盘.press(键)


def 松开(键):
    """松开一个键。例：松开("a")"""
    return _键盘.release(键)


def 发送按键(组合):
    """模拟按下并松开（支持组合）。例：发送按键("ctrl+c")、发送按键("enter")"""
    return _键盘.press_and_release(组合)


def 发送(组合):
    """发送字符串或快捷键（send 的别名）。例：发送("ctrl+shift+esc")"""
    return _键盘.send(组合)


def 键入(文字):
    """模拟把文字一个一个打出来。例：键入("你好，泡语言")"""
    return _键盘.write(文字)


# ---- 快捷键类 ----
def 注册快捷键(组合, 函数):
    """注册一个全局快捷键，按下时执行函数。返回句柄，用于 移除快捷键。"""
    return _键盘.add_hotkey(组合, 函数)


def 移除快捷键(句柄):
    """取消 注册快捷键 注册的快捷键。"""
    try:
        _键盘.remove_hotkey(句柄)
    except Exception:
        pass


def 注册热键(组合, 函数):
    """注册快捷键（register_hotkey，和 注册快捷键 一样）。"""
    return _键盘.register_hotkey(组合, 函数)


def 注销快捷键(句柄):
    """注销快捷键（unregister_hotkey）。"""
    try:
        _键盘.unregister_hotkey(句柄)
    except Exception:
        pass


def 清除快捷键(句柄):
    """清除单个快捷键（clear_hotkey）。"""
    try:
        _键盘.clear_hotkey(句柄)
    except Exception:
        pass


def 清除所有快捷键():
    """清除所有快捷键（clear_all_hotkeys）。"""
    return _键盘.clear_all_hotkeys()


def 移除所有快捷键():
    """移除所有快捷键（remove_all_hotkeys）。"""
    return _键盘.remove_all_hotkeys()


def 取消所有快捷键():
    """取消所有快捷键挂接（unhook_all_hotkeys）。"""
    return _键盘.unhook_all_hotkeys()


def 注销所有快捷键():
    """注销所有快捷键（unregister_all_hotkeys）。"""
    return _键盘.unregister_all_hotkeys()


# ---- 按键阻止与映射 ----
def 阻止按键(键):
    """全局阻止某个键的原始功能。例：阻止按键("a") 后按 a 不再有任何效果。"""
    return _键盘.block_key(键)


def 解除阻止(键):
    """恢复被 阻止按键 阻止的键。例：解除阻止("a")"""
    return _键盘.unblock_key(键)


def 重新映射按键(来源, 目标):
    """把按键 来源 重新映射成 目标。例：重新映射按键("a", "b")"""
    return _键盘.remap_key(来源, 目标)


def 取消重新映射按键(来源):
    """取消按键重新映射。"""
    return _键盘.unremap_key(来源)


def 重新映射快捷键(来源, 目标):
    """把快捷键 来源 重新映射成 目标。例：重新映射快捷键("ctrl+a", "ctrl+c")"""
    return _键盘.remap_hotkey(来源, 目标)


def 取消重新映射快捷键(来源):
    """取消快捷键重新映射。"""
    return _键盘.unremap_hotkey(来源)


# ---- 回调与挂接 ----
def 注册按下回调(函数):
    """每次有按键被按下就调用 函数(事件对象)。"""
    return _键盘.on_press(函数)


def 注册松开回调(函数):
    """每次有按键被松开就调用 函数(事件对象)。"""
    return _键盘.on_release(函数)


def 注册按键按下回调(键, 函数):
    """指定键被按下时调用 函数(事件对象)。例：注册按键按下回调("a", 回调)"""
    return _键盘.on_press_key(键, 函数)


def 注册按键松开回调(键, 函数):
    """指定键被松开时调用 函数(事件对象)。"""
    return _键盘.on_release_key(键, 函数)


def 挂接(函数):
    """挂接一个底层键盘事件监听（hook）。"""
    return _键盘.hook(函数)


def 取消挂接(句柄):
    """取消挂接（unhook）。"""
    try:
        _键盘.unhook(句柄)
    except Exception:
        pass


def 取消所有挂接():
    """取消所有挂接（unhook_all）。"""
    return _键盘.unhook_all()


def 挂接按键(键, 函数):
    """挂接单个按键的事件（hook_key）。"""
    return _键盘.hook_key(键, 函数)


def 取消挂接按键(键):
    """取消单个按键的挂接（unhook_key）。"""
    try:
        _键盘.unhook_key(键)
    except Exception:
        pass


# ---- 记录与回放 ----
def 开始记录():
    """开始记录按键（之后可用 停止记录 拿到记录）。"""
    return _键盘.start_recording()


def 停止记录():
    """停止记录，返回记录的按键事件列表。"""
    return _键盘.stop_recording()


def 记录(直到键="esc"):
    """录下从调用到按下 直到键 之间的所有按键，返回事件列表。"""
    return _键盘.record(直到键)


def 回放(事件列表, 速度=1.0):
    """把 记录/停止记录 得到的事件列表原样重放。例：回放(记录())"""
    return _键盘.play(事件列表, speed_factor=速度)


def 重放(事件列表):
    """重放（replay，和 回放 一样）。"""
    return _键盘.replay(事件列表)


# ---- 缩写与词语 ----
def 添加缩写(缩写, 完整文字):
    """输入缩写自动替换成完整文字。例：添加缩写("bz", "注意安全")"""
    return _键盘.add_abbreviation(缩写, 完整文字)


def 移除缩写(缩写):
    """移除缩写。"""
    return _键盘.remove_abbreviation(缩写)


def 注册缩写(缩写, 完整文字):
    """注册缩写（和 添加缩写 一样）。"""
    return _键盘.register_abbreviation(缩写, 完整文字)


def 添加词语监听(词语, 回调):
    """输入到某个词语时触发回调。例：添加词语监听("hello", 回调)"""
    return _键盘.add_word_listener(词语, 回调)


def 移除词语监听(词语, 回调):
    """移除词语监听。"""
    return _键盘.remove_word_listener(词语, 回调)


def 注册词语监听(词语, 回调):
    """注册词语监听（和 添加词语监听 一样）。"""
    return _键盘.register_word_listener(词语, 回调)


def 获得输入文字(事件列表):
    """从事件列表还原成输入的字符串。"""
    return _键盘.get_typed_strings(事件列表)


# ---- 解析与转换 ----
def 解析快捷键(组合):
    """把快捷键字符串解析成结构。例：解析快捷键("ctrl+c")"""
    return _键盘.parse_hotkey(组合)


def 解析快捷键组合(组合):
    """解析快捷键组合（parse_hotkey_combinations）。"""
    return _键盘.parse_hotkey_combinations(组合)


def 规范化(名称):
    """把按键名规范化成标准名。例：规范化("ctrl")"""
    return _键盘.normalize_name(名称)


def 规范化名称(名称):
    """规范化名称（normalize_name，和 规范化 一样）。"""
    return _键盘.normalize_name(名称)


def 按键转扫描码(键):
    """把键名转成扫描码列表。例：按键转扫描码("a")"""
    return _键盘.key_to_scan_codes(键)


def 全部修饰键():
    """全部修饰键名称（all_modifiers，数据常量）。例：全部修饰键() 包含 "ctrl" 等。"""
    return _键盘.all_modifiers


def 单侧修饰键():
    """左右分开的修饰键（sided_modifiers，数据常量）。"""
    return _键盘.sided_modifiers


def 是否修饰键(名称):
    """判断一个键名是不是修饰键（ctrl/alt/shift 等）。"""
    return _键盘.is_modifier(名称)


def 获得快捷键名(扫描码组合=None):
    """把扫描码组合还原成快捷键名。例：获得快捷键名([29, 47])"""
    return _键盘.get_hotkey_name(扫描码组合)


# ---- 状态与杂项 ----
def 延时调用(秒, 函数):
    """过多少秒后调用函数（call_later，需要程序持续运行）。例：延时调用(0.5, 回调)"""
    return _键盘.call_later(函数, delay=秒)


def 暂存状态():
    """暂存当前按键状态（stash_state）。"""
    return _键盘.stash_state()


def 恢复状态():
    """恢复暂存的按键状态（restore_state）。"""
    return _键盘.restore_state()


def 恢复修饰键():
    """恢复修饰键状态（restore_modifiers）。"""
    return _键盘.restore_modifiers()


def 版本():
    """返回 keyboard 库版本号。"""
    return _键盘.version


# ---- 常量 ----
按下事件 = _键盘.KEY_DOWN   # 事件类型：按下
松开事件 = _键盘.KEY_UP     # 事件类型：松开
键盘事件 = _键盘.KeyboardEvent  # 键盘事件类型
