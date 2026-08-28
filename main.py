# -*- coding:utf-8 -*-
"""
对硬盘要求较高，需要较高的数据传输速度
"""
import tkinter as tk
import tkinter.ttk as ttk
from tkinter.filedialog import askdirectory
from multiprocessing import freeze_support
from ctypes import windll
import os
import json
import sys
from PIL import Image, ImageTk
import time
import numpy as np
from base64 import b64decode
from icon import icon_SPEC, icon_left, icon_right  # 图标文件
import SPEC_parallel as SPEC


def initialization():
    # 初始化数据文件夹
    if not os.path.exists(folder_temp):
        os.makedirs(folder_temp)
    global VarName_IO, VarName_RAM, VarName_PARAM, VarName_ZONE, VarName_CALI
    VarName_IO = ("分析文件夹", "输出文件夹", "输出文件名")
    VarName_RAM = ("运行内存 (GB)", "并行核数")
    VarName_PARAM = ("“图片对”数目", "查询窗口宽度 (奇数)", "查询窗口高度 (奇数)")
    VarName_ZONE = ("x1 (左边界)", "x2 (右边界)", "y1 (上边界)", "y2 (下边界)")
    VarName_CALI = ("标定比例系数 (mm/Pixel)", "双帧时间间隔 (ms)")
    global folder_input, folder_output, OutputName, listing, Var_IO
    global RAM, process_num, Var_RAM
    global n, width, height, Var_PARAM
    global x1, x2, y1, y2, xp, yp, Var_ZONE
    global scale, dt, Var_CALI
    try:
        # 文件夹信息
        with open(os.path.join(folder_temp, "initial_IO.json"), "r") as json_file:
            initial_IO = json.load(json_file)

        folder_input = tk.StringVar()
        folder_input.set(initial_IO[VarName_IO[0]])
        folder_output = tk.StringVar()
        folder_output.set(initial_IO[VarName_IO[1]])
        OutputName = tk.StringVar()
        OutputName.set(initial_IO[VarName_IO[2]])
        listing = []
        Var_IO = (folder_input, folder_output, OutputName)

        # 内存和运算效率参数
        with open(os.path.join(folder_temp, "initial_RAM.json"), "r") as json_file:
            initial_RAM = json.load(json_file)

        RAM = tk.IntVar()  # 内存(GB)
        RAM.set(initial_RAM[VarName_RAM[0]])
        process_num = tk.IntVar()  # 并行进程数
        process_num.set(initial_RAM[VarName_RAM[1]])
        Var_RAM = (RAM, process_num)

        # SPEC计算参数
        with open(os.path.join(folder_temp, "initial_PARAM.json"), "r") as json_file:
            initial_PARAM = json.load(json_file)

        n = tk.IntVar()  # 需要分析的“图片对”数量
        n.set(initial_PARAM[VarName_PARAM[0]])
        width, height = tk.IntVar(), tk.IntVar()  # 查询窗口大小
        width.set(initial_PARAM[VarName_PARAM[1]])
        height.set(initial_PARAM[VarName_PARAM[2]])
        Var_PARAM = (n, width, height)

        # 计算区域参数
        with open(os.path.join(folder_temp, "initial_ZONE.json"), "r") as json_file:
            initial_ZONE = json.load(json_file)

        x1, x2 = tk.IntVar(), tk.IntVar()  # x方向计算范围
        y1, y2 = tk.IntVar(), tk.IntVar()  # y方向计算范围
        x1.set(initial_ZONE[VarName_ZONE[0]])
        x2.set(initial_ZONE[VarName_ZONE[1]])
        y1.set(initial_ZONE[VarName_ZONE[2]])
        y2.set(initial_ZONE[VarName_ZONE[3]])
        Var_ZONE = (x1, x2, y1, y2)
        xp, yp = tk.IntVar(), tk.IntVar()  # 图片大小
        xp.set(0)
        yp.set(0)

        # 标定参数
        with open(os.path.join(folder_temp, "initial_CALI.json"), "r") as json_file:
            initial_CALI = json.load(json_file)

        scale = tk.DoubleVar()
        dt = tk.DoubleVar()
        scale.set(initial_CALI[VarName_CALI[0]])
        dt.set(initial_CALI[VarName_CALI[1]])
        Var_CALI = (scale, dt)
    except:
        # 文件夹信息
        folder_input = tk.StringVar()
        folder_input.set(os.path.abspath("."))
        folder_input.set(folder_temp)
        folder_output = tk.StringVar()
        folder_output.set(os.path.abspath("."))
        folder_output.set(folder_temp)
        OutputName = tk.StringVar()
        OutputName.set("SPEC")
        listing = []
        Var_IO = (folder_input, folder_output, OutputName)

        # 内存和运算效率参数
        RAM = tk.IntVar()  # 内存(GB)
        RAM.set(8)
        process_num = tk.IntVar()  # 并行进程数
        process_num.set(4)
        Var_RAM = (RAM, process_num)

        # SPEC计算参数
        n = tk.IntVar()  # 需要分析的“图片对”数量
        n.set(250)
        width, height = tk.IntVar(), tk.IntVar()  # 查询窗口大小
        width.set(65)
        height.set(9)
        Var_PARAM = (n, width, height)

        # 计算区域参数
        x1, x2 = tk.IntVar(), tk.IntVar()  # x方向计算范围
        y1, y2 = tk.IntVar(), tk.IntVar()  # y方向计算范围
        # 初始化为-1，届时将自动调整为整幅图片
        x1.set(-1)
        x2.set(-1)
        y1.set(-1)
        y2.set(-1)
        Var_ZONE = (x1, x2, y1, y2)
        xp, yp = tk.IntVar(), tk.IntVar()  # 图片大小
        xp.set(0)
        yp.set(0)

        # 标定参数
        scale = tk.DoubleVar()
        dt = tk.DoubleVar()
        scale.set(1)
        dt.set(1)
        Var_CALI = (scale, dt)
    return None


