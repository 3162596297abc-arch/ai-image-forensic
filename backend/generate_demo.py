"""Generate a more realistic demo portrait."""
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
import random
import io

w, h = 600, 750
img = Image.new("RGB", (w, h), (20, 22, 30))
draw = ImageDraw.Draw(img)
rng = random.Random(42)

# Background with subtle gradient and texture
for y in range(h):
    r = 20 + int(y / h * 15)
    g = 22 + int(y / h * 12)
    b = 30 + int(y / h * 25)
    draw.line([(0, y), (w, y)], fill=(r, g, b))

# Add background noise/texture
for _ in range(w * h // 8):
    x = rng.randint(0, w - 1)
    y = rng.randint(0, h - 1)
    c = rng.randint(-5, 5)
    pixel = img.getpixel((x, y))
    img.putpixel((x, y), tuple(max(0, min(255, p + c)) for p in pixel))

# Main face
cx, cy = w // 2, h // 2 - 30
rx, ry = 140, 170

# Skin base
for y_offset in range(-ry, ry + 1):
    for x_offset in range(-rx, rx + 1):
        if (x_offset / rx) ** 2 + (y_offset / ry) ** 2 <= 1:
            x, y_px = cx + x_offset, cy + y_offset
            if 0 <= x < w and 0 <= y_px < h:
                shade = 0.92 + 0.08 * (1 - ((x_offset / rx) ** 2 + (y_offset / ry) ** 2) ** 0.5)
                r = int(225 * shade)
                g = int(190 * shade)
                b = int(160 * shade)
                # Add subtle skin texture
                r += rng.randint(-3, 3)
                g += rng.randint(-3, 3)
                b += rng.randint(-3, 3)
                img.putpixel((x, y_px), (
                    max(0, min(255, r)),
                    max(0, min(255, g)),
                    max(0, min(255, b)),
                ))

# Eyes
for side in [-1, 1]:
    ex = cx + side * 45
    ey = cy - 25
    # Eye white
    for dx in range(-22, 23):
        for dy in range(-10, 11):
            if (dx / 22) ** 2 + (dy / 10) ** 2 <= 1:
                img.putpixel((ex + dx, ey + dy), (248, 248, 248))
    # Iris
    for dx in range(-10, 11):
        for dy in range(-10, 11):
            if dx*dx + dy*dy <= 100:
                img.putpixel((ex + dx, ey + dy), (70, 110, 160))
    # Pupil
    for dx in range(-5, 6):
        for dy in range(-5, 6):
            if dx*dx + dy*dy <= 25:
                img.putpixel((ex + dx, ey + dy), (15, 15, 20))
    # Highlight
    for dx in range(-3, 4):
        for dy in range(-3, 4):
            if dx*dx + dy*dy <= 9:
                img.putpixel((ex + dx - 4, ey + dy - 3), (255, 255, 255))

# Eyebrows
for side in [-1, 1]:
    bx = cx + side * 40
    by = cy - 50
    for i in range(60):
        t = i / 59
        x = bx + int((t - 0.5) * 80)
        y = by + int(-5 * ((t - 0.5) ** 2) * 15 - t * 8)
        for j in range(3):
            draw.point((x + rng.randint(-1, 1), y + rng.randint(-1, 1)), fill=(55, 38, 28))

# Nose
for i in range(30):
    t = i / 29
    ny = cy + int(t * 38)
    nx = cx + int(-15 * ((t - 0.5) ** 2 - 0.25) * 4)
    for j in range(max(2, 10 - int(t * 8))):
        draw.point((nx + rng.randint(-1, 1), ny + rng.randint(0, 1)), fill=(200, 165, 135))

# Mouth
mouth_y = cy + 60
for dx in range(-30, 31):
    dy = int(8 * ((dx / 30) ** 2) - 2)
    for j in range(5):
        draw.point((cx + dx + rng.randint(-1, 1), mouth_y + dy + rng.randint(-1, 1)), fill=(190, 115, 105))

# Hair
for _ in range(4000):
    x = rng.randint(cx - 170, cx + 170)
    y = rng.randint(30, cy - 50)
    dist = ((x - cx) / 155) ** 2 + ((y - cy + 100) / 160) ** 2
    is_in_face = ((x - cx) / 120) ** 2 + ((y - cy) / 150) ** 2 <= 1
    if dist < 1.3 and not is_in_face:
        shade = rng.randint(35, 70)
        img.putpixel((x, y), (shade, shade - 10, shade - 15))

# Shoulders
for y in range(cy + 150, h):
    for x in range(cx - 160, cx + 160):
        t = (x - cx) / 150
        if abs(t) < 1:
            edge = 0.85 + 0.15 * (1 - abs(t))
            if y < cy + 150 + int(160 * edge):
                img.putpixel((x, y), (55, 50, 65))

# Final processing
img = img.filter(ImageFilter.GaussianBlur(radius=2))
enhancer = ImageEnhance.Contrast(img)
img = enhancer.enhance(1.1)

path = "demo_portrait.png"
img.save(path, quality=95)
print(f"Demo portrait saved: {path} ({w}x{h})")
