# -*- coding:utf-8 -*-
"""
并行单像素互相关程序说明：
分块并行：由于互相关矩阵过大将爆内存, 需要分块进行互相关操作, 按照法向位置分成多个横向长条区域
分块依据：互相关矩阵R数据个数不能超过某个最大值数据, 与【计算机内存】、【并行核数】有关
并行过程：每个核分组单独导入图片, 并求和、输出互相关矩阵
→对硬盘要求较高，需要较高的数据传输速度

总结：
依据目前认知：
1、CPU占用率越高，计算速度越高, 但8核以上计算效率随着核数增多, 计算速度并不会有非常大的提升（信息传递导致）
2、8核以上时，RAM越高，计算速度越高
"""

import numpy as np
from time import time
from PIL import Image
from multiprocessing import Pool
import os


# 定义一个类作为参数
class SPEC_Parameters(object):
    def __init__(
        self,
        RAM,
        process_num,
        n,
        width,
        height,
        xp,
        yp,
        x1,
        x2,
        y1,
        y2,
        folder_input,
        folder_output,
    ):
        # 内存与计算效率
        self.RAM = RAM
        self.process_num = process_num

        # 计算参数
        self.n = n
        self.width2, self.height2 = int(width / 2), int(height / 2)  # 查询窗口的一半
        self.width = self.width2 * 2 + 1  # 查询窗口宽度
        self.height = self.height2 * 2 + 1  # 查询窗口高度

        # 计算区域初始化，如果给定数字超出范围，设置为边界值
        if y1 - self.height2 < 0 or y1 + self.height2 > yp - 1:
            y1 = self.height2
        if y2 + self.height2 > yp - 1 or y2 <= y1:
            y2 = yp - self.height2 - 1
        if x1 - self.width2 < 0 or x1 + self.width2 > xp - 1:
            x1 = self.width2
        if x2 + self.width2 > xp - 1 or x2 <= x1:
            x2 = xp - self.width2 - 1
        self.xp, self.yp = xp, yp
        self.x1, self.x2, self.y1, self.y2 = x1, x2, y1, y2
        self.numX = x2 - x1 + 1  # x数量
        self.numY = y2 - y1 + 1  # y数量

        # 文件夹设置
        self.folder_input = folder_input
        self.folder_output = folder_output
        # 列出文件夹内 BMP 文件名
        self.listing = [a for a in os.listdir(folder_input) if a.endswith(".bmp")]


# 本程序中的类给定，不同的程序可以设置不同的参数类
def init():
    # 内存相关
    RAM = 64  # 电脑内存量(GB), 用于计算建议内存
    process_num = 16  # 1为串行运行, 不启用并行池

    # 计算参数
    n = 2000  # 共导入 2*n 张图片
    width, height = 65, 13  # 查询窗口大小

    # 图像区域参数
    xp = 2048  # 像素个数
    yp = 2048  # 像素个数
    # 注意：图像竖直方向上与图像像素坐标是相反的, 因此索引越大位置越低
    x1 = 800
    x2 = 1000
    y1 = 100  # 互相关【中心】位置, y 最高坐标像素索引
    y2 = 1971  # 互相关【中心】位置, y 最低坐标像素索引

    # 文件夹初始化
    folder_input = r"E:\HighV_test2\picture\50Hz_1"
    folder_output = r"E:\HighV_test2\Output\50Hz_1\SPEC"  # 输出文件夹

    SPEC_PARAM = SPEC_Parameters(
        RAM,
        process_num,
        n,
        width,
        height,
        xp,
        yp,
        x1,
        x2,
        y1,
        y2,
        folder_input,
        folder_output,
    )
    return SPEC_PARAM


# 导入一对图片
def input_picture(PARAM, picture_number):
    Im_A = np.array(
        Image.open(
            os.path.join(PARAM.folder_input, PARAM.listing[2 * picture_number])
        ).convert("L"),
        "f",
    )
    Im_B = np.array(
        Image.open(
            os.path.join(PARAM.folder_input, PARAM.listing[2 * picture_number + 1])
        ).convert("L"),
        "f",
    )
    return Im_A, Im_B


