```python
import torch
import cv2
import numpy as np

# ------------ 输入 ------------
# corners: (3,8,3)  相机坐标系下 8 个角点
# K      : (3,3)    相机内参
# img_hw : (H,W)    原图尺寸，用来建一张黑底画布

corners = torch.tensor([
    [[ 3.0,  1.0,  5.0],   # 框 1 的 8 点
     [ 3.0,  1.0,  1.0],
     [ 3.0, -1.0,  1.0],
     [ 3.0, -1.0,  5.0],
     [ 1.0,  1.0,  5.0],
     [ 1.0,  1.0,  1.0],
     [ 1.0, -1.0,  1.0],
     [ 1.0, -1.0,  5.0]],
    # 框 2、3 同理……
], dtype=torch.float32)

K = torch.tensor([[721.5377, 0.0,      609.5593],
                  [0.0,      721.5377, 172.8540],
                  [0.0,      0.0,      1.0]], dtype=torch.float32)

H, W = 375, 1242
canvas = np.zeros((H, W, 3), dtype=np.uint8)

# ------------ 投影 ------------
def project(K, pts):
    # pts: (...,3)
    uv = torch.matmul(pts, K.T)          # (...,3)
    uv = uv[..., :2] / uv[..., 2:3]      # (...,2)
    return uv

uv = project(K, corners)                 # (3,8,2)

# ------------ 画线 ------------
edges = [(0,1),(1,2),(2,3),(3,0),
         (4,5),(5,6),(6,7),(7,4),
         (0,4),(1,5),(2,6),(3,7)]

colors = [(0,0,255), (0,255,0), (255,0,0)]  # 三个框不同颜色

for b in range(3):
    uvb = uv[b].numpy()
    for (i, j) in edges:
        pt1 = (int(uvb[i,0]), int(uvb[i,1]))
        pt2 = (int(uvb[j,0]), int(uvb[j,1]))
        cv2.line(canvas, pt1, pt2, colors[b], 1, cv2.LINE_AA)

cv2.imwrite('boxes_raw.png', canvas)
```

```python
import cv2
import numpy as np

# ------------------ 你的输入，直接引用 ------------------
# corners: (N, 8, 3)  相机坐标系下的 8 个角点
# K      : (3, 3)     相机内参
# (h, w) : 图像高、宽
# -----------------------------------------------------

# 固定 12 条边（每框 8 顶点→12 棱）
edges = [(0, 1), (1, 2), (2, 3), (3, 0),
         (4, 5), (5, 6), (6, 7), (7, 4),
         (0, 4), (1, 5), (2, 6), (3, 7)]

# 新建画布
canvas = np.zeros((h, w, 3), dtype=np.uint8)

# 投影
uv = (corners @ K.T)          # (N, 8, 3)
uv = uv[..., :2] / uv[..., 2:3]  # (N, 8, 2)

# 画框：随机颜色区分不同框
colors = np.random.randint(50, 255, (corners.shape[0], 3)).tolist()

for box_id, uvb in enumerate(uv.astype(int)):
    for i, j in edges:
        cv2.line(canvas, tuple(uvb[i]), tuple(uvb[j]), colors[box_id], 1, cv2.LINE_AA)

cv2.imwrite('boxes.png', canvas)   # 或 cv2.imshow(...)
```


```python
# corners_lidar  : (N,8,3)  原坐标系（例如 LiDAR）
T_cam_lidar = np.array([...], dtype=np.float64)  # 4×4
ones = np.ones((corners_lidar.shape[0], 8, 1))
corners_cam = (T_cam_lidar @ np.concatenate([corners_lidar, ones], axis=-1)[...,None])[..., :3, 0]

from scipy.spatial.transform import Rotation as Rsc

x,y,z,roll,pitch,yaw = ...            # 米 & 弧度
R = Rsc.from_euler('XYZ', [roll,pitch,yaw]).as_matrix()
t = np.array([[x,y,z]])               # (1,3)
corners_cam = corners_world @ R.T + t

print(corners_cam[0])        # 8 个点 x,y,z 应该都是相机坐标
print("z range:", corners_cam[...,2].min(), corners_cam[...,2].max())
```