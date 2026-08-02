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
| Home page (bio, contact, interests) | `index.html` |
| Papers, abstracts, links | `research.html` |
| Supervision and teaching | `teaching.html` |
| CV page | `cv.html` |
| Colours, fonts, spacing | `assets/css/style.css` |

The header and footer are repeated in each of the four HTML files. If you change the
navigation, change it in all four.

### Hiding a paper temporarily

Wrap the whole `<article class="paper">…</article>` in an HTML comment. The secondary-track
paper with Michaela Paffenholz is currently hidden this way in `research.html` — its text and
figure are intact, so removing the two comment lines brings it straight back.

### Adding your references

`index.html` has a **References** block near the bottom, commented out. Fill in the names and
delete the two comment lines around it (`<!-- ... -->`).

### Adding a page

Copy `teaching.html`, replace the `<main>` content and the `<head>` metadata, and add one line
to the `<nav>` in every page.

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
| Service Shapes Careers (JMP) | Fig. 3, auto-cropped from the draft PDF in `Papers/JMP_Baarck/` |
| Rising Inequality, Declining Mobility | `Papers/Baarck_Bode_Peichl_RRS_over_time_baseline.pdf` |
| Fairness Views and Policy Preferences | the four `Papers/Baarck_Dolls_Windsteiger/t2_policy_*.png`, composited into a 2×2 grid |
| Manager Preferences | `Papers/Baarck_Kosse_Peichl_Sunde_Wohlrabe/coefplot_linvest_cont_above10perc.jpg` |
| Secondary-Track Choices | `Papers/Baarck_Paffenholz_trend_gym_abi_late.png` |
| Learning Income Levels (Applied Geography) | Fig. 2 of the open-access article |
| Loneliness in Europe (Health Policy) | Fig. 2 of the open-access article |

Entries with no figure — currently the last two work-in-progress papers — use
`<article class="paper paper--nofigure">`, which drops the second column so the text runs
full width. `assets/research/figure-placeholder.svg` is kept as a stand-in you can point a
new entry at until its figure exists.

## Links

External links all carry `target="_blank" rel="noopener"` so they open in a new tab and leave
this site open behind them. Keep that on any link you add. Working papers link to the CESifo
working paper; published papers link to the journal article plus a free-to-read route (the
author PDF or the PubMed Central version), since the journal links are paywalled.

## The job market paper draft is not published

`.gitignore` excludes `Papers/JMP_Baarck/*.pdf`. The draft is marked *preliminary and
incomplete — please do not circulate*, and anything committed to this repository is publicly
downloadable even when no page links to it. Keep the PDF in that folder locally: the build
script re-crops Figure 3 from it, and commits only the extracted figure
(`service-shapes-careers-fig3.png`). If the draft is restructured, update `JMP_FIGURE_PAGE`
in `tools/build_assets.py`.

## Layout

```
index.html  research.html  teaching.html  cv.html   pages
assets/css/style.css                 the only stylesheet
assets/img/                          headshot + favicon
assets/research/                     web-sized figures (generated)
assets/cv/                           CV page images (generated)
files/Baarck_CV.pdf                  the CV people download
Papers/                              original figure exports (sources)
tools/build_assets.py                regenerates everything under assets/
```
