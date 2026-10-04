"""
CEMSI - Procesamiento de expedientes del especialista.

- Elimina la marca "Made with PrimeScanner" (recorte del pie o relleno con color de papel).
- Oculta la CURP en la constancia SEP (dato personal sensible).
- Regenera PDFs limpios en assets/docs/ y miniaturas .webp en assets/images/diplomas/.
- Extrae la fotografía del especialista desde el título UPC.

Uso:  python3 scripts/process_docs.py <carpeta_con_pdfs_originales>
Requiere: pip install PyMuPDF Pillow
"""
import io
import os
import shutil
import sys

import pymupdf
from PIL import Image, ImageEnhance, ImageStat

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, "assets", "docs")
DIPL = os.path.join(ROOT, "assets", "images", "diplomas")
IMGS = os.path.join(ROOT, "assets", "images")

SRC = sys.argv[1] if len(sys.argv) > 1 else "."
EXPEDIENTE = os.path.join(SRC, "media_1791079345933.pdf")
PDTR_FOUND = os.path.join(SRC, "media_1791079345831.pdf")
PDTR_ADV = os.path.join(SRC, "media_1791079346011.pdf")

ZOOM = 2.2


def render(doc, n):
    pix = doc[n].get_pixmap(matrix=pymupdf.Matrix(ZOOM, ZOOM))
    return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)


def crop_bottom(img, frac):
    w, h = img.size
    return img.crop((0, 0, w, int(h * frac)))


def paper_color(img, box):
    """Mediana del color del papel en una franja de referencia."""
    return tuple(int(v) for v in ImageStat.Stat(img.crop(box)).median)


def fill_region(img, x0f, y0f, x1f=1.0, y1f=1.0, ref_above=0.025):
    w, h = img.size
    x0, y0, x1, y1 = int(w * x0f), int(h * y0f), int(w * x1f), int(h * y1f)
    ref = (x0, max(0, y0 - int(h * ref_above)), x1, y0 - 2)
    color = paper_color(img, ref)
    img.paste(color, (x0, y0, x1, y1))
    return img


def mirror_patch(img, x0f, y0f):
    """Cubre la esquina inferior derecha con el reflejo de la inferior izquierda
    (útil cuando el diseño del diploma es simétrico y hay patrón de fondo)."""
    w, h = img.size
    x0, y0 = int(w * x0f), int(h * y0f)
    src = img.crop((0, y0, w - x0, h)).transpose(Image.FLIP_LEFT_RIGHT)
    img.paste(src, (x0, y0))
    return img


def save_pdf(images, name):
    out = pymupdf.open()
    for im in images:
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=80, optimize=True, progressive=True)
        w, h = im.size
        page = out.new_page(width=w / ZOOM, height=h / ZOOM)
        page.insert_image(page.rect, stream=buf.getvalue())
    out.set_metadata({"title": name, "author": "CEMSI", "producer": "CEMSI"})
    out.save(os.path.join(DOCS, name), garbage=4, deflate=True)


def save_thumb(img, name, width=720):
    im = img.copy()
    im.thumbnail((width, width * 2))
    im.save(os.path.join(DIPL, name), "WEBP", quality=82, method=6)
    full = img.copy()
    full.thumbnail((1500, 3000))
    os.makedirs(os.path.join(DIPL, "full"), exist_ok=True)
    full.save(os.path.join(DIPL, "full", name), "WEBP", quality=80, method=6)


def main():
    os.makedirs(DOCS, exist_ok=True)
    os.makedirs(DIPL, exist_ok=True)

    # Limpia salidas previas (incluye el Intermediate duplicado erróneamente: no existe original).
    for d in (DOCS, DIPL):
        for f in os.listdir(d):
            p = os.path.join(d, f)
            shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)

    exp = pymupdf.open(EXPEDIENTE)

    unam = crop_bottom(render(exp, 0), 0.930)
    quiro = fill_region(render(exp, 1), 0.640, 0.930)
    uaeh = crop_bottom(render(exp, 2), 0.916)
    upc = crop_bottom(render(exp, 3), 0.918)
    sep = fill_region(render(exp, 4), 0.640, 0.917)
    sep = fill_region(sep, 0.675, 0.096, 0.965, 0.128, ref_above=0.008)  # CURP oculta
    neuro = mirror_patch(render(exp, 5), 0.645, 0.862)

    found = render(pymupdf.open(PDTR_FOUND), 0)
    adv = render(pymupdf.open(PDTR_ADV), 0)

    save_pdf([unam], "diplomado-neurofacilitacion-unam.pdf")
    save_pdf([quiro], "diplomado-quirofisico-morelos.pdf")
    save_pdf([uaeh], "titulo-medico-cirujano-uaeh.pdf")
    save_pdf([upc, sep], "titulo-terapia-fisica-upc.pdf")
    save_pdf([neuro], "certificacion-neurodinamia-fyosolis.pdf")
    save_pdf([found], "pdtr-foundational-2026.pdf")
    save_pdf([adv], "pdtr-advanced-2026.pdf")

    save_thumb(uaeh, "miniatura-uaeh.webp")
    save_thumb(upc, "miniatura-upc.webp")
    save_thumb(unam, "miniatura-unam.webp")
    save_thumb(quiro, "miniatura-quirofisico.webp")
    save_thumb(neuro, "miniatura-neurodinamia.webp")
    save_thumb(found, "miniatura-pdtr.webp")
    save_thumb(adv, "miniatura-pdtr-advanced.webp")

    # Fotografía del especialista (óvalo del título UPC, la toma más nítida).
    w, h = upc.size
    face = upc.crop((int(w * 0.085), int(h * 0.285), int(w * 0.278), int(h * 0.540)))
    face = ImageEnhance.Contrast(face).enhance(1.08)
    face = ImageEnhance.Sharpness(face).enhance(1.3)
    face.save(os.path.join(IMGS, "doctor-alejandro-gutierrez.webp"), "WEBP", quality=90, method=6)

    raw = os.path.join(IMGS, "doctor-alejandro-gutierrez-raw.webp")
    if os.path.exists(raw):
        os.remove(raw)

    # Previews de control (no se publican).
    prev = os.path.join(ROOT, ".preview")
    os.makedirs(prev, exist_ok=True)
    for n, im in {"quiro": quiro, "sep": sep, "neuro": neuro, "unam": unam}.items():
        p = im.copy()
        p.thumbnail((800, 1200))
        p.save(os.path.join(prev, f"{n}.png"))
    print("OK")


if __name__ == "__main__":
    main()
