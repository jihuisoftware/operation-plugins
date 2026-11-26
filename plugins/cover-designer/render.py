"""Render a single cover from a validated background. All layout coordinates are pixels."""
from PIL import Image, ImageDraw, ImageFont, ImageOps


def text_block(draw, text, path, face, maximum, box_height):
    for size in range(maximum, 15, -2):
        font = ImageFont.truetype(str(path), size, index=face)
        lines = ['']
        for char in text:
            if char == '\n':
                lines.append('')
            elif lines[-1] and draw.textlength(lines[-1] + char, font=font) > 940:
                lines.append(char)
            else:
                lines[-1] += char
        value = '\n'.join(lines)
        bounds = draw.multiline_textbbox((0, 0), value, font=font, spacing=8)
        if bounds[2] - bounds[0] <= 944 and bounds[3] - bounds[1] <= box_height:
            return value, font
    raise ValueError('封面文字过长，请缩短后重新排版')


def compose(folder, spec):
    with Image.open(folder / 'input') as picture:
        image = ImageOps.fit(ImageOps.exif_transpose(picture).convert('RGB'), (1080, 1440),
                             centering=(spec['x'], spec['y']))
    path = spec['font_path']
    panel = Image.new('RGBA', image.size)
    draw = ImageDraw.Draw(panel)
    offset = -920 if spec.get('panel') == 'top' else 0
    draw.rectangle((0, 920 + offset, 1080, 1440 + offset), fill=(12, 18, 26, 200))
    for text, top, size, height in ((spec['title'], 972, 86, 248), (spec['subtitle'], 1272, 46, 112)):
        if text:
            value, font = text_block(draw, text, path, spec['font_face'], size, height)
            draw.multiline_text((64, top + offset), value, font=font, fill='white', spacing=8)
    image.paste(panel, mask=panel.getchannel('A'))
    image.save(folder / 'cover.jpg', quality=92)