# 文件初始化数据的保存
def save_initialization():
    # 文件夹信息
    initial_IO = dict()
    for a in range(len(Var_IO)):
        initial_IO[VarName_IO[a]] = Var_IO[a].get()
    with open(os.path.join(folder_temp, "initial_IO.json"), "w") as json_file:
        json.dump(initial_IO, json_file)

    # 内存和运算效率参数
    initial_RAM = dict()
    for a in range(len(Var_RAM)):
        initial_RAM[VarName_RAM[a]] = Var_RAM[a].get()
    with open(os.path.join(folder_temp, "initial_RAM.json"), "w") as json_file:
        json.dump(initial_RAM, json_file)

    # SPEC计算参数
    initial_PARAM = dict()
    for a in range(len(Var_PARAM)):
        initial_PARAM[VarName_PARAM[a]] = Var_PARAM[a].get()
    with open(os.path.join(folder_temp, "initial_PARAM.json"), "w") as json_file:
        json.dump(initial_PARAM, json_file)

    # 计算区域参数
    initial_ZONE = dict()
    for a in range(len(Var_ZONE)):
        initial_ZONE[VarName_ZONE[a]] = Var_ZONE[a].get()
    with open(os.path.join(folder_temp, "initial_ZONE.json"), "w") as json_file:
        json.dump(initial_ZONE, json_file)

    # 标定参数
    initial_CALI = dict()
    for a in range(len(Var_CALI)):
        initial_CALI[VarName_CALI[a]] = Var_CALI[a].get()
    with open(os.path.join(folder_temp, "initial_CALI.json"), "w") as json_file:
        json.dump(initial_CALI, json_file)

    return None


# 文件夹设置栏
def FolderFrames():
    def selectAnalysis():
        path_ = askdirectory(
            title="选择分析文件夹", initialdir=folder_input.get()
        )  # 使用askdirectory()方法返回文件夹的路径
        if path_ == "":
            folder_input.get()  # 当打开文件路径选择框后点击"取消" 输入框会清空路径，所以使用get()方法再获取一次路径
        else:
            path_ = path_.replace("/", "\\")  # 实际在代码中执行的路径为“\“ 所以替换一下
            folder_input.set(path_)
        return None

    def selectOutput():
        path_ = askdirectory(
            title="选择输出文件夹", initialdir=folder_output.get()
        )  # 使用askdirectory()方法返回文件夹的路径
        if path_ == "":
            folder_output.get()  # 当打开文件路径选择框后点击"取消" 输入框会清空路径，所以使用get()方法再获取一次路径
        else:
            path_ = path_.replace("/", "\\")  # 实际在代码中执行的路径为“\“ 所以替换一下
            folder_output.set(path_)
        return None

    Frame = tk.LabelFrame(root, text="分析路径设置")
    Frame.pack(fill=tk.X, side=tk.TOP)
    # 分析文件夹
    ttk.Label(Frame, text="分析文件夹").grid(row=0, column=0)
    ttk.Entry(Frame, textvariable=folder_input).grid(row=0, column=1, ipadx=200)
    ttk.Button(Frame, text="浏览", command=selectAnalysis).grid(row=0, column=2)
    # 输出文件夹
    ttk.Label(Frame, text="输出文件夹").grid(row=1, column=0)
    ttk.Entry(Frame, textvariable=folder_output).grid(row=1, column=1, ipadx=200)
    ttk.Button(Frame, text="浏览", command=selectOutput).grid(row=1, column=2)
    return None


