from flask import session
from PIL import Image, ImageDraw, ImageFont
import random
import io

class CaptchaService:
    def __init__(self, width=120, height=30, characters='ABCDEFGHJKLMNPQRSTUVWXYZ23456789', text_length=5):
        self.width = width
        self.height = height
        self.characters = characters
        self.text_length = text_length

    def generate_captcha_text(self):
        """生成一个随机的验证码文本"""
        return ''.join(random.choice(self.characters) for _ in range(self.text_length))

    def generate_captcha_image(self, captcha_text):
        """生成图形验证码"""
        # 创建一个图像对象，白色背景
        img = Image.new('RGB', (self.width, self.height), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)

        # 在图像上写入验证码文本
        font = ImageFont.load_default()
        draw.text((10, 5), captcha_text, fill=(0, 0, 0), font=font)

        # 保存图像到一个字节流中，而不是文件系统
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        return img_byte_arr

    def get_captcha(self):
        """生成图形验证码并保存验证码文本到 session"""
        captcha_text = self.generate_captcha_text()
        session['captcha'] = captcha_text
        print("[Debug from Captcha] Captcha is now: ", session.get('captcha', ''))
        return self.generate_captcha_image(captcha_text)