# 图片求和池
def sum_pool(PARAM, process_delay):
    Im_sum_A, Im_sum_B = np.zeros((PARAM.yp, PARAM.xp)), np.zeros((PARAM.yp, PARAM.xp))
    for a in range(process_delay, PARAM.n, PARAM.process_num):  # 时间帧范围
        Im_A, Im_B = input_picture(PARAM, a)
        Im_sum_A += Im_A
        Im_sum_B += Im_B
    return Im_sum_A, Im_sum_B


# 图片方差求和池
def sigma_sum_pool(PARAM, Im_mean_A, Im_mean_B, process_delay):
    sigma_A, sigma_B = np.zeros((PARAM.yp, PARAM.xp)), np.zeros((PARAM.yp, PARAM.xp))
    for a in range(process_delay, PARAM.n, PARAM.process_num):  # 时间帧范围
        Im_A, Im_B = input_picture(PARAM, a)
        sigma_A += (Im_A - Im_mean_A) ** 2
        sigma_B += (Im_B - Im_mean_B) ** 2
    return sigma_A, sigma_B


# 进行并行统计计算的函数
def statistics_parallel(PARAM, choose=0):
    if (
        not os.path.exists(os.path.join(PARAM.folder_output, "Im_mean_A.npy"))
        or choose == 0
    ):
        Im_mean_A, Im_mean_B = np.zeros((PARAM.yp, PARAM.xp)), np.zeros(
            (PARAM.yp, PARAM.xp)
        )
        sigma_A, sigma_B = np.zeros((PARAM.yp, PARAM.xp)), np.zeros(
            (PARAM.yp, PARAM.xp)
        )
        pool = Pool(processes=PARAM.process_num)
        for result in pool.starmap(
            sum_pool, [(PARAM, a) for a in range(PARAM.process_num)]
        ):
            Im_mean_A += result[0]
            Im_mean_B += result[1]
        pool.close()
        pool.join()
        Im_mean_A /= PARAM.n
        Im_mean_B /= PARAM.n
        print("平均完成")
        pool = Pool(processes=PARAM.process_num)
        for result in pool.starmap(
            sigma_sum_pool,
            [(PARAM, Im_mean_A, Im_mean_B, a) for a in range(PARAM.process_num)],
        ):
            sigma_A += result[0]
            sigma_B += result[1]
        pool.close()
        pool.join()

        # 消除0, 防止nan
        tempA = np.mean(sigma_A)  # 用平均值将 0 代替掉
        tempB = np.mean(sigma_B)
        for a in range(np.size(sigma_A, 0)):
            for b in range(np.size(sigma_A, 1)):
                if sigma_A[a, b] == 0:
                    sigma_A[a, b] = tempA
                if sigma_B[a, b] == 0:
                    sigma_B[a, b] = tempB
        sigma_A = np.sqrt(sigma_A / (PARAM.n - 1))
        sigma_B = np.sqrt(sigma_B / (PARAM.n - 1))

        # 保存变量
        # np.save(os.path.join(PARAM.folder_output, "sigma_A.npy"), sigma_A)
        # np.save(os.path.join(PARAM.folder_output, "sigma_B.npy"), sigma_B)
        # np.save(os.path.join(PARAM.folder_output, "Im_mean_A.npy"), Im_mean_A)
        # np.save(os.path.join(PARAM.folder_output, "Im_mean_B.npy"), Im_mean_B)
        # Image.fromarray(Im_mean_A).convert("RGB").save(
        #     os.path.join(PARAM.folder_output, "Im_mean_A.png")
        # )
        # Image.fromarray(Im_mean_B).convert("RGB").save(
        #     os.path.join(PARAM.folder_output, "Im_mean_B.png")
        # )
    else:
        sigma_A = np.load(os.path.join(PARAM.folder_output, "sigma_A.npy"))
        sigma_B = np.load(os.path.join(PARAM.folder_output, "sigma_B.npy"))
        Im_mean_A = np.load(os.path.join(PARAM.folder_output, "Im_mean_A.npy"))
        Im_mean_B = np.load(os.path.join(PARAM.folder_output, "Im_mean_A.npy"))
    return sigma_A, sigma_B, Im_mean_A, Im_mean_B