# 文件列表栏
def FolderListFrames():
    def list_BMP():
        def list_it():
            if os.path.exists(folder_input.get()):
                global listing
                listing = [
                    a for a in os.listdir(folder_input.get()) if a.endswith(".bmp")
                ]
                n0.set(len(listing))
                list.delete(0, tk.END)
                for item in listing:
                    list.insert(tk.END, item)
                preview_scale.set(1)
                RedrawPicture()
            else:
                print("错误：无此文件夹")

        global u, v, PARAM
        if not (u is None):
            if tk.messagebox.askyesno(
                "列出文件目录", "此操作将清除计算结果，是否确定？"
            ):
                u = None
                v = None
                PARAM = None
                global progress
                progress["value"] = 0
                Analysis_Progress.set("准备开始计算")
                list_BMP()
        else:
            list_it()
        return None

    width0 = 35
    Frame = tk.LabelFrame(root, text="BMP文件列表", width=width0)
    ttk.Button(
        Frame, text="列出文件夹内所有BMP文件", command=list_BMP, width=width0
    ).pack(fill=tk.X, side=tk.TOP)
    Frame_temp = tk.Frame(Frame, width=width0)
    n0 = tk.IntVar()  # 需要分析的“图片对”数量
    n0.set(0)
    ttk.Label(Frame_temp, text="共").pack(fill=tk.X, side=tk.LEFT)
    ttk.Label(Frame_temp, textvariable=n0).pack(fill=tk.X, side=tk.LEFT)
    ttk.Label(Frame_temp, text="张图片").pack(fill=tk.X, side=tk.LEFT)
    Frame_temp.pack(fill=tk.X, side=tk.TOP)

    # 滚动条
    Scroll = tk.Scrollbar(Frame)
    Scroll.pack(fill=tk.Y, side=tk.RIGHT)
    list = tk.Listbox(Frame, selectmode=tk.BROWSE, width=width0)
    list.pack(fill=tk.BOTH)

    # 配置
    list.configure(yscrollcommand=Scroll.set)
    list.pack(side=tk.LEFT, fill=tk.BOTH)
    # 额外给属性赋值
    Scroll["command"] = list.yview

    Frame.pack(fill=tk.Y, side=tk.LEFT)
    return None


# 计算参数栏
class VariablesFrames(tk.Canvas):
    def __init__(self, master):
        super().__init__(master, width=0, height=0)
        self.master = master
        self.pack(fill=tk.Y, side=tk.LEFT)
        self.frame = ttk.Frame(self)
        self.frame.pack()
        self.Rolling()
        self.create_widgets()

    def create_widgets(self):
        self.Add_a_Frame(Var_RAM, VarName_RAM, "内存和运算效率")
        self.Add_a_Frame(Var_PARAM, VarName_PARAM, "分析参数")
        self.Add_a_Frame(Var_ZONE, VarName_ZONE, "计算区域")
        self.Add_a_Frame(Var_CALI, VarName_CALI, "标定系数")

    def Add_a_Frame(self, Var, VarName, Label):
        Frame_temp = tk.LabelFrame(self.frame, text=Label)
        Frame_temp.pack(fill=tk.X, side=tk.TOP)
        for i in range(len(Var)):
            ttk.Label(Frame_temp, text=VarName[i]).pack(fill=tk.X, side=tk.TOP)
            ttk.Entry(Frame_temp, textvariable=Var[i]).pack(fill=tk.X, side=tk.TOP)
        return None

    def Rolling(self):
        # 添加滚动条
        # 原文链接1：https://blog.csdn.net/bigcarp/article/details/123846887
        # 原文连接2：https://blog.csdn.net/qq_28123095/article/details/79331756
        def Rolling(event):  # 滚轴移动
            self.configure(
                scrollregion=self.bbox("all"), width=self.frame.winfo_width()
            )
            return None

        self.bar = tk.Scrollbar(self.master, orient=tk.VERTICAL)  # 竖直滚动条
        self.bar.pack(fill=tk.Y, side=tk.LEFT)
        self.bar.configure(command=self.yview)
        self.configure(yscrollcommand=self.bar.set)  # 设置
        self.create_window((0, 0), window=self.frame)
        self.frame.bind("<Configure>", Rolling)
        return None


