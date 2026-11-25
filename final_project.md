## 大作业
- 任务：基于给定数据完成新颖视角合成(NVS) 任务，
进行技术调研、算法实现、提交在线评估系统打分
- 组队：最多3 人一组
- 时间：
  - 实现：11月12日- 12 月22 日，11 月22 日起提供计算资源
  - 展示：最后两周课
  - 验收：最后两周实验课
- 评分：定量评价+ 汇报展示，占总分30%
  - 定量评价（15分）：提供在线评估系统，见说明文档
  - 汇报展示（15分）：表达是否清晰、调研是否充分、方法是否创新

## 任务：新视角合成
给定一组多视角图像，重建出场景的三维结构（3D点云、相机位 姿、3D高斯表达等），并渲染出指定新视角下的RGB 图像。

## 数据说明
- 训练：50 张已知内参的图片和其中一对图片的相对位姿
  - 相对位姿：确定世界坐标系（定义世界中心帧）并提供尺度信息
- 测试：20 张测试图片对应的内参和外参
  - 测试图片位姿与训练集提供的处于同一世界坐标系
- 提交：20 张渲染出的测试RGB 图像

## 测评说明
- 定量评价：将对上传的20 张测试RGB 图像和ground truth 图像计算PSNR / SSIM / LPIPS 指标，综合三项排 名并根据班级总体完成程度给分
  - PSNR (峰值信噪比)↑：衡量渲染图像与真实图像的像素差异
  - SSIM (结构相似性) ↑：衡量图像在亮度、对比度和结构上的相似程度
  - LPIPS (感知相似度) ↓：利用深度网络特征衡量两张图像的视觉感知差异
- 提交方式：提交渲染图片到在线评估系统打分，11.22 提供计算资源时一并提供，基础逻辑为
  - 通过ssh 上传文件到指定位置
  - 通过自动评估脚本调用评估返回结果并更新到任务榜单

## 思路
- 方案探索：不同的三维表示和渲染方式
  - COLMAP 求解点云+ 相机位姿，再接3DGS 重建场景
  - Feed-forward 重建模型直接预测位姿、3DGS 表征
  - 图像/视频生成模型直接生成新视角图像
  - ……

## 思路1：COLMAP + 3DGS
基本实现：利用COLMAP 对给定的训练多视角图片进行位 姿标定和点云重建，利用SfM 稀疏点云初始化训练3DGS， 然后渲染测试视角
进阶探索：更准的相机位姿标定提升位姿精度，更强的 3DGS 建模方法得到更好的场景建模等。
- https://github.com/cvg/Hierarchical-Localization, 定位
- https://github.com/graphdeco-inria/gaussian-splatting, 3DGS

## 思路2：Feed-Forward Model
基本实现：调研feed-forward 重建模型，输入一组多视角 图片，通过一个神经网络得到显式（3DGS, …）或者隐式 （latent,…）的场景建模表达，根据建模表达选取渲染方式 渲染出对应的测试视角图片
思考探索：如何使用给定的相机参数，尝试不同的feedforward 重建模型，探索显式/隐式的场景表达和渲染方式
- https://github.com/cvg/yonosplat, 显示三维表达
- https://github.com/cvg/resplat, 显式三维表达
- https://hwjiang1510.github.io/RayZer/, 隐式三维表达

## 思路3：X + Generative Model
基本实现：提供输入多视角图片和某种形式的condition， 利用图像/视频生成模型来直接渲染指定的测试视角图片。
Condition 形式探索：使用大语言模型直接建模3D 场景的 Mesh 网格，或者使用feed-forward 模型得到场景点云
- https://openai.com/index/gpt-6-astra/, LLM
- https://github.com/MiniMax-AI/MiniMax-H3, 视频生成模型
- https://github.com/nv-tlabs/GEN3C, 点云conditioned 视频生成模型
- https://github.com/bytedance-seed/depth-anything-3, feed-forward 点云/深度重建