# 寻找互相关峰值
def peak_uv(PARAM, R, sigma_A, sigma_B, numYb, choose=1):
    def peak_uv_single(R0):
        u0, v0 = 0, 0
        loc = np.argwhere(R0.max() == R0)
        xx = loc[0][1]
        yy = loc[0][0]
        if xx == 0 or xx == PARAM.width - 1 or yy == 0 or yy == PARAM.height - 1:
            dxx, dyy = 0, 0
        elif choose == 0:
            # Gauss函数拟合方法
            if np.min(R0[yy - 1 : yy + 2, xx]) > 0:
                dyy = (np.log(R0[yy - 1, xx]) - np.log(R0[yy + 1, xx])) / (
                    2
                    * (
                        np.log(R0[yy + 1, xx])
                        - 2 * np.log(R0[yy, xx])
                        + np.log(R0[yy - 1, xx])
                    )
                )
            else:
                dyy = 0
            if np.min(R0[yy, xx - 1 : xx + 2]) > 0:
                dxx = (np.log(R0[yy, xx - 1]) - np.log(R0[yy, xx + 1])) / (
                    2
                    * (
                        np.log(R0[yy, xx + 1])
                        - 2 * np.log(R0[yy, xx])
                        + np.log(R0[yy, xx - 1])
                    )
                )
            else:
                dxx = 0
        elif choose == 1:
            # 二次函数拟合方法
            dxx = (R0[yy, xx - 1] - R0[yy, xx + 1]) / (
                2 * (R0[yy, xx + 1] - 2 * R0[yy, xx] + R0[yy, xx - 1])
            )
            dyy = (R0[yy - 1, xx] - R0[yy + 1, xx]) / (
                2 * (R0[yy + 1, xx] - 2 * R0[yy, xx] + R0[yy - 1, xx])
            )
        else:
            raise ValueError("峰值插值方法错误, choose 只能选择0/1")

        # 以中心为原点，找出对应位置的x、y坐标值
        rxx = xx + dxx - PARAM.width2
        ryy = yy + dyy - PARAM.height2
        v0 = ryy
        u0 = rxx
        return u0, v0

    print("寻找速度...")
    u = np.zeros((numYb, PARAM.numX))
    v = np.zeros((numYb, PARAM.numX))
    for a in range(numYb):
        for b in range(PARAM.numX):
            R1 = (
                R[a, b]
                / (
                    sigma_A[a + PARAM.height2, b + PARAM.width2]
                    * sigma_B[a : a + PARAM.height, b : b + PARAM.width]
                )
                / (PARAM.n - 1)
            )
            u[a, b], v[a, b] = peak_uv_single(R1)
    return u, v


# 互相关求和池
def correlation_pool(
    PARAM,
    Im_mean_A,
    Im_mean_B,
    y1b,
    y2b,
    process_delay,
    process_description,
):
    numYb = y2b - y1b + 1
    R = np.zeros((numYb, PARAM.numX, PARAM.height, PARAM.width))
    for a in range(process_delay, PARAM.n, PARAM.process_num):  # 时间帧范围
        if a % 100 == 0:
            print("%s: %d/%d" % (process_description, a, PARAM.n))
        Im_A, Im_B = input_picture(PARAM, a)
        Im_A -= Im_mean_A
        Im_B -= Im_mean_B
        Im_A = Im_A[
            y1b - PARAM.height2 : y2b + PARAM.height2 + 1,
            PARAM.x1 - PARAM.width2 : PARAM.x2 + PARAM.width2 + 1,
        ]
        Im_B = Im_B[
            y1b - PARAM.height2 : y2b + PARAM.height2 + 1,
            PARAM.x1 - PARAM.width2 : PARAM.x2 + PARAM.width2 + 1,
        ]
        for b in range(numYb):
            for c in range(PARAM.numX):
                R[b, c] += (
                    Im_A[b + PARAM.height2, c + PARAM.width2]
                    * Im_B[b : b + PARAM.height, c : c + PARAM.width]
                )
    return R


