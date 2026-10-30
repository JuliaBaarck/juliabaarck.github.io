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


def strip_social_frame(im: Image.Image, top: int) -> Image.Image:
    """Cut a social-media graphic down to its plot.

    The LinkedIn exports carry a headline and subtitle above the plot and, below
    a thin grey rule, a notes line and a citation. The website shows the subtitle
    as a caption instead, so keep only what lies between `top` (measured per
    graphic, just below the subtitle) and that rule.
    """
    gray = im.convert("L")
    w, h = gray.size
    px = gray.load()
    content = [any(px[x, y] < TRIM_THRESHOLD for x in range(0, w, 3)) for y in range(h)]
    rule = h
    # The rule is the first content band of at most 3 rows in the bottom third.
    y = h * 2 // 3
    while y < h:
        if content[y]:
            band_end = y
            while band_end < h and content[band_end]:
                band_end += 1
            if band_end - y <= 3:
                rule = y
                break
            y = band_end
        y += 1
    return trim_whitespace(im.crop((0, top, w, rule)))


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
    src = PAPERS / "Baarck_Bode_Peichl" / "RRS_Evolution_LinkedIn.png"
    if not src.exists():
        log("  !! source missing, skipping")
        return
    im = strip_social_frame(flatten(Image.open(src)), top=370)
    save_png(fit_width(im, FIGURE_WIDTH), RESEARCH_OUT / "rising-inequality-mobility.png")


def build_fairness_figure() -> None:
    src = PAPERS / "Baarck_Dolls_Windsteiger" / "linkedin_heterogeneity_policy.png"
    if not src.exists():
        log("  !! source missing, skipping")
        return
    im = strip_social_frame(flatten(Image.open(src)), top=312)
    save_png(fit_width(im, FIGURE_WIDTH), RESEARCH_OUT / "fairness-views-policy.png")


def build_manager_preferences_figure() -> None:
    src = PAPERS / "Baarck_Kosse_Peichl_Sunde_Wohlrabe" / "coefplot_linvest_cont_above10perc.jpg"
    if not src.exists():
        log("  !! source missing, skipping")
        return
    im = fit_width(trim_whitespace(flatten(Image.open(src)), padding=8), FIGURE_WIDTH)
    save_png(im, RESEARCH_OUT / "manager-preferences.png")


def build_secondary_track_figure() -> None:
    src = PAPERS / "Baarck_Paffenholz_trend_gym_abi_late.png"
    if not src.exists():
        log("  !! source missing, skipping")
        return
    im = fit_width(trim_whitespace(flatten(Image.open(src))), FIGURE_WIDTH)
    save_png(im, RESEARCH_OUT / "secondary-track-choices.png")


def build_jmp_figures() -> None:
    """Design figures of the job market paper: treated vs. pooled control cohorts.

    The two panels are shown stacked on the research page, with their labels in
    the HTML, so each is saved on its own.
    """
    panels = {
        "figdesign_treated_sas_se.png": "jmp-treated-cohort.png",
        "figdesign_controls_sas_se.png": "jmp-control-cohorts.png",
    }
    for name, out in panels.items():
        src = PAPERS / "JMP_Baarck" / name
        if not src.exists():
            log(f"  !! panel missing: {name}, skipping")
            continue
        im = fit_width(trim_whitespace(flatten(Image.open(src)), padding=8), FIGURE_WIDTH)
        save_png(im, RESEARCH_OUT / out)


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
    ("figures: job market paper", build_jmp_figures),
    ("figure: rising inequality, declining mobility", build_mobility_figure),
    ("figure: fairness views", build_fairness_figure),
    ("figure: manager preferences", build_manager_preferences_figure),
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

