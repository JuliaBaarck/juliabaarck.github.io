#!/usr/bin/env python3
"""Regenerate every derived image on the website.

Sources live in `Papers/` (figure exports), `files/` (the CV PDF) and
`assets/img/julia-baarck-original.png` (the headshot). Nothing here is edited by
hand -- run this script after replacing a source file:

    python tools/build_assets.py

Requires Pillow. PDF sources additionally need `pdftoppm` on PATH (it ships with
MiKTeX and with poppler); if it is missing those steps are skipped with a note
rather than failing the whole build.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
PAPERS = ROOT / "Papers"
RESEARCH_OUT = ROOT / "assets" / "research"
CV_OUT = ROOT / "assets" / "cv"
IMG_OUT = ROOT / "assets" / "img"

# White-ish pixels are treated as background when trimming figure margins.
TRIM_THRESHOLD = 247
# Padding kept around a trimmed figure, in pixels of the source image.
TRIM_PADDING = 12
# Research figures render in a ~360px column, so 900px covers 2x displays.
FIGURE_WIDTH = 900


def log(msg: str) -> None:
    print(msg)


def find_pdftoppm() -> str | None:
    return shutil.which("pdftoppm")


def trim_whitespace(im: Image.Image, padding: int = TRIM_PADDING) -> Image.Image:
    """Crop uniform white margins, keeping a little breathing room."""
    rgb = im.convert("RGB")
    # point() maps every channel value: near-white -> 0, everything else -> 255,
    # so the bounding box of the result is the bounding box of the real content.
    mask = rgb.point(lambda v: 0 if v >= TRIM_THRESHOLD else 255).convert("L")
    box = mask.getbbox()
    if box is None:
        return im
    left, upper, right, lower = box
    left = max(0, left - padding)
    upper = max(0, upper - padding)
    right = min(im.width, right + padding)
    lower = min(im.height, lower + padding)
    return im.crop((left, upper, right, lower))


def flatten(im: Image.Image) -> Image.Image:
    """Composite any transparency onto white so JPEG/PNG output stays clean."""
    if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
        background = Image.new("RGB", im.size, "white")
        background.paste(im.convert("RGBA"), mask=im.convert("RGBA").split()[-1])
        return background
    return im.convert("RGB")


def fit_width(im: Image.Image, max_width: int) -> Image.Image:
    if im.width <= max_width:
        return im
    height = round(im.height * max_width / im.width)
    return im.resize((max_width, height), Image.LANCZOS)


def save_png(im: Image.Image, dest: Path, colors: int = 128) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    # Palette-quantise line art: these figures use very few colours, so this cuts
    # file size by roughly 3-4x with no visible loss.
    quantised = im.quantize(colors=colors, method=Image.MEDIANCUT, dither=Image.NONE)
    quantised.save(dest, format="PNG", optimize=True)
    log(f"  -> {dest.relative_to(ROOT)}  ({dest.stat().st_size // 1024} KB, {im.width}x{im.height})")


def save_jpeg(im: Image.Image, dest: Path, quality: int = 86) -> None:
    """For figures with continuous colour (maps, photos) where PNG bloats."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    im.save(dest, format="JPEG", quality=quality, optimize=True, progressive=True)
    log(f"  -> {dest.relative_to(ROOT)}  ({dest.stat().st_size // 1024} KB, {im.width}x{im.height})")


def pdf_to_image(pdf: Path, dpi: int, page: int = 1) -> Image.Image | None:
    """Rasterise one page of a PDF via pdftoppm."""
    pdftoppm = find_pdftoppm()
    if pdftoppm is None:
        log(f"  !! pdftoppm not found on PATH, skipping {pdf.name}")
        return None
    with tempfile.TemporaryDirectory() as tmp:
        prefix = Path(tmp) / "page"
        subprocess.run(
            [pdftoppm, "-png", "-r", str(dpi), "-f", str(page), "-l", str(page),
             str(pdf), str(prefix)],
            check=True,
            capture_output=True,
        )
        produced = sorted(Path(tmp).glob("page*.png"))
        if not produced:
            log(f"  !! pdftoppm produced no output for {pdf.name} page {page}")
            return None
        return Image.open(produced[0]).copy()


def pdf_page_count(pdf: Path) -> int:
    pdfinfo = shutil.which("pdfinfo")
    if pdfinfo:
        out = subprocess.run([pdfinfo, str(pdf)], capture_output=True, text=True)
        for line in out.stdout.splitlines():
            if line.startswith("Pages:"):
                return int(line.split()[1])
    # Fall back to probing pages one at a time.
    count = 0
    while count < 20:
        try:
            if pdf_to_image(pdf, dpi=10, page=count + 1) is None:
                break
        except subprocess.CalledProcessError:
            break
        count += 1
    return count


# ---------------------------------------------------------------------------
# Individual build steps
# ---------------------------------------------------------------------------


def build_headshot() -> None:
    src = IMG_OUT / "julia-baarck-original.png"
    if not src.exists():
        log("  !! headshot source missing, skipping")
        return
    im = flatten(Image.open(src))
    # The original is slightly wider than tall; crop to a 4:5 portrait centred
    # horizontally, which reads as a headshot rather than a cropped snapshot.
    target_w = round(im.height * 0.8)
    if target_w < im.width:
        left = (im.width - target_w) // 2
        im = im.crop((left, 0, left + target_w, im.height))
    im = fit_width(im, 720)
    dest = IMG_OUT / "julia-baarck.jpg"
    im.save(dest, format="JPEG", quality=86, optimize=True, progressive=True)
    log(f"  -> {dest.relative_to(ROOT)}  ({dest.stat().st_size // 1024} KB, {im.width}x{im.height})")


