# image-integrity-check — 图片完整性检查

## 用途
检测论文/报告中的图片是否存在 manipulation(拼接、克隆、擦除等)。通过 ELA(Error Level Analysis)误差分析识别异常区域,标注疑似位置,建议人工核查。

## 触发条件
- 论文配图交稿前检查图片完整性时。
- 怀疑某图片被篡改时。
- 用户提到"图片检查""ELA""图片完整性""manipulation"时。

## 工具依赖
```bash
pip install Pillow numpy
```

## 操作步骤
1. 输入待检查图片。
2. 做 ELA 分析:将图片以已知质量重新 JPEG 压缩,计算与原图的像素差异。
3. 正常区域差异均匀,被篡改区域差异异常(因篡改后重新压缩的误差模式不同)。
4. 识别异常区域,用热力图标注。
5. 输出标注图 + 异常区域坐标。
6. 标注"疑似 manipulation,建议人工核查"。

## 调用示例
```python
from PIL import Image
import numpy as np

def ela_analysis(image_path, quality=90):
    """Error Level Analysis"""
    original = Image.open(image_path).convert("RGB")

    # 重新压缩
    temp_path = "ela_temp.jpg"
    original.save(temp_path, "JPEG", quality=quality)
    recompressed = Image.open(temp_path).convert("RGB")

    # 计算像素差异
    arr_orig = np.array(original, dtype=np.int16)
    arr_recomp = np.array(recompressed, dtype=np.int16)
    diff = np.abs(arr_orig - arr_recomp)

    # 放大差异便于可视化
    diff_scaled = np.clip(diff * 20, 0, 255).astype(np.uint8)
    ela_image = Image.fromarray(diff_scaled)

    # 识别异常区域(差异远高于均值)
    diff_gray = diff.mean(axis=2)
    threshold = diff_gray.mean() + 3 * diff_gray.std()
    anomaly_mask = diff_gray > threshold
    anomaly_ratio = anomaly_mask.sum() / anomaly_mask.size

    print(f"异常区域占比: {anomaly_ratio:.4f}")
    if anomaly_ratio > 0.01:  # 超过 1% 区域异常
        print("⚠️ 检测到疑似 manipulation 区域,建议人工核查")

    # 标注异常区域
    marked = np.array(original).copy()
    marked[anomaly_mask] = [255, 0, 0]  # 红色标注
    marked_img = Image.fromarray(marked)

    return ela_image, marked_img, anomaly_ratio

ela_img, marked_img, ratio = ela_analysis("figure.png")
ela_img.save("ela_result.png")
marked_img.save("ela_marked.png")
```

## 输出格式
- ELA 差异图(`ela_result.png`)。
- 异常区域标注图(`ela_marked.png`,红色标注疑似区域)。
- 异常区域占比数值。

## 约束
- 只标注"疑似",不单独判定造假,最终结论需人工核查。
- ELA 对原生高压缩率图片可能误报,需结合噪声分析综合判断。
- 不输出"图片造假"这类定论性表述。