# 小区域 SPEC
def correlation_small_field(
    PARAM, sigma_A, sigma_B, Im_mean_A, Im_mean_B, y1b, y2b, process_description
):
    numYb = y2b - y1b + 1
    # 开始互相关运算
    R = np.zeros((numYb, PARAM.numX, PARAM.height, PARAM.width))
    pool = Pool(processes=PARAM.process_num)
    for R0 in pool.starmap(
        correlation_pool,
        [
            (PARAM, Im_mean_A, Im_mean_B, y1b, y2b, a, process_description)
            for a in range(PARAM.process_num)
        ],
    ):
        R += R0
    pool.close()
    pool.join()

    # 寻找峰值
    u, v = peak_uv(
        PARAM,
        R,
        sigma_A[y1b - PARAM.height2 : y2b + PARAM.height2 + 1, :],
        sigma_B[y1b - PARAM.height2 : y2b + PARAM.height2 + 1, :],
        numYb,
    )
    return u, v


# 合并区域 SPEC
def correlation_integration(PARAM, sigma_A, sigma_B, Im_mean_A, Im_mean_B):
    """
    :param sigma_A: A帧标准差
    :param sigma_B: B帧标准差
    :param Im_mean_A: 所有 A 帧图片的平均值
    :param Im_mean_B: 所有 B 帧图片的平均值
    :return: 平均速度场 u,v
    """
    # 通过设计最大数据量 2**25 * RAM * utilization / process_num 估计分块block数目
    # 先算出总像素数量，再除以总内存对应的像素数量(最大数据量)，就是分块数
    numBlock = (
        int(
            (PARAM.numY + PARAM.height)  # 图像纵向像素数量
            * (PARAM.numX + PARAM.width)  # 图像横向像素数量
            * PARAM.height  # 互相关纵向像素数量
            * PARAM.width  # 互相关横向像素数量
            / (2**25 * PARAM.RAM * PARAM.utilization / PARAM.process_num)
        )
        + 1
    )
    numYb = (
        int(PARAM.numY / numBlock) + 1
    )  # 每个分块的y坐标个数 (小于分块纵向像素点个数)
    while (numYb + 2 * PARAM.height2) * (
        PARAM.numX + 2 * PARAM.width2
    ) * PARAM.width * PARAM.height > 2**24 * PARAM.RAM * PARAM.utilization / PARAM.process_num:
        numBlock += 1
        numYb = int(PARAM.numY / numBlock) + 1
    # 图片由上至下进行分块分析
    y1b = PARAM.y1  # 当前块的 上侧中心位置的y索引
    y2b = y1b + numYb - 1  # 当前块的 下侧中心位置的y索引
    u, v = np.zeros((PARAM.numY, PARAM.numX)), np.zeros((PARAM.numY, PARAM.numX))
    for a in range(numBlock - 1):
        process_description = "区域%d/%d" % (a + 1, numBlock)
        print(process_description)
        start = time()
        print(
            "分块法向像素点数: %d\n上边界索引: %d\n下边界索引: %d" % (numYb, y1b, y2b)
        )
        (
            u[y1b - PARAM.y1 : y2b - PARAM.y1 + 1],
            v[y1b - PARAM.y1 : y2b - PARAM.y1 + 1],
        ) = correlation_small_field(
            PARAM,
            sigma_A,
            sigma_B,
            Im_mean_A,
            Im_mean_B,
            y1b,
            y2b,
            process_description,
        )
        end = time()
        print("区域完成, 用时 %.1f s\n" % (end - start))
        y1b += numYb
        y2b += numYb
    if numBlock > 1:
        process_description = "区域%d/%d" % (numBlock, numBlock)
        print(process_description)
        numYb = PARAM.y2 - y1b + 1
        print(
            "分块法向像素点数: %d\n上边界索引: %d\n下边界索引: %d" % (numYb, y1b, y2b)
        )
        (
            u[y1b - PARAM.y1 : PARAM.y2 - PARAM.y1 + 1],
            v[y1b - PARAM.y1 : PARAM.y2 - PARAM.y1 + 1],
        ) = correlation_small_field(
            PARAM,
            sigma_A,
            sigma_B,
            Im_mean_A,
            Im_mean_B,
            y1b,
            PARAM.y2,
            process_description,
        )
    u = np.flip(u, axis=0)
    v = np.flip(v, axis=0)
    print(u.shape)
    return u, v