def build_mobility_figure() -> None:
    src = PAPERS / "Baarck_Bode_Peichl_RRS_over_time_baseline.pdf"
    if not src.exists():
        log("  !! source missing, skipping")
        return
    im = pdf_to_image(src, dpi=200)
    if im is None:
        return
    im = fit_width(trim_whitespace(flatten(im)), FIGURE_WIDTH)
    save_png(im, RESEARCH_OUT / "rising-inequality-mobility.png")


def build_fairness_grid() -> None:
    """Composite the four policy-preference panels into a 2x2 grid."""
    names = [
        "t2_policy_umverteilung.png",       # "We need more redistribution"
        "t2_policy_verr_ungleichheit.png",  # perceived inequality
        "t2_policy_einkommenssteuer.png",   # income tax
        "t2_policy_vermoegenssteuer.png",   # wealth tax
    ]
    panels = []
    for name in names:
        path = PAPERS / "Baarck_Dolls_Windsteiger" / name
        if not path.exists():
            log(f"  !! panel missing: {name}, skipping figure")
            return
        panels.append(fit_width(trim_whitespace(flatten(Image.open(path)), padding=6), 560))

    cell_w = max(p.width for p in panels)
    cell_h = max(p.height for p in panels)
    # The row gap is larger than the column gap: each panel carries its title on
    # top, which would otherwise crowd the x-axis of the panel above it.
    gap_x, gap_y = 24, 56
    canvas = Image.new("RGB", (cell_w * 2 + gap_x, cell_h * 2 + gap_y), "white")
    for index, panel in enumerate(panels):
        col, row = index % 2, index // 2
        # Centre each panel in its cell so differing axis widths still line up.
        x = col * (cell_w + gap_x) + (cell_w - panel.width) // 2
        y = row * (cell_h + gap_y) + (cell_h - panel.height) // 2
        canvas.paste(panel, (x, y))
    save_png(canvas, RESEARCH_OUT / "fairness-views-policy.png")


def build_secondary_track_figure() -> None:
    src = PAPERS / "Baarck_Paffenholz_trend_gym_abi_late.png"
    if not src.exists():
        log("  !! source missing, skipping")
        return
    im = fit_width(trim_whitespace(flatten(Image.open(src))), FIGURE_WIDTH)
    save_png(im, RESEARCH_OUT / "secondary-track-choices.png")


def build_spatial_income_figure() -> None:
    # Fig. 2 of the Applied Geography paper, cropped out of the open-access PDF
    # (paulhufe.net/pdfs/GTSBHWP_2023.pdf) and kept in Papers/ as the source.
    src = PAPERS / "Garbasevschi_etal_gini_median_income_maps.png"
    if not src.exists():
        log("  !! source missing, skipping")
        return
    im = fit_width(trim_whitespace(flatten(Image.open(src)), padding=6), FIGURE_WIDTH)
    # Choropleths are continuous-colour; PNG would be ~3x the size here.
    save_jpeg(im, RESEARCH_OUT / "spatial-income-inequality.jpg")


def build_loneliness_figure() -> None:
    # Fig. 2 of the Health Policy paper, from open-access PMC9479375.
    src = PAPERS / "Baarck_dHombres_Tintori_loneliness_eu_maps.jpg"
    if not src.exists():
        log("  !! source missing, skipping")
        return
    im = fit_width(trim_whitespace(flatten(Image.open(src)), padding=6), FIGURE_WIDTH)
    save_jpeg(im, RESEARCH_OUT / "loneliness-europe.jpg")


def build_cv_pages() -> None:
    src = ROOT / "files" / "Baarck_CV.pdf"
    if not src.exists():
        log("  !! files/Baarck_CV.pdf missing, skipping")
        return
    for old in CV_OUT.glob("cv-page-*.png"):
        old.unlink()
    pages = pdf_page_count(src)
    if not pages:
        log("  !! could not determine CV page count, skipping")
        return
    for page in range(1, pages + 1):
        im = pdf_to_image(src, dpi=150, page=page)
        if im is None:
            return
        im = fit_width(flatten(im), 1240)
        # A CV page is black text plus blue links on white -- 32 palette entries
        # keep the anti-aliasing smooth while roughly halving the file size.
        save_png(im, CV_OUT / f"cv-page-{page}.png", colors=32)


STEPS = [
    ("headshot", build_headshot),
    ("figure: rising inequality, declining mobility", build_mobility_figure),
    ("figure: fairness views (2x2 composite)", build_fairness_grid),
    ("figure: secondary-track choices", build_secondary_track_figure),
    ("figure: spatial income inequality", build_spatial_income_figure),
    ("figure: loneliness in Europe", build_loneliness_figure),
    ("CV page images", build_cv_pages),
]


def main() -> int:
    if find_pdftoppm() is None:
        log("note: pdftoppm not on PATH -- PDF-derived images will be skipped.\n")
    for label, step in STEPS:
        log(f"{label}:")
        try:
            step()
        except Exception as exc:  # keep going; one bad source shouldn't block the rest
            log(f"  !! failed: {exc}")
    log("\ndone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

