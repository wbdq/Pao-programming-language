# -*- coding: utf-8 -*-
"""泡语言海龟画图模块：用中文调用 turtle，不用写英文命令。

用法示例：
    设置背景色(白)
    设置颜色(红)
    设置速度(5)
    对于 数字 在 范围(4):
        前进(100)
        右转(90)
    完成()        # 保持画布窗口不关闭
"""

import turtle as _t

# 中文颜色名 → turtle 认识的英文颜色名
_颜色表 = {
    "红": "red", "橙": "orange", "黄": "yellow", "绿": "green",
    "青": "cyan", "蓝": "blue", "紫": "purple", "粉": "pink",
    "黑": "black", "白": "white", "灰": "gray", "棕": "brown",
    "金": "gold", "银": "silver", "天蓝": "skyblue", "深蓝": "navy",
    "深绿": "darkgreen", "酒红": "crimson", "浅蓝": "lightblue",
}


def _转颜色(颜色):
    return _颜色表.get(颜色, 颜色)


def 前进(步数):
    _t.forward(int(步数))


def 后退(步数):
    _t.backward(int(步数))


def 左转(角度):
    _t.left(int(角度))


def 右转(角度):
    _t.right(int(角度))


def 画圆(半径, 角度=360):
    _t.circle(int(半径), int(角度))


def 画点(大小=1, 颜色=None):
    if 颜色 is None:
        _t.dot(int(大小))
    else:
        _t.dot(int(大小), _转颜色(颜色))


def 开始填充():
    """开始填充：先用 设置颜色 选好填充色，再开始填充，画完图形后调用 结束填充。"""
    _t.begin_fill()


def 结束填充():
    _t.end_fill()


def 抬起笔():
    _t.penup()


def 落下笔():
    _t.pendown()


def 隐藏海龟():
    _t.hideturtle()


def 显示海龟():
    _t.showturtle()


def 去(横, 纵):
    _t.goto(int(横), int(纵))


def 设置速度(速度):
    _t.speed(int(速度))


def 设置颜色(颜色):
    _t.color(_转颜色(颜色))


def 设置画笔粗细(宽度):
    _t.pensize(int(宽度))


def 设置背景色(颜色):
    _t.bgcolor(_转颜色(颜色))


def 重置():
    _t.reset()


def 清屏():
    _t.clear()


def 设置方向(角度):
    """把海龟朝向设为指定角度（0 向右，90 向上）。"""
    _t.setheading(int(角度))


def 方向():
    """返回海龟当前朝向角度。"""
    return _t.heading()


def 位置():
    """返回海龟当前位置 (横, 纵)。"""
    return _t.position()


def 横坐标():
    """返回海龟当前位置的横坐标。"""
    return _t.xcor()


def 纵坐标():
    """返回海龟当前位置的纵坐标。"""
    return _t.ycor()


def 距离(横, 纵):
    """返回海龟到指定点的直线距离。"""
    return _t.distance(int(横), int(纵))


def 朝向(横, 纵):
    """返回海龟指向指定点的角度。"""
    return _t.towards(int(横), int(纵))


def 海龟大小(宽, 长=None, 轮廓=None):
    """设置海龟图标的大小。海龟大小(2) 放大两倍；海龟大小(2, 3) 拉长。"""
    if 长 is None:
        _t.shapesize(int(宽))
    elif 轮廓 is None:
        _t.shapesize(int(宽), int(长))
    else:
        _t.shapesize(int(宽), int(长), int(轮廓))


def 倾斜(角度):
    """让海龟图标旋转一个角度（不影响移动方向）。"""
    _t.tilt(int(角度))


def 复制():
    """复制一个海龟，返回新海龟对象。"""
    return _t.clone()


def 撤销():
    """撤销上一步画图动作。"""
    _t.undo()


# ---- 位置与坐标 ----
def 设横坐标(数值):
    _t.setx(int(数值))


def 设纵坐标(数值):
    _t.sety(int(数值))


def 设置位置(横, 纵):
    """把海龟移到指定位置（和 去 一样）。"""
    _t.setpos(int(横), int(纵))


def 回家():
    """让海龟回到原点 (0,0)，方向朝右。"""
    _t.home()


