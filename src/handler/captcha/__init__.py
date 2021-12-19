import base64
import random
import string

from captcha.image import ImageCaptcha


def random_str(length: int = 10) -> str: return ''.join(
    random.choices(string.ascii_letters + string.digits, k=length))


def generate_captcha() -> tuple[str, bytes]:
    """Returns:
        captcha_text: str
        captcha_image: bytes  # b64encode bytes"""
    image = ImageCaptcha(width=280, height=90)
    captcha_text = random_str()
    data = image.generate(captcha_text)
    captcha_image = base64.b64encode(data.getvalue())
    return (captcha_text, captcha_image)
