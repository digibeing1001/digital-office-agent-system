# image-forensics — 图片取证

## 用途
图片 manipulation 取证检测。综合 ELA 误差分析、噪声分析、元数据检查多维度手段,标注图片中的异常区域,为图片完整性判断提供证据。与 image-integrity-check 互补,本技能侧重多维度综合取证。

## 触发条件
- 需要对图片做深度取证分析时。
- 图片完整性检查发现异常,需进一步取证时。
- 用户提到"图片取证""forensics""篡改检测"时。

## 工具依赖
```bash
pip install Pillow numpy
```

## 操作步骤
1. ELA 误差分析:检测不同区域的压缩痕迹差异。
2. 噪声分析:估计噪声模式,篡改区域噪声模式通常异常。
3. 元数据检查:读取 EXIF,看是否有编辑软件痕迹、时间戳矛盾。
4. 综合多维度结果,标注异常区域。
5. 输出取证报告,标注"疑似,建议人工核查"。

## 调用示例
```python
from PIL import Image, ExifTags
import numpy as np

def ela_analysis(image_path, quality=90):
    """ELA 误差分析"""
    original = Image.open(image_path).convert("RGB")
    temp = "forensics_temp.jpg"
    original.save(temp, "JPEG", quality=quality)
    recompressed = Image.open(temp).convert("RGB")
    diff = np.abs(np.array(original, dtype=np.int16) - np.array(recompressed, dtype=np.int16))
    return diff.mean(axis=2)

def noise_analysis(image_path, block_size=8):
    """噪声分析:估计局部噪声方差,篡改区域方差异常"""
    img = Image.open(image_path).convert("L")
    arr = np.array(img, dtype=np.float32)
    h, w = arr.shape
    noise_map = np.zeros((h // block_size, w // block_size))
    for i in range(0, h - block_size, block_size):
        for j in range(0, w - block_size, block_size):
            block = arr[i:i+block_size, j:j+block_size]
            noise_map[i//block_size, j//block_size] = block.std()
    return noise_map

def metadata_check(image_path):
    """元数据检查"""
    img = Image.open(image_path)
    exif = img._getexif() if hasattr(img, "_getexif") else None
    findings = []
    if exif:
        for tag_id, value in exif.items():
            tag = ExifTags.TAGS.get(tag_id, tag_id)
            if tag in ("Software", "HostComputer", "ProcessingSoftware"):
                findings.append(f"⚠️ 编辑软件痕迹: {tag}={value}")
            if tag == "DateTime" and "20:20:20" in str(value):
                findings.append(f"⚠️ 时间戳疑似异常: {value}")
    if not findings:
        findings.append("元数据未发现明显异常")
    return findings

def forensics_report(image_path):
    print(f"=== 图片取证报告: {image_path} ===\n")

    # ELA
    ela = ela_analysis(image_path)
    ela_anomaly = ela.mean() + 3 * ela.std()
    ela_ratio = (ela > ela_anomaly).sum() / ela.size
    print(f"[ELA] 异常区域占比: {ela_ratio:.4f}")

    # 噪声
    noise = noise_analysis(image_path)
    noise_anomaly = noise.mean() + 3 * noise.std()
    noise_ratio = (noise > noise_anomaly).sum() / noise.size
    print(f"[噪声] 异常区域占比: {noise_ratio:.4f}")

    # 元数据
    meta = metadata_check(image_path)
    print("[元数据]")
    for m in meta:
        print(f"  {m}")

    if ela_ratio > 0.01 or noise_ratio > 0.05:
        print("\n⚠️ 疑似 manipulation,建议人工核查")
    else:
        print("\n未发现明显异常(仅供参考)")

forensics_report("figure.png")
```

## 输出格式
- 取证报告:ELA 异常区域、噪声异常区域、元数据发现。
- 异常区域标注图。

## 约束
- 标注"疑似,建议人工核查",不单独判定造假。
- 多维度综合判断,不凭单一指标下定论。
- 元数据缺失不等于无异常(可能被清除)。