# 绘制图像
def RedrawPicture(event=None):
    # 绘制三个矩形作为边框的函数
    def create_three_rectangles(x1, x2, y1, y2, width):
        canvas_picture.create_rectangle(
            x1 * preview_scale.get() - width,
            y1 * preview_scale.get() - width,
            x2 * preview_scale.get() + width,
            y2 * preview_scale.get() + width,
            outline="#ffffff",
            width=width,
        )
        canvas_picture.create_rectangle(
            x1 * preview_scale.get() + width,
            y1 * preview_scale.get() + width,
            x2 * preview_scale.get() - width,
            y2 * preview_scale.get() - width,
            outline="#ffffff",
            width=width,
        )
        canvas_picture.create_rectangle(
            x1 * preview_scale.get(),
            y1 * preview_scale.get(),
            x2 * preview_scale.get(),
            y2 * preview_scale.get(),
            outline="#ff0000",
            width=width,
        )
        return None

    # 每次刷新图片保存参数
    if n.get() > int(len(listing) / 2):
        n.set(int(len(listing) / 2))
    save_initialization()

    # 先消除之前绘制的图像
    for widget in rollFrame.winfo_children():
        widget.destroy()
    # 打开图像
    global image_show
    # 读取图像
    image_show = Image.open(os.path.join(folder_input.get(), listing[0]))
    x0, y0 = image_show.size
    xp.set(x0)
    yp.set(y0)
    # 变更图像大小
    if preview_scale.get() > 1:
        x0 = round(x0 * preview_scale.get())
        y0 = round(y0 * preview_scale.get())
        image_show = image_show.resize((x0, y0), Image.NEAREST)
    # 将图像转换为 Tkinter 可用的格式
    image_show = ImageTk.PhotoImage(image_show)
    canvas_picture = tk.Canvas(
        rollFrame, width=x0 + preview_scale.get(), height=y0 + preview_scale.get()
    )
    canvas_picture.pack(fill=tk.BOTH, expand=True)
    canvas_picture.create_image(
        preview_scale.get(), preview_scale.get(), anchor="nw", image=image_show
    )

    if (
        x1.get() < 0
        or x2.get() <= 0
        or x2.get() >= x0
        or y1.get() < 0
        or y2.get() <= 0
        or y2.get() >= y0
    ):
        x1.set(0)  # x2默认取图片最大值
        y1.set(0)  # y2默认取图片最大值
        x2.set(x0 - 1)  # x2默认取图片最大值
        y2.set(y0 - 1)  # y2默认取图片最大值
    # 绘制计算区域的线条，为防止单色对比度容易低的问题，采用三条线描述勾选框
    create_three_rectangles(
        x1.get() + 1.5, x2.get() + 1.5, y1.get() + 1.5, y2.get() + 1.5, 0.5
    )

    # 再绘制一个结果区域，此区域表示最终计算结果的矢量范围
    # 由于不能直接绘制半透明矩形，需要用 Image 绘制一个半透明图片
    global rectangle
    rectangle = Image.new(
        "RGBA",
        (
            (x2.get() - x1.get() - width.get() + 1) * preview_scale.get(),
            (y2.get() - y1.get() - height.get() + 1) * preview_scale.get(),
        ),
        (255, 255, 0, 64),
    )  # 红色半透明
    rectangle = ImageTk.PhotoImage(rectangle)
    # 将半透明图像画到 Canvas 上
    canvas_picture.create_image(
        (int(width.get() / 2) + x1.get() + 1.5) * preview_scale.get(),
        (int(height.get() / 2) + y1.get() + 1.5) * preview_scale.get(),
        anchor="nw",
        image=rectangle,
    )
    print("图像刷新")
    return None


# 预览图片区域
def PicturePreviewFrames():
    # 双滚轴实现滚动原文链接：https://blog.csdn.net/bigcarp/article/details/123846887
    def Picture_Moving():
        def Rolling(event):  # 滚轴移动
            canvas_roll.configure(scrollregion=canvas_roll.bbox("all"))
            return None

        # 建立底层滚动画布
        canvas_roll = tk.Canvas(root, width=0, height=0)
        # 创建滚动条
        Scroll_Y = tk.Scrollbar(root, orient="vertical", command=canvas_roll.yview)
        Scroll_Y.pack(fill=tk.Y, side=tk.RIGHT)
        canvas_roll.configure(yscrollcommand=Scroll_Y.set)
        Scroll_X = tk.Scrollbar(root, orient="horizontal", command=canvas_roll.xview)
        Scroll_X.pack(fill=tk.X, side=tk.BOTTOM)
        canvas_roll.configure(xscrollcommand=Scroll_X.set)

        canvas_roll.pack(fill=tk.BOTH, expand=True)
        # 创建可滚动 Frame
        global rollFrame
        rollFrame = tk.Frame(canvas_roll)  # 在画布上创建frame
        # Frame 上创建一个 create_window 跟随画布滚动
        canvas_roll.create_window((0, 0), window=rollFrame)
        rollFrame.bind("<Configure>", Rolling)
        # rollFrame.bind("<B1-Motion>", Moving)

    # 更新滑动条值的函数
    def update_scale_value(val):
        # 将当前值转换为整数并设置为preview_scale
        value = round(float(val))  # 将值四舍五入到最接近的整数
        if 1 <= value <= 8:  # 确保值在范围内
            preview_scale.set(value)

    Frame_temp = tk.Frame(root)
    ttk.Label(Frame_temp, text="图片大小：").pack(side=tk.LEFT)
    ttk.Label(Frame_temp, textvariable=xp).pack(side=tk.LEFT)
    ttk.Label(Frame_temp, text="×").pack(side=tk.LEFT)
    ttk.Label(Frame_temp, textvariable=yp).pack(side=tk.LEFT)
    ttk.Label(Frame_temp, text="图片缩放比例：", width=15, anchor="e").pack(
        side=tk.LEFT
    )
    ttk.Label(Frame_temp, textvariable=preview_scale, width=2, anchor="center").pack(
        side=tk.LEFT
    )
    scale = ttk.Scale(
        Frame_temp,
        from_=1,
        to=8,
        variable=preview_scale,
        orient=tk.HORIZONTAL,
        command=lambda val: update_scale_value(val),  # 绑定回调函数
    )
    scale.pack(side=tk.LEFT)  # 创建一个 Canvas 控件
    tk.Label(
        Frame_temp, text="红框为计算范围", bd=1, relief="solid", fg="red", bg="white"
    ).pack(side=tk.LEFT)
    tk.Label(Frame_temp, text="黄底表示矢量结果像素的位置", bg="#ffff88").pack(
        side=tk.LEFT
    )
    Frame_temp.pack(fill=tk.X, side=tk.TOP)

    # 创建 Frame 并使之可滚动
    Picture_Moving()
    return None


