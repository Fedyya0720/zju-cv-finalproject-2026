# 大作业任务与数据说明

用 50 张训练 RGB、逐图内参和两个锚点的相对位姿重建场景，再在给定的 20 个测试相机下生成 RGB 图片。
可以使用优化型重建、前馈重建或其他课程允许的方法，所有方法使用相同输入和评测协议。

## 图片编号与文件对应

| 路径（相对于材料包根目录） | 内容 |
|---|---|
| `data/train/rgb/000001.png`–`000050.png` | 50 张训练 RGB，768×432 |
| `data/train/cameras.json` | 每张训练图的 `name`、`image_file`、`K` 和尺寸；不提供完整训练外参 |
| `data/train/anchors.json` | 两个锚点、两个方向的相对变换和基线 |
| `data/test/cameras.json` | 每个测试目标的 `name`、`K`、尺寸、`c2w`、`w2c` |
| `data/test/test_names.txt` | 必须生成的 `000001.png`–`000020.png` |

训练、测试分别从 `000001` 连续编号，文件名格式为 `{id:06d}.png`。两套编号独立：训练 `000001.png` 和测试目标 `000001.png` 是不同视角，分别由 `data/train/`、`data/test/` 区分。**按 `name` 字段关联图片、内参和位姿，不要依赖列表下标或自己排序后配对。** 编号不代表时间间隔。
JSON 中 `image_file` 相对于 `data/`，例如 `train/rgb/000001.png`。
测试的 `test/rgb/000001.png` 仅为目标标识；学生包不提供测试 RGB 真值。

本版数据标识为 `cv2026_train50_test20_v3`，本次公开发布包为 cv2026-assignment-v1。图片内容、相机参数、坐标系、尺度和评测公式与上一版相同，仅重新编号并补充说明。
**必须使用新版文件名提交；旧版原始帧编号或带 train_/test_ 前缀的文件名会被拒绝。**

## 两个锚点与世界坐标系

| 锚点 | 训练图片 | 定义 |
|---|---|---|
| `anchor0` | `000001.png` | 该相机坐标系就是世界坐标系；`c2w = I` |
| `anchor1` | `000002.png` | 通过给定相对位姿，确定另一台相机的位置、方向和基线尺度 |

世界原点是 `000001.png` 相机的光心；世界轴与该相机的轴重合。
使用 **OpenCV 坐标约定：x 向右、y 向下、z 向前**，4×4 齐次矩阵左乘列向量。

统一记号：`T_A_from_B` 将 **B 坐标系下的点坐标变换到 A 坐标系**。
`anchors.json` 提供两个方向：

```text
X_anchor0 = T_anchor0_from_anchor1 @ X_anchor1
X_anchor1 = T_anchor1_from_anchor0 @ X_anchor0

T_anchor1_from_anchor0 = inverse(T_anchor0_from_anchor1)
```

因此 `T_anchor0_from_anchor1` 表示 **000002 相机在 000001 坐标系下的位姿**。
因为世界坐标系就是 anchor0：

```text
000001 的 c2w = T_world_from_anchor0 = I
000002 的 c2w = T_world_from_anchor1 = T_anchor0_from_anchor1
```

`c2w` 的右上角三维平移向量表示相机光心在世界坐标系下的位置。
基线约为 **2.982204877109437**，单位是 SfM 任意尺度，**不是米**。
反向变换必须对整个矩阵求逆；不能只把平移取负。
其余 48 张训练图的参考外参不提供，需要自行估计。

## 测试相机：统一坐标系与内参

**全部 20 个测试相机与两个锚点使用同一个世界坐标系和相同尺度。**
`data/test/cameras.json` 的 `cameras` 列表中，每个目标都有自己的完整 `K`、`width`、`height`、`c2w` 和 `w2c`：

```text
X_world  = c2w @ X_camera
X_camera = w2c @ X_world
w2c      = inverse(c2w)

K = [[fx,  0, cx],
     [ 0, fy, cy],
     [ 0,  0,  1]]
```

`K` 以处理后图像的像素为单位。各帧内参可能不同，**每个测试视角都必须使用自己对应的 K**。
图像已去畸变、裁剪和缩放为 768×432；K 已同步调整，畸变系数为零。不要重复去畸变，也不要沿用原始图像的 K。

在材料包根目录读取某个测试相机，例如：

```python
import json
import numpy as np

with open("data/test/cameras.json", encoding="utf-8") as f:
    cameras = {c["name"]: c for c in json.load(f)["cameras"]}
camera = cameras["000001.png"]
K = np.asarray(camera["K"])
c2w = np.asarray(camera["c2w"])
w2c = np.asarray(camera["w2c"])
# 用该 K 和位姿渲染 768×432 RGB，保存为 predictions/000001.png
```

自行重建产生的坐标系通常不同，需要根据锚点对齐旋转、平移和统一尺度，并对场景及训练相机应用一致变换，再用给定测试相机渲染。
若方法内部使用 OpenGL 等其他相机轴约定，还需要进行一致的坐标转换。
不提供参考点云；不得用测试真值进行配准、曝光调整或相机优化。

下一步：[提交与排名规则](submission.md) · [返回入口](../README.md)
