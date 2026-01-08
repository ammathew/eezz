import io

from PIL import Image, ImageDraw, ImageFont


def _load_font(size):
    try:
        return ImageFont.truetype("DejaVuSans-Bold.ttf", size)
    except Exception:
        return ImageFont.load_default()


def _wrap_text(draw, text, font, max_width):
    words = text.split()
    if not words:
        return [text]

    lines = []
    current_line = words[0]
    for word in words[1:]:
        test_line = f"{current_line} {word}"
        line_width = draw.textlength(test_line, font=font)
        if line_width <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word
    lines.append(current_line)
    return lines


def render_ad_image(text, size=1080, padding=140):
    cleaned_text = (text or "").strip()
    if not cleaned_text:
        cleaned_text = "YOUR MESSAGE"

    image = Image.new("RGB", (size, size), color=(0, 0, 0))
    draw = ImageDraw.Draw(image)
    max_width = size - (padding * 2)
    max_height = size - (padding * 2)

    font_size = 140
    while font_size >= 36:
        font = _load_font(font_size)
        lines = _wrap_text(draw, cleaned_text, font, max_width)
        line_height = font.getbbox("Ay")[3]
        total_height = (line_height * len(lines)) + (line_height * 0.35 * (len(lines) - 1))
        widest_line = max(draw.textlength(line, font=font) for line in lines)

        if total_height <= max_height and widest_line <= max_width:
            break
        font_size -= 6

    if font_size < 36:
        font = _load_font(36)
        lines = _wrap_text(draw, cleaned_text, font, max_width)
        line_height = font.getbbox("Ay")[3]
        total_height = (line_height * len(lines)) + (line_height * 0.35 * (len(lines) - 1))
    else:
        line_height = font.getbbox("Ay")[3]
        total_height = (line_height * len(lines)) + (line_height * 0.35 * (len(lines) - 1))

    current_y = (size - total_height) / 2
    for line in lines:
        line_width = draw.textlength(line, font=font)
        x = (size - line_width) / 2
        draw.text((x, current_y), line, fill=(255, 255, 255), font=font)
        current_y += line_height * 1.35

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()