def main():
    # 初始化
    scale = 0.0372246  # 标定系数 [mm/pixel]
    dt = 0.75e-3  # 两帧图像的时间间隔 [s]
    PARAM = init()  # 初始化类

    # 数据准备
    print("\n数据准备...")
    start = time()
    sigma_A, sigma_B, Im_mean_A, Im_mean_B = statistics_parallel(PARAM)
    end = time()
    print("统计数据用时%.1f s" % (end - start))

    # 互相关运算：
    print("\n%d核并行=\n互相关开始...\n" % (PARAM.process_num))
    start = time()
    u, v = correlation_integration(PARAM, sigma_A, sigma_B, Im_mean_A, Im_mean_B)
    u = u * scale / dt * 1000
    v = v * scale / dt * 1000
    end = time()
    print("SPEC计算用时 %.1f s" % (end - start))

    # 输出Tecplot剖面文件
    y = (
        np.arange(PARAM.numY) + (PARAM.yp - 1 - PARAM.y2)
    ) * scale  # y坐标原点：图片最低点为原点0
    x = np.linspace(0, PARAM.numX - 1, PARAM.numX) * scale  # x坐标

    OutputName = "SPEC_profile_%d" % PARAM.n
    Var = (y, np.mean(u, axis=1), np.mean(v, axis=1))
    VarName = ("y [mm]", "u [m/s]", "v [m/s]")
    Tecplot_Profile(PARAM.folder_output, OutputName, Var, VarName)

    OutputName = "SPEC_field_%d" % PARAM.n
    Var = (x, y, u, v)
    VarName = ("x [mm]", "y [mm]", "u [m/s]", "v [m/s]")
    print(x.shape, y.shape, u.shape, v.shape)
    Tecplot_One_Zone(PARAM.folder_output, OutputName, Var, VarName)


# tecplot 输出函数
def Tecplot_Profile(folder_output, OutputName, Var, VarName):
    # 输出
    # 坐标准备
    x = Var[0]
    numVar = len(Var)
    if numVar != len(VarName):
        raise ValueError("profile输出：变量名与变量数量不相等")
    elif numVar == 1:
        raise ValueError("profile输出：变量只有一个")

    with open(folder_output + "\\" + OutputName + ".dat", "w") as Output:
        Output.write('TITLE="{0}"\nVARIABLES='.format(OutputName))
        for a in VarName:
            Output.write(' "{0}"'.format(a))
        Output.write("\n")
        numX = len(x)
        Output.write('ZONE T="profile", I={0}, F=POINT\n'.format(numX))
        for a in range(numX):
            Output.write("{:e}".format(x[a % numX]))
            for b in range(numVar - 1):
                Output.write("\t{:e}".format(Var[b + 1][a]))
            Output.write("\n")
    return None


def Tecplot_One_Zone(
    folder_output, OutputName, Var, VarName, ZoneName="Zone 0", solutiontime=0, choose=0
):
    """
    choose=0表示结构化网格
    choose=1表示散点网格
    """
    # 坐标准备
    x = Var[0]
    y = Var[1]
    numVar = len(Var)
    if numVar != len(VarName):
        raise ValueError("变量名与变量数量不相等")

    # 开始输出
    with open(folder_output + "\\" + OutputName + ".dat", "w") as Output:
        Output.write('TITLE="{0}"\nVARIABLES='.format(OutputName))
        for i in range(numVar):
            Output.write(' "{0}"'.format(VarName[i]))
        Output.write("\n")
        if choose == 0:  # 结构化网格
            numY, numX = np.shape(Var[2])
            if numX != len(Var[0]):
                raise ValueError("Tecplot输出：横坐标网格数目不正确")
            elif numY != len(Var[1]):
                raise ValueError("Tecplot输出：纵坐标网格数目不正确")
            Output.write(
                'ZONE T="zone 1", I={0}, J={1}, F=POINT\nSolutiontime={2}\n'.format(
                    numX, numY, solutiontime
                )
            )
            for i in range(numY):
                for j in range(numX):
                    Output.write("{:e}".format(x[j]))
                    Output.write("\t{:e}".format(y[i]))
                    for k in range(2, numVar):
                        Output.write("\t{:e}".format(Var[k][i, j]))
                    Output.write("\n")
        elif choose == 1:  # 散点网格
            numN = len(Var[2])
            Output.write('ZONE T="{0}",I={1},J=1,F=POINT\n'.format(ZoneName, numN))
            for i in range(numN):
                for j in range(numVar):
                    Output.write("{:e}\t".format(Var[j][i]))
                Output.write("\n")
    return None


if __name__ == "__main__":
    main()
