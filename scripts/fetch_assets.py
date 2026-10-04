"""
CEMSI - Descarga de recursos estáticos (se sirven desde el propio dominio, sin CDNs en runtime).

- Fuente Plus Jakarta Sans (woff2 variable, subset latin) -> assets/fonts/
- Banderas MX / US (PNG 2x)                                 -> assets/images/flags/
- Íconos Lucide + WhatsApp (Simple Icons) en un sprite SVG   -> src/partials/icons.svg
- Sellos institucionales recortados de los diplomas          -> assets/images/sellos/

Uso: python3 scripts/fetch_assets.py <carpeta_con_pdfs_originales>
"""
import os
import re
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = {"User-Agent": "Mozilla/5.0 (CEMSI build)"}

LUCIDE = [
    "menu", "x", "arrow-right", "arrow-up-right", "calendar-check", "calendar", "phone", "mail",
    "map-pin", "clock", "stethoscope", "activity", "brain", "hand-heart", "bone", "graduation-cap",
    "award", "file-text", "external-link", "download", "check", "shield-check", "message-circle",
    "user", "navigation", "map", "satellite", "book-open", "chevron-right", "circle-alert", "house",
    "waypoints", "info", "hourglass", "globe",
]


def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def save(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)


def fonts():
    base = "https://cdn.jsdelivr.net/fontsource/fonts/plus-jakarta-sans:vf@latest/"
    save(f"{ROOT}/assets/fonts/plus-jakarta-sans-latin-wght.woff2", get(base + "latin-wght-normal.woff2"))
    save(f"{ROOT}/assets/fonts/plus-jakarta-sans-latin-ext-wght.woff2", get(base + "latin-ext-wght-normal.woff2"))
    # TTF solo para generar imágenes (OG) con Pillow; no se publica.
    ttf = "https://github.com/google/fonts/raw/main/ofl/plusjakartasans/PlusJakartaSans%5Bwght%5D.ttf"
    save(f"{ROOT}/scripts/.cache/PlusJakartaSans.ttf", get(ttf))


def flags():
    for code in ("mx", "us"):
        save(f"{ROOT}/assets/images/flags/{code}.png", get(f"https://flagcdn.com/w80/{code}.png"))


def icons():
    symbols, missing = [], []
    for name in LUCIDE:
        try:
            svg = get(f"https://unpkg.com/lucide-static@latest/icons/{name}.svg").decode()
        except Exception:
            missing.append(name)
            continue
        inner = re.sub(r"^[\s\S]*?<svg[^>]*>|</svg>\s*$", "", svg.strip())
        inner = re.sub(r"<!--[\s\S]*?-->", "", inner)
        inner = re.sub(r"\s+", " ", inner).strip()
        symbols.append(f'<symbol id="i-{name}" viewBox="0 0 24 24">{inner}</symbol>')
    wa = get("https://unpkg.com/simple-icons@latest/icons/whatsapp.svg").decode()
    path = re.search(r'<path d="([^"]+)"', wa).group(1)
    symbols.append(f'<symbol id="i-whatsapp" viewBox="0 0 24 24"><path class="fill" d="{path}"/></symbol>')
    sprite = (
        '<svg xmlns="http://www.w3.org/2000/svg" aria-hidden="true" focusable="false" '
        'style="position:absolute;width:0;height:0;overflow:hidden">' + "".join(symbols) + "</svg>"
    )
    save(f"{ROOT}/src/partials/icons.svg", sprite.encode())
    if missing:
        print("Íconos no encontrados:", missing)


def seals(src):
    import pymupdf
    from PIL import Image, ImageOps

    out = f"{ROOT}/assets/images/sellos"
    os.makedirs(out, exist_ok=True)
    for f in os.listdir(out):
        os.remove(os.path.join(out, f))
    exp = pymupdf.open(os.path.join(src, "media_1791079345933.pdf"))
    found = pymupdf.open(os.path.join(src, "media_1791079345831.pdf"))
    jobs = {
        "uaeh": (exp, 2, (0.350, 0.028, 0.510, 0.186)),
        "upc": (exp, 3, (0.032, 0.020, 0.206, 0.196)),
        "eies": (exp, 1, (0.375, 0.015, 0.632, 0.210)),
        "fyosolis": (exp, 5, (0.046, 0.072, 0.230, 0.178)),
        "pdtr": (found, 0, (0.432, 0.192, 0.590, 0.410)),
    }
    for name, (doc, n, box) in jobs.items():
        pix = doc[n].get_pixmap(matrix=pymupdf.Matrix(3, 3))
        im = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        w, h = im.size
        im = im.crop((int(w * box[0]), int(h * box[1]), int(w * box[2]), int(h * box[3])))
        g = ImageOps.grayscale(im)
        g = ImageOps.autocontrast(g, cutoff=(2, 8))  # papel -> blanco
        g = g.point(lambda v: 255 if v > 196 else int(v * 0.92))
        g.thumbnail((220, 220))
        g.save(f"{out}/{name}.webp", "WEBP", quality=85)


if __name__ == "__main__":
    fonts()
    flags()
    icons()
    if len(sys.argv) > 1:
        seals(sys.argv[1])
    print("OK")