# 开始计算按钮和信息输出栏
class StartFrames(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.pack(fill=tk.Y, side=tk.LEFT)
        self.create_widgets()
        return None

    def create_widgets(self):
        self.create_Start_Buttons()
        self.create_Progress_Bar()
        self.create_print_output_box()
        return None

    def create_Start_Buttons(self):
        def Start_Analysis():
            if tk.messagebox.askyesno(
                "分析",
                "请确认【内存】充足、【分析参数】【计算区域】正确，确定开始分析吗？",
            ):
                SPEC_Calculation()
            return None

        def Stop_Analysis():
            global Analysis_Continuing
            Analysis_Continuing = False
            print("程序手动终止")
            raise ValueError("程序手动终止")

        ttk.Button(self, text="图像刷新", command=RedrawPicture).pack(
            fill=tk.X, side=tk.TOP
        )
        ttk.Button(self, text="开始计算", command=Start_Analysis).pack(
            fill=tk.X, side=tk.TOP
        )
        ttk.Button(self, text="停止计算", command=Stop_Analysis).pack(
            fill=tk.X, side=tk.TOP
        )
        ttk.Button(self, text="输出结果", command=SPEC_Output).pack(
            fill=tk.X, side=tk.TOP
        )
        return None

    def create_print_output_box(self):
        # 输出 print 框
        def redirect_stdout_to_tkinter(text_widget):
            # 原文链接：https://blog.csdn.net/qq_26358881/article/details/132369041
            class StdoutRedirector:
                def __init__(self, text_widget):
                    self.text_widget = text_widget

                def write(self, message):
                    self.text_widget.insert("end", message)
                    self.text_widget.see("end")

            sys.stdout = StdoutRedirector(text_widget)

        global output_text
        output_text = tk.Text(self, width=25, state="normal")
        # output_text = tk.Text(self)
        output_text.pack(expand=True, fill=tk.BOTH)
        # 重定向标准输出到文本框
        redirect_stdout_to_tkinter(output_text)
        return None

    def create_Progress_Bar(self):
        global progress
        progress = ttk.Progressbar(self)
        ttk.Label(self, textvariable=Analysis_Progress).pack(fill=tk.X, side=tk.TOP)
        progress.pack(fill=tk.X, side=tk.TOP)
        return None


# Frames 栏目构图
def PrintFrames():
    # 列出文件夹内的图片信息
    FolderListFrames()
    # 文件夹信息
    FolderFrames()
    # 左侧参数栏
    VariablesFrames(root)
    # 开始栏
    StartFrames(root)
    # 图片预览区域
    PicturePreviewFrames()
    return None


# 合并进行
def correlation_integration(PARAM, sigma_A, sigma_B, Im_mean_A, Im_mean_B):
    """
    :param sigma_A: A帧标准差
    :param sigma_B: B帧标准差
    :param Im_mean_A: 所有 A 帧图片的平均值
    :param Im_mean_B: 所有 B 帧图片的平均值
    :return: 平均速度场 u,v
    """
    # 通过设计最大数据量 2**25 * RAM / process_num 估计分块block数目
    # 先算出总像素数量，再除以总内存对应的像素数量(最大数据量)，就是分块数
    numBlock = (
        int(
            (PARAM.numY + PARAM.height)  # 图像纵向像素数量
            * (PARAM.numX + PARAM.width)  # 图像横向像素数量
            * PARAM.height  # 互相关纵向像素数量
            * PARAM.width  # 互相关横向像素数量
            * PARAM.process_num
            * 0.75
            / 2**25
            / PARAM.RAM
        )
        + 1
    )
    if numBlock == 1:
        numBlock = 2
    numYb = (
        int(PARAM.numY / numBlock) + 1
    )  # 每个分块的y坐标个数 (小于分块纵向像素点个数)
    # 初始化进度条
    global progress
    progress["maximum"] = numBlock
    progress["value"] = 0
    Analysis_Progress.set("并行 SPEC 计算进度：0 %")
    # 图片由上至下进行分块分析
    y1b = PARAM.y1  # 当前块的 上侧中心位置的 y 索引
    y2b = y1b + numYb - 1  # 当前块的 下侧中心位置的 y 索引
    u, v = np.zeros((PARAM.numY, PARAM.numX)), np.zeros((PARAM.numY, PARAM.numX))
    starttime = time.time()
    for a in range(numBlock):
        if a == numBlock - 1:
            y2b = PARAM.y2  # 最后一块区域将 y2b 设置为 y2
        print(time.strftime("%Y-%m-%d %H:%M", time.localtime()))
        process_description = "区域%d/%d" % (a + 1, numBlock)
        print(process_description)
        print(
            "分块法向像素点数: %d\n上边界索引: %d\n下边界索引: %d" % (numYb, y1b, y2b)
        )
        start = time.time()
        if a != 0:
            remaining_time = (end - starttime) / a * (numBlock - a)  # 估计剩余时间
            print(
                "总剩余时间约 %d min %d s" % (remaining_time // 60, remaining_time % 60)
            )
        root.update_idletasks()
        (
            u[y1b - PARAM.y1 : y2b - PARAM.y1 + 1],
            v[y1b - PARAM.y1 : y2b - PARAM.y1 + 1],
        ) = SPEC.correlation_small_field(
            PARAM,
            sigma_A,
            sigma_B,
            Im_mean_A,
            Im_mean_B,
            y1b,
            y2b,
            process_description,
        )
        end = time.time()
        print(
            "区域完成, 用时 %d min %d s\n" % ((end - start) // 60, (end - start) % 60)
        )
        y1b += numYb
        y2b += numYb
        Analysis_Progress.set(
            "并行 SPEC 计算进度：%d %%" % (round((a + 1) / numBlock * 100))
        )
        progress["value"] += 1
        output_text.update()
        # root.update_idletasks()
        global Analysis_Continuing
        if not Analysis_Continuing:
            Analysis_Continuing = True
            progress["value"] = 0
            if a != numBlock - 1:
                raise ValueError("程序手动终止")

    u = np.flip(u, axis=0)
    v = np.flip(v, axis=0)
    print("互相关结果为大小", u.shape, "的矩阵")
    output_text.update()
    return u, v


# 计算
def SPEC_Calculation():
    # 保存参数
    save_initialization()
    # 初始化分析参数
    global PARAM, u, v, sigma_A, sigma_B, Im_mean_A, Im_mean_B
    PARAM = SPEC.SPEC_Parameters(
        RAM.get(),
        process_num.get(),
        n.get(),
        width.get(),
        height.get(),
        xp.get(),
        yp.get(),
        x1.get() + int(width.get() / 2),
        x2.get() - int(width.get() / 2),
        y1.get() + int(height.get() / 2),
        y2.get() - int(height.get() / 2),
        folder_input.get(),
        folder_output.get(),
    )

    # 数据准备
    print(time.strftime("\n%Y-%m-%d %H:%M", time.localtime()))
    print("图片统计量计算中...")
    Analysis_Progress.set("图片统计量计算中...")
    root.update_idletasks()
    start = time.time()
    sigma_A, sigma_B, Im_mean_A, Im_mean_B = SPEC.statistics_parallel(PARAM)
    end = time.time()
    print("数据统计用时%.1f s" % (end - start))
    output_text.update()

    # 互相关运算
    print(time.strftime("\n%Y-%m-%d %H:%M", time.localtime()))
    print("%d核并行\n互相关开始...\n" % (PARAM.process_num))
    start = time.time()
    u, v = correlation_integration(PARAM, sigma_A, sigma_B, Im_mean_A, Im_mean_B)
    end = time.time()
    print(
        "SPEC计算用时 %d h %d min %d s\n"
        % ((end - start) // 60 // 60, (end - start) // 60 % 60, (end - start) % 60)
    )

    tk.messagebox.showinfo(message="分析完成")
    SPEC_Output()
    return None


# 输出函数
def SPEC_Output():
    # 输出界面
    class OutputFrames(tk.Frame):
        def __init__(self, master):
            super().__init__(master)
            self.master = master
            self.pack()
            self.create_widgets()
            return None

        def create_widgets(self):
            self.choose_coordinate()
            self.create_choose_output()
            self.create_scale_reconfirm()
            self.create_buttons()
            return None

        def choose_coordinate(self):
            Frame_temp = tk.LabelFrame(self, text="坐标系选择")
            Frame_temp.pack(fill=tk.X, side=tk.TOP)
            # 创建并显示 Radiobutton（右手坐标系）
            tk.Radiobutton(
                Frame_temp,
                image=RHC,
                indicatoron=0,
                variable=coordinate,
                value=1,
            ).pack(side=tk.LEFT)
            tk.Radiobutton(
                Frame_temp,
                image=LHC,
                indicatoron=0,
                variable=coordinate,
                value=2,
            ).pack(side=tk.RIGHT)
            return None

        def create_choose_output(self):
            Frame_temp = tk.LabelFrame(self, text="选择输出变量")
            Frame_temp.pack(fill=tk.X, side=tk.TOP)
            ttk.Checkbutton(Frame_temp, text="输出整场", variable=field_output).pack(
                fill=tk.X, side=tk.TOP
            )
            ttk.Checkbutton(
                Frame_temp, text="输出流向平均剖面", variable=profile_output
            ).pack(fill=tk.X, side=tk.TOP)
            ttk.Checkbutton(
                Frame_temp, text="输出统计量图片", variable=statistics_output
            ).pack(fill=tk.X, side=tk.TOP)
            return None

        def create_scale_reconfirm(self):
            Frame_temp = tk.LabelFrame(self, text="标定信息再确认")
            Frame_temp.pack(fill=tk.X, side=tk.TOP)
            for i in range(len(Var_CALI)):
                ttk.Label(Frame_temp, text=VarName_CALI[i]).pack(fill=tk.X, side=tk.TOP)
                ttk.Entry(Frame_temp, textvariable=Var_CALI[i]).pack(
                    fill=tk.X, side=tk.TOP
                )
            ttk.Label(Frame_temp, text="输出文件命名").pack(fill=tk.X, side=tk.TOP)
            ttk.Entry(Frame_temp, textvariable=OutputName).pack(fill=tk.X, side=tk.TOP)
            return None

        def create_buttons(self):
            def Start_Output():
                if tk.messagebox.askyesno(
                    "输出提示",
                    "再次确认【标定系数】和【输出文件夹】是否正确，是否输出？",
                ):
                    if (
                        field_output.get()
                        or profile_output.get()
                        or statistics_output.get()
                    ):
                        DataOutput()
                        tk.messagebox.showinfo(message="输出完成")
                        self.master.destroy()
                    else:
                        tk.messagebox.showinfo(message="请选择至少一个选项进行输出")
                else:
                    self.master.lift()
                return None

            def Stop_Output():
                self.master.destroy()

            Frame_temp = tk.LabelFrame(self)
            Frame_temp.pack(fill=tk.X, side=tk.TOP)
            ttk.Button(Frame_temp, text="取消", command=Stop_Output).pack(
                fill=tk.X, side=tk.BOTTOM
            )
            ttk.Button(Frame_temp, text="输出", command=Start_Output).pack(
                fill=tk.X, side=tk.BOTTOM
            )
            return None

    # 数据输出函数
    def DataOutput():
        def Output_field():
            Var = (x, y, u0, v0)
            VarName = ("x [mm]", "y [mm]", "u [m/s]", "v [m/s]")
            if os.path.exists(
                os.path.join(PARAM.folder_output, OutputName.get() + "_field.dat")
            ):
                if tk.messagebox.askyesno(
                    "场域输出", "【场域输出】文件已存在，是否覆盖？"
                ):
                    SPEC.Tecplot_One_Zone(
                        PARAM.folder_output, OutputName.get() + "_field", Var, VarName
                    )
            else:
                SPEC.Tecplot_One_Zone(
                    PARAM.folder_output, OutputName.get() + "_field", Var, VarName
                )
            return None

        def Output_profile():
            Var = (y, np.mean(u0, axis=1), np.mean(v0, axis=1))
            VarName = ("y [mm]", "u [m/s]", "v [m/s]")
            if os.path.exists(
                os.path.join(PARAM.folder_output, OutputName.get() + "_profile.dat")
            ):
                if tk.messagebox.askyesno(
                    "剖面输出", "【剖面输出】文件已存在，是否覆盖？"
                ):
                    SPEC.Tecplot_Profile(
                        PARAM.folder_output, OutputName.get() + "_profile", Var, VarName
                    )
            else:
                SPEC.Tecplot_Profile(
                    PARAM.folder_output, OutputName.get() + "_profile", Var, VarName
                )
            return None

        def Output_statistic_picture():
            Image.fromarray(Im_mean_A).convert("RGB").save(
                os.path.join(PARAM.folder_output, OutputName.get() + "_Im_mean_A.bmp")
            )
            Image.fromarray(Im_mean_B).convert("RGB").save(
                os.path.join(PARAM.folder_output, OutputName.get() + "_Im_mean_B.bmp")
            )
            sigma_A0 = sigma_A / np.mean(sigma_A) * 255 / 2
            sigma_B0 = sigma_B / np.mean(sigma_B) * 255 / 2
            Image.fromarray(sigma_A0).convert("RGB").save(
                os.path.join(PARAM.folder_output, OutputName.get() + "_sigma_A.bmp")
            )
            Image.fromarray(sigma_B0).convert("RGB").save(
                os.path.join(PARAM.folder_output, OutputName.get() + "_sigma_B.bmp")
            )
            return None

        def Output_log():
            with open(
                PARAM.folder_output + "\\" + OutputName.get() + ".log", "w"
            ) as Output:
                for a in range(len(VarName_PARAM)):
                    Output.write(
                        "{0}\t{1}\n".format(VarName_PARAM[a], Var_PARAM[a].get())
                    )
                for a in range(len(VarName_ZONE)):
                    Output.write(
                        "{0}\t{1}\n".format(VarName_ZONE[a], Var_ZONE[a].get())
                    )
                for a in range(len(VarName_CALI)):
                    Output.write(
                        "{0}\t{1}\n".format(VarName_CALI[a], Var_CALI[a].get())
                    )
            return None

        save_initialization()
        PARAM.folder_output = folder_output.get()
        if not os.path.exists(PARAM.folder_output):
            os.makedirs(PARAM.folder_output)
        # 输出Tecplot剖面文件
        y = (
            np.arange(PARAM.numY) + (PARAM.yp - 1 - PARAM.y2)
        ) * scale.get()  # y坐标原点：图片最低点为原点0
        x = (np.arange(PARAM.numX) + PARAM.x1) * scale.get()  # x坐标
        u0 = u * scale.get() / dt.get()
        v0 = v * scale.get() / dt.get()
        if coordinate.get() == 2:
            x = (
                np.arange(PARAM.numX) + (PARAM.xp - 1 - PARAM.x2)
            ) * scale.get()  # x坐标
            u0 = -np.flip(u0, axis=1)
            v0 = np.flip(v0, axis=1)
        if field_output.get():  # 输出 Tecplot 场文件
            Output_field()
        if profile_output.get():  # 输出 Tecplot 剖面文件
            Output_profile()
        if statistics_output.get():
            Output_statistic_picture()
        Output_log()

        print("结果输出完成")
        return None

    if u is None:
        tk.messagebox.showinfo(message="还未进行分析")
    else:
        Output_Window = tk.Toplevel(root)
        Output_Window.title("结果输出")
        Output_Window.resizable(False, False)
        tmp = open("tmp.ico", "wb+")  # "wb+" 删除原有内容
        tmp.write(b64decode(icon_SPEC))
        tmp.close()
        Output_Window.iconbitmap("tmp.ico")
        os.remove("tmp.ico")  # 删除文件
        OutputFrames(Output_Window)
        Output_Window.mainloop()
    return None


if __name__ == "__main__":
    freeze_support()
    # 主窗口
    root = tk.Tk()
    root.geometry("1200x600+100+100")  # 大小和位置
    root.title("SPEC")  # 设置标题
    # icon 设置
    # 将import进来的icon.py里的数据转换成临时文件i.ico，作为图标
    tmp = open("tmp.ico", "wb+")  # "wb+" 删除原有内容
    tmp.write(b64decode(icon_SPEC))
    tmp.close()
    root.iconbitmap("tmp.ico")
    # 坐标系示意图导入
    tmp = open("tmp.ico", "wb+")  # "wb+" 删除原有内容
    tmp.write(b64decode(icon_right))
    tmp.close()  # 要先关闭，否则会占用文件无法后续的打开
    RHC = ImageTk.PhotoImage(file="tmp.ico")

    tmp = open("tmp.ico", "wb+")  # "wb+" 删除原有内容
    tmp.write(b64decode(icon_left))
    tmp.close()
    LHC = ImageTk.PhotoImage(file="tmp.ico")
    os.remove("tmp.ico")  # 删除文件

    # 图片设置
    image_show = None  # 需要显示的图片，因为必须要持续索引，所以要求为全局变量
    rectangle = None  # 需要显示的方形区域也是一样作为全局变量预先定义

    # 调用api设置成由应用程序缩放
    # 设置字体清晰
    # 原文链接：https://blog.csdn.net/qq_25921925/article/details/103987572
    windll.shcore.SetProcessDpiAwareness(1)
    # 调用api获得当前的缩放因子
    ScaleFactor = windll.shcore.GetScaleFactorForDevice(0)
    # 设置缩放因子
    root.tk.call("tk", "scaling", ScaleFactor / 65)

    # 将初始化参数信息、临时图像信息等保存在此文件夹内，并进行初始化
    folder_temp = r"C:\temp\SPEC"
    initialization()

    # 一些通信用的全局变量
    PARAM = None  # 分析信息存储
    u, v = None, None  # 分析结果存储
    sigma_A, sigma_B, Im_mean_A, Im_mean_B = None, None, None, None
    rollFrame = None  # 可滚动的 Frame
    progress = None
    output_text = None  # 信息输出栏
    preview_scale = tk.IntVar()  # 预览图像的尺寸比例
    preview_scale.set(1)
    Analysis_Progress = tk.StringVar()
    Analysis_Progress.set("准备开始计算")
    Analysis_Continuing = True  # 判断分析进程是否继续进行的变量 True 为正常执行

    # 输出参数
    coordinate = tk.IntVar()
    coordinate.set(1)  # 1、2 分别为右手和左手坐标系。
    field_output = tk.BooleanVar()  # 选择是否输出整场
    field_output.set(True)
    profile_output = tk.BooleanVar()  # 选择是否输出剖面
    profile_output.set(True)
    statistics_output = tk.BooleanVar()  # 选择是否输出平均量图片
    statistics_output.set(True)

    # 绘制所有窗口
    PrintFrames()
    # 图片统计
    root.mainloop()
