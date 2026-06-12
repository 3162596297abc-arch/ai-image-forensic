from PIL import Image
import numpy as np

input_path = r"E:\ai-image-forensic\背景素材\image.jpg"
output_path = r"E:\ai-image-forensic\机器人.png"

img = Image.open(input_path).convert("RGBA")
data = np.array(img)

# 纯黑背景阈值: R<30, G<30, B<30 视为背景
black_mask = (data[:, :, 0] < 30) & (data[:, :, 1] < 30) & (data[:, :, 2] < 30)

# 把黑色背景像素设为透明
data[black_mask, 3] = 0

result = Image.fromarray(data, "RGBA")
result.save(output_path, "PNG")
print(f"Done: {output_path}")
print(f"Size: {result.size}, Mode: {result.mode}")
