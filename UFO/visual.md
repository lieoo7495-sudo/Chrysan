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