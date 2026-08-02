# juliabaarck.github.io

Personal academic website, served by GitHub Pages at <https://juliabaarck.github.io/>.

Plain HTML and one CSS file — no Jekyll, no build step, no JavaScript, no external fonts.
Push to `main` and the change is live in a minute or two.

## Previewing changes

Just double-click `index.html` — it opens in your browser and every link works offline.

If you'd rather serve it properly (closer to how GitHub Pages behaves):

```
python -m http.server 8000
```

then open <http://localhost:8000>.

## Editing the text

| What | Where |
|---|---|
| Home page (bio, contact, interests, job-market line) | `index.html` |
| Papers, abstracts, links | `research.html` |
| CV page | `cv.html` |
| Colours, fonts, spacing | `assets/css/style.css` |

The header and footer are repeated in each of the three HTML files. If you change the
navigation, change it in all three.

### Adding your references

`index.html` has a **References** block near the bottom, commented out. Fill in the names and
delete the two comment lines around it (`<!-- ... -->`).

### Adding a page (e.g. Teaching)

Copy `cv.html`, replace the `<main>` content, and add one line to the `<nav>` in each of the
four files.

## Updating the CV

1. Drop the new PDF in as `files/Baarck_CV.pdf` (keep the filename — people link to it).
2. Run `python tools/build_assets.py` to regenerate the page images shown on `cv.html`.
3. Update the "Last updated" date in `cv.html`.

## Adding or replacing a research figure

Figures on `research.html` are generated from sources in `Papers/`.

To **replace a placeholder**: put your figure in `assets/research/`, then point the entry's
`<img src="...">` at it in `research.html` (each placeholder has a comment above it saying so).

To **regenerate everything** after changing a source in `Papers/`:

```
python tools/build_assets.py
```

`tools/build_assets.py` resizes, trims whitespace and compresses each image so pages stay
fast. It needs Pillow (`pip install pillow`); the PDF sources also need `pdftoppm` on your
PATH, which you already have via MiKTeX.

### Where each figure comes from

| Entry on the research page | Source |
|---|---|
| Rising Inequality, Declining Mobility | `Papers/Baarck_Bode_Peichl_RRS_over_time_baseline.pdf` |
| Fairness Views and Policy Preferences | the four `Papers/Baarck_Dolls_Windsteiger/t2_policy_*.png`, composited into a 2×2 grid |
| Secondary-Track Choices | `Papers/Baarck_Paffenholz_trend_gym_abi_late.png` |
| Learning Income Levels (Applied Geography) | Fig. 2 of the open-access article |
| Loneliness in Europe (Health Policy) | Fig. 2 of the open-access article |
| Job market paper, remaining work in progress | `assets/research/figure-placeholder.svg` |

## Layout

```
index.html  research.html  cv.html   pages
assets/css/style.css                 the only stylesheet
assets/img/                          headshot + favicon
assets/research/                     web-sized figures (generated)
assets/cv/                           CV page images (generated)
files/Baarck_CV.pdf                  the CV people download
Papers/                              original figure exports (sources)
tools/build_assets.py                regenerates everything under assets/
```
