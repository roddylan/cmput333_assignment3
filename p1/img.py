from pathlib import Path
from datetime import datetime
from math import sqrt
from PIL import Image, ImageDraw, ImageFont

def add_watermark(path):
    p = Path(path)
    
    try:
        ts = datetime.fromtimestamp(p.stat().st_ctime)
    except FileNotFoundError:
        ts = datetime.now()
        
    # Reverted to a single line
    text = f'{ts.strftime("%Y-%m-%d %H:%M:%S")} | Group 9'

    base = Image.open(path).convert("RGBA")
    width, height = base.size

    watermark_canvas = Image.new('RGBA', (width, height), (255, 255, 255, 0))
    draw = ImageDraw.Draw(watermark_canvas)

    def get_font(size):
        font_options = ["arialbd.ttf", "Arial Bold.ttf", "arial.ttf", "Arial.ttf"]
        for font_name in font_options:
            try:
                return ImageFont.truetype(font_name, size=size)
            except IOError:
                continue
        return ImageFont.load_default()

    font = get_font(100) # Baseline size

    if font != ImageFont.load_default():
        # Changed back to standard textbbox
        bbox = draw.textbbox((0, 0), text, font=font)
        base_text_width = bbox[2] - bbox[0]
        
        # Scale to fill 90% of the image WIDTH
        target_width = width * 0.90
        scale_factor = target_width / base_text_width
        
        final_font_size = int(100 * scale_factor)
        font = get_font(final_font_size)

    # Recalculate exact bounding box for perfect centering
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    
    x = (width - text_w) / 2
    y = (height - text_h) / 2 - (bbox[1] if bbox[1] > 0 else 0)

    # Changed back to standard text drawing
    draw.text((x, y), text, font=font, fill=(0, 0, 0, 20))

    # Paste directly onto the base image
    base.paste(watermark_canvas, (0, 0), watermark_canvas)
    base.save(path, "PNG")
    
    
for i in range(0, 58):
    if i == 0:
        add_watermark('image.png')
    else:
        add_watermark(f'image-{i}.png')
