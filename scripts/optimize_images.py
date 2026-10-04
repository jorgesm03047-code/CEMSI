"""
CEMSI - Optimización de imágenes ilustrativas + generación de marca (logo PNG, favicon, OG).

Uso: python3 scripts/optimize_images.py <carpeta_con_jpg_generados>
"""
import glob
import os
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "images")
SRC = sys.argv[1] if len(sys.argv) > 1 else "."

PHOTOS = {
    "hero_assessment": "valoracion-neuromuscular",
    "spine_model": "modelo-columna",
    "reflex_test": "evaluacion-refleja",
    "manual_therapy": "terapia-manual",
    "general_medicine": "medicina-integral",
    "ergonomic_desk": "ergonomia-escritorio",
}

NAVY = (30, 78, 140)
BLUE = (62, 120, 178)
GREEN = (30, 158, 107)

# Nodos del isotipo (coordenadas en caja 0..100). Debe coincidir con src/partials/logo-mark.svg
NODES = [(50, 50), (22, 30), (40, 14), (74, 20), (84, 52), (68, 84), (28, 76)]
LINKS = [(0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 1)]


def photos():
    os.makedirs(f"{OUT}/fotos", exist_ok=True)
    for key, name in PHOTOS.items():
        files = glob.glob(os.path.join(SRC, f"{key}_*.jpg"))
        if not files:
            print("Falta:", key)
            continue
        im = Image.open(sorted(files)[-1]).convert("RGB")
        for width in (800, 1400):
            c = im.copy()
            if c.width > width:
                c = c.resize((width, round(c.height * width / c.width)), Image.LANCZOS)
            c.save(f"{OUT}/fotos/{name}-{width}.webp", "WEBP", quality=78, method=6)


def draw_mark(size, bg=None):
    s = size / 100
    im = Image.new("RGBA", (size, size), bg or (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for a, b in LINKS:
        (x1, y1), (x2, y2) = NODES[a], NODES[b]
        d.line([(x1 * s, y1 * s), (x2 * s, y2 * s)], fill=BLUE + (255,), width=max(2, int(3.2 * s)))
    for i, (x, y) in enumerate(NODES):
        r = (9 if i == 0 else 6) * s
        d.ellipse([x * s - r, y * s - r, x * s + r, y * s + r], fill=(GREEN if i == 0 else NAVY) + (255,))
    return im


def brand():
    draw_mark(512).save(f"{OUT}/logo-cemsi.png", optimize=True)
    icon = draw_mark(180, bg=(255, 255, 255, 255))
    icon.save(f"{ROOT}/apple-touch-icon.png", optimize=True)

    ttf = os.path.join(ROOT, "scripts", ".cache", "PlusJakartaSans.ttf")
    og = Image.new("RGB", (1200, 630), (255, 255, 255))
    d = ImageDraw.Draw(og)
    d.rectangle([0, 0, 1200, 10], fill=NAVY)
    og.paste(draw_mark(220), (90, 90), draw_mark(220))

    def font(size, weight):
        f = ImageFont.truetype(ttf, size)
        try:
            f.set_variation_by_axes([weight])
        except Exception:
            pass
        return f

    d.text((340, 120), "CEMSI", font=font(110, 800), fill=NAVY)
    d.text((345, 250), "Centro Médico de Salud Integral", font=font(38, 600), fill=(51, 65, 85))
    d.text((90, 420), "Medicina integral, fisioterapia y", font=font(46, 700), fill=NAVY)
    d.text((90, 480), "reprogramación neurofuncional P-DTR®", font=font(46, 700), fill=NAVY)
    d.text((90, 560), "Dr. Alejandro Gutiérrez Lazcano", font=font(30, 600), fill=(21, 128, 85))
    og.save(f"{OUT}/og-cemsi.jpg", quality=86, optimize=True)


if __name__ == "__main__":
    photos()
    brand()
    print("OK")
