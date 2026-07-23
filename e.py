from pptx import Presentation

prs = Presentation()

# 第1页
slide = prs.slides.add_slide(prs.slide_layouts[0])
slide.shapes.title.text = "测试PPT"
slide.placeholders[1].text = "这是自动生成的"

# 第2页
slide = prs.slides.add_slide(prs.slide_layouts[1])
slide.shapes.title.text = "功能列表"

text_frame = slide.placeholders[1].text_frame
text_frame.text = "支持："

for item in ["文本", "表格", "图片", "图表"]:
    p = text_frame.add_paragraph()
    p.text = item

prs.save("test.pptx")

print("生成成功")
