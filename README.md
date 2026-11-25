# Computer Vision 2026 大作业

使用 50 张训练 RGB、相机内参及两个锚点的相对位姿重建场景，生成给定 20 个测试相机下的 RGB 图像。

## 当前可以做什么

**本次先发布作业数据和评测协议，训练服务器账号与在线提交方式后续另行通知。**
现在可以在自己的设备上完成重建、训练、渲染和预测图片校验，不需要服务器账号。

1. 阅读 [任务与数据说明](docs/task.md)，确认相机坐标系、内参及两个锚点的变换方向。
2. 使用 `data/train/` 的公开输入开展实验。
3. 按 `data/test/cameras.json` 的每个目标相机及其 K 生成预测，保存到 `predictions/`。
4. 阅读 [提交与排名规则](docs/submission.md)，执行本地校验；账号开通后再上传评测。

## 文件结构

```text
cv2026-assignment-v1/
├── README.md
├── submit.py                 # 现在本地校验；开通后上传和查询
├── data/
│   ├── train/
│   │   ├── rgb/              # 000001.png–000050.png
│   │   ├── cameras.json      # 逐图内参
│   │   └── anchors.json      # 两个锚点及相对位姿
│   └── test/
│       ├── cameras.json      # 逐图 K、尺寸、c2w、w2c
│       └── test_names.txt    # 000001.png–000020.png
├── docs/
│   ├── task.md               # 任务、数据和坐标系
│   └── submission.md         # 图片要求、alias、评测和排名
├── tools/
│   ├── submission.json       # 冻结的数据与评测配置
│   └── checksums.sha256      # 文件完整性校验
└── predictions/              # 初始为空，放预测图片
```

训练和测试分别按 `{id:06d}.png` 编号；训练的 `000001.png` 与测试目标的 `000001.png` 是不同视角。
两个锚点是**训练**图 `000001.png`、`000002.png`，第一张的相机坐标系就是世界坐标系。全部测试位姿与锚点同坐标系、同尺度。
每个测试目标的 K 单独给出，不要用一个固定 K 替代所有视角。

## 本地检查预测图片

目录必须只包含指定的 20 张 **768×432、8-bit RGB PNG**，单张不超过 4 MiB，总量不超过 32 MiB。
需要 Python 3.10+，无需 pip 安装，执行：

```bash
# 将示例别名替换为本组实际别名
python3 submit.py --images ./predictions --alias "本组选择的别名" --check-only
```

这个命令不需要账号、不连接网络、不绑定别名，也不计算指标。
在线提交开放后，每次新提交必须显式指定 alias；首次有效提交被接收后永久绑定。
榜单使用各组最新成功提交，PSNR/SSIM 排名从高到低、LPIPS 从低到高，三个单项名次等权平均，综合分越低越好。完整细则见 [提交与排名规则](docs/submission.md)。

本包不含测试 RGB 真值、参考点云、其余训练相机的参考外参、服务器私钥或登录密码。
数据协议为 `cv2026_train50_test20_v3`，与目前服务器评测一致；本次整理不改变图像、内参、位姿、测试划分或评分规则。

可在材料包根目录执行 `sha256sum -c tools/checksums.sha256` 检查文件完整性。
