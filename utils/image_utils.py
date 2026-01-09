# from PIL import Image, ImageDraw, ImageFont
# import io
#
#
# def generate_text_image(text):
#     # 1. 初始化图片和绘图对象
#     img = Image.new('RGB', (300, 100), color='white')
#     draw = ImageDraw.Draw(img)
#
#     # 2. 加载字体（可选，指定字体大小，无自定义字体则用默认）
#     try:
#         font = ImageFont.truetype("simhei.ttf", 36)  # 本地字体文件，需对应路径
#     except:
#         font = ImageFont.load_default(size=36)
#
#     # 3. 替代 textsize()：用 textbbox() 获取边界框并计算宽高
#     # xy=(0,0) 为文本绘制的起始参考点，不影响尺寸计算
#     bbox = draw.textbbox((0, 0), text=text, font=font)
#     text_width = bbox[2] - bbox[0]  # 右边界 - 左边界 = 文本宽度
#     text_height = bbox[3] - bbox[1]  # 下边界 - 上边界 = 文本高度
#     text_size = (text_width, text_height)  # 与 textsize() 返回格式一致
#
#     # 4. （可选）绘制文本到图片（居中显示，验证尺寸有效性）
#     img_center_x = (300 - text_width) // 2
#     img_center_y = (100 - text_height) // 2
#     draw.text((img_center_x, img_center_y), text=text, font=font, fill='black')
#
#     # 5. 转为字节流（项目中可用于接口返回，如验证码）
#     img_byte_stream = io.BytesIO()
#     img.save(img_byte_stream, format='PNG')
#     img_byte_stream.seek(0)
#
#     print(f"文本尺寸：{text_size}")
#     return img_byte_stream
#
#
# # 调用测试
# if __name__ == "__main__":
#     generate_text_image("测试文本尺寸计算")