def 传送(横, 纵=None, 角度=None):
    """瞬间把海龟传送到指定位置（不画线）。例：传送(100, 100)"""
    if 纵 is None and 角度 is None:
        _t.teleport(int(横))
    elif 角度 is None:
        _t.teleport(int(横), int(纵))
    else:
        _t.teleport(int(横), int(纵), int(角度))


# ---- 图章 ----
def 图章():
    """在当前位置印一个海龟图形，返回图章编号。"""
    return _t.stamp()


def 清除图章(编号):
    """清除指定编号的图章。"""
    _t.clearstamp(编号)


def 清除所有图章():
    """清除全部图章。"""
    _t.clearstamps()


# ---- 笔与颜色 ----
def 是否画线():
    """返回海龟的笔是否落下（落下才会画线）。"""
    return _t.isdown()


def 笔状态():
    """返回当前笔的全部设置（颜色、粗细、是否落下等）。"""
    return _t.pen()


def 笔颜色(颜色):
    """设置画笔颜色（只影响线条，不影响填充）。例：笔颜色("红")"""
    _t.pencolor(_转颜色(颜色))


def 填充颜色(颜色):
    """设置填充颜色（配合 开始填充/结束填充 使用）。"""
    _t.fillcolor(_转颜色(颜色))


def 是否填充中():
    """返回当前是否正在填充（开始填充 和 结束填充 之间）。"""
    return _t.filling()


def 颜色模式(模式=None):
    """读取或设置颜色模式：255（0~255 数值）或 1.0（0~1 小数）。"""
    if 模式 is None:
        return _t.colormode()
    return _t.colormode(int(模式))


# ---- 多边形记录 ----
def 开始记录多边形():
    """开始记录海龟走过的路径，之后用 结束记录多边形/获得多边形 取出来。"""
    _t.begin_poly()


def 结束记录多边形():
    _t.end_poly()


def 获得多边形():
    """返回记录的多边形顶点坐标列表。"""
    return _t.get_poly()


# ---- 撤销缓冲 ----
def 设置撤销缓冲区(大小):
    """设置最多能撤销多少步。例：设置撤销缓冲区(100)"""
    _t.setundobuffer(int(大小))


def 撤销记录条数():
    """返回当前可撤销的步数。"""
    return _t.undobufferentries()


# ---- 形状 ----
_形状表 = {
    "经典": "classic", "箭头": "arrow", "乌龟": "turtle", "圆形": "circle",
    "方块": "square", "三角形": "triangle", "空": "blank",
}


def 形状(名称):
    """设置海龟的形状："经典"、"箭头"、"乌龟"、"圆形"、"方块"、"三角形"、"空"。"""
    return _t.shape(_形状表.get(str(名称), str(名称)))


def 注册形状(名称, 形状=None):
    """注册一个自定义形状，之后用 形状(名称) 切换。"""
    if 形状 is None:
        _t.register_shape(str(名称))
    else:
        _t.register_shape(str(名称), 形状)


def 添加形状(名称, 形状=None):
    """添加形状（和 注册形状 一样）。"""
    if 形状 is None:
        _t.addshape(str(名称))
    else:
        _t.addshape(str(名称), 形状)


def 现有形状():
    """返回所有可用形状名称列表。"""
    return _t.getshapes()


def 缩放模式(模式):
    """设置缩放模式："自动"、"用户"、"无"。"""
    return _t.resizemode(str(模式))


def 形状变换(横1, 竖1, 横2, 竖2):
    """用矩阵变换海龟形状。例：形状变换(2, 0, 0, 2) 放大两倍。"""
    return _t.shapetransform(int(横1), int(竖1), int(横2), int(竖2))


def 剪切因子(剪切值):
    """让海龟形状倾斜变形。例：剪切因子(1)"""
    return _t.shearfactor(int(剪切值))


def 倾斜角度():
    """返回海龟图标当前的倾斜角度。"""
    return _t.tiltangle()


def 是否可见():
    """返回海龟当前是否可见。"""
    return _t.isvisible()


# ---- 屏幕与窗口 ----
def 重置屏幕():
    """重置整个画布（清空画面、恢复设置）。"""
    _t.resetscreen()


def 清空屏幕():
    """清空画布上的所有图形（保留海龟）。"""
    _t.clearscreen()


def 屏幕尺寸(宽, 高):
    """设置画布大小。例：屏幕尺寸(800, 600)"""
    _t.screensize(int(宽), int(高))


