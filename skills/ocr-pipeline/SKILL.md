# ocr-pipeline — OCR 流水线

## 用途
扫描件、图表、截图的文字识别。基于 PaddleOCR 做多语言 OCR,提取文本并结构化输出(文本块、坐标、置信度),中文场景优先。

## 触发条件
- 需要从扫描件/图片/PDF 提取文字时。
- 图表中的文字需要结构化提取时。
- 用户提到"OCR""文字识别""扫描件"时。

## 工具依赖
```bash
pip install paddlepaddle paddleocr
# GPU 版:pip install paddlepaddle-gpu
```

## 操作步骤
1. 输入图片路径或 PDF(逐页转图片)。
2. 用 PaddleOCR 识别文字(支持中文、英文、多语言)。
3. 提取每个文本块的内容、坐标框、置信度。
4. 按坐标排序,还原文档阅读顺序。
5. 结构化输出(JSON / 文本)。

## 调用示例
```python
from paddleocr import PaddleOCR
import json

# 初始化(中文场景,lang="ch")
ocr = PaddleOCR(use_angle_cls=True, lang="ch", show_log=False)

def ocr_image(image_path):
    """对单张图片做 OCR"""
    result = ocr.ocr(image_path, cls=True)
    blocks = []
    for idx, line in enumerate(result[0]):
        box = line[0]        # 4 个角点坐标
        text = line[1][0]    # 文本
        conf = line[1][1]    # 置信度
        # 计算中心 y 坐标用于排序
        cy = sum(p[1] for p in box) / 4
        cx = sum(p[0] for p in box) / 4
        blocks.append({
            "text": text,
            "confidence": float(conf),
            "bbox": box,
            "center_y": cy,
            "center_x": cx,
        })

    # 按 y 坐标排序(从上到下),同 y 按 x 排序(从左到右)
    blocks.sort(key=lambda b: (round(b["center_y"] / 20), b["center_x"]))
    return blocks

def ocr_to_text(image_path):
    """OCR 并输出纯文本"""
    blocks = ocr_image(image_path)
    lines = [b["text"] for b in blocks if b["confidence"] > 0.5]
    return "\n".join(lines)

# 单张图片
blocks = ocr_image("scan_page.png")
print(json.dumps(blocks[:3], ensure_ascii=False, indent=2))
print("\n--- 提取文本 ---")
print(ocr_to_text("scan_page.png"))

# PDF 逐页处理
def ocr_pdf(pdf_path):
    import fitz  # PyMuPDF
    doc = fitz.open(pdf_path)
    full_text = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        pix = page.get_pixmap(dpi=200)
        img_path = f"temp_page_{page_num}.png"
        pix.save(img_path)
        text = ocr_to_text(img_path)
        full_text.append(f"=== Page {page_num+1} ===\n{text}")
        import os; os.remove(img_path)
    return "\n\n".join(full_text)
```

## 输出格式
- 结构化 JSON:每块含 text、confidence、bbox(4 角点坐标)。
- 纯文本:按阅读顺序排列的文本内容。

## 约束
- 中文场景优先用 PaddleOCR(lang="ch")。
- 低置信度(<0.5)的文本块需标注,建议人工复核。
- PDF 需逐页转图片再 OCR,不可整篇处理。