def 设置世界坐标(左, 下, 右, 上):
    """自定义坐标系范围。例：设置世界坐标(-500, -500, 500, 500)"""
    _t.setworldcoordinates(int(左), int(下), int(右), int(上))


def 轨迹(数量=1, 延迟毫秒=None):
    """动画开关：轨迹(0) 关掉动画直接画完；轨迹(1) 恢复动画。"""
    if 延迟毫秒 is None:
        _t.tracer(int(数量))
    else:
        _t.tracer(int(数量), int(延迟毫秒))


def 更新():
    """轨迹关闭时，手动刷新画面。"""
    return _t.update()


def 动画延迟(毫秒):
    """设置动画每步之间的延迟（毫秒）。例：动画延迟(50)"""
    _t.delay(int(毫秒))


def 开始监听():
    """开始监听键盘/鼠标事件（配合 注册按键/注册点击 使用）。"""
    _t.listen()


def 注册按键(键, 函数):
    """按下指定键时执行函数。例：注册按键("上", 前进10)"""
    _t.onkey(函数, str(键))


def 注册按下按键(键, 函数):
    """按下指定键时执行函数（onkeypress）。"""
    _t.onkeypress(函数, str(键))


def 注册松开按键(键, 函数):
    """松开指定键时执行函数（onkeyrelease）。"""
    _t.onkeyrelease(函数, str(键))


def 注册点击(函数):
    """点击海龟时执行函数（函数接收横坐标、纵坐标）。"""
    _t.onclick(函数)


def 注册屏幕点击(函数):
    """点击画布任意位置时执行函数。"""
    _t.onscreenclick(函数)


def 注册拖拽(函数):
    """拖动海龟时执行函数。"""
    _t.ondrag(函数)


def 注册松开(函数):
    """在海龟上松开鼠标时执行函数。"""
    _t.onrelease(函数)


def 定时器(毫秒, 函数):
    """过多少毫秒后执行函数（配合 开始监听 使用）。例：定时器(1000, 刷新)"""
    _t.ontimer(函数, int(毫秒))


def 输入文字(标题, 提示):
    """弹出对话框让用户输入一行文字，返回输入内容。"""
    return _t.textinput(str(标题), str(提示))


def 输入数字(标题, 提示, 默认=None, 最小=None, 最大=None):
    """弹出对话框让用户输入一个数字，返回数值。"""
    return _t.numinput(str(标题), str(提示), 默认, 最小, 最大)


def 窗口标题(标题):
    """设置画布窗口的标题。"""
    _t.title(str(标题))


def 窗口设置(宽=None, 高=None, 起点横=None, 起点纵=None):
    """设置窗口大小和位置。例：窗口设置(800, 600)"""
    _t.setup(int(宽) if 宽 is not None else None,
             int(高) if 高 is not None else None,
             int(起点横) if 起点横 is not None else None,
             int(起点纵) if 起点纵 is not None else None)


def 窗口宽度():
    """返回窗口当前宽度。"""
    return _t.window_width()


def 窗口高度():
    """返回窗口当前高度。"""
    return _t.window_height()


def 画布():
    """返回底层画布对象（一般用不到）。"""
    return _t.getcanvas()


def 画笔对象():
    """返回底层画笔对象（一般用不到）。"""
    return _t.getpen()


def 屏幕对象():
    """返回底层屏幕对象（一般用不到）。"""
    return _t.getscreen()


def 全部海龟():
    """返回画布上全部海龟对象列表。"""
    return _t.turtles()


def 模式(模式=None):
    """读取或设置坐标模式："标准"、"标志"。"""
    if 模式 is None:
        return _t.mode()
    return _t.mode(str(模式))


def 角度制():
    """把角度单位设为度（默认）。"""
    _t.degrees()


def 弧度制():
    """把角度单位设为弧度。"""
    _t.radians()


def 写字(文字, 对齐="左", 字体=None):
    """在当前位置写下文字。对齐："左"/"中"/"右"；字体：("微软雅黑", 16, "正常")"""
    对齐表 = {"左": "left", "中": "center", "右": "right"}
    if 字体 is None:
        _t.write(str(文字), align=对齐表.get(对齐, 对齐))
    else:
        _t.write(str(文字), align=对齐表.get(对齐, 对齐), font=字体)


def 完成():
    """保持画布窗口不关闭，等待手动关窗。"""
    _t.done()


def 关闭():
    """立即关闭画布窗口。"""
    _t.bye()
