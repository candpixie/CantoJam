"""Draw the tone-height figure: the 0243 ladder against what the corpus says.

Writes docs/tone-levels.svg. Pure standard library, so building the figure
does not add a dependency to a package that advertises having none.

    python3 scripts/figure_tone_levels.py
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
MODEL = json.loads((ROOT / "cantojam" / "data" / "model.json").read_text())

# The four-level ladder lyricists use. Rungs are evenly spaced by construction:
# it encodes order and grouping, not a metric distance.
LADDER_0243 = {"4": 0, "5": 1, "6": 1, "3": 2, "1": 3, "2": 3}

NAMES = {"1": "陰平", "2": "陰上", "3": "陰去", "4": "陽平", "5": "陽上", "6": "陽去"}

# Tones whose measured height contradicts the ladder.
CONTRADICTS = {"4": "2", "5": "1"}

W, H = 720, 492
L, R = 150, 452          # ladder column, measured column
AXIS = 630               # semitone axis
TOP, BOT = 128, 348
ACCENT = "#c0567e"
GREY = "#9a9a9a"
INK = "#1a1a1a"
MUTE = "#6b6b6b"
FAINT = "#dcdcdc"
FONT = "Lato, -apple-system, 'Helvetica Neue', Arial, sans-serif"

levels = {t: float(v) for t, v in MODEL["tone_levels"].items()}
hi = max(levels.values()) + 0.6
lo = min(levels.values()) - 0.6


def y_measured(v):
    return BOT - (v - lo) / (hi - lo) * (BOT - TOP)


def y_rung(rung):
    return BOT - rung / 3 * (BOT - TOP)


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


o = []
add = o.append
add(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
    f'viewBox="0 0 {W} {H}" font-family="{FONT}">')
add(f'<rect width="{W}" height="{H}" fill="#ffffff"/>')

# ---- title block ----
add(f'<text x="32" y="36" font-size="16" font-weight="700" fill="{INK}">'
    f'The 0243 ladder against measured tone height</text>')
add(f'<text x="32" y="58" font-size="12" fill="{MUTE}">'
    f'{MODEL["songs"]} Cantopop songs, {MODEL["syllables"]:,} sung syllables. '
    f'Height is median semitones relative to each song&#8217;s median pitch.</text>')

# ---- column headers ----
for x, label, sub, col in (
    (L, "0243 ladder", "predicted", MUTE),
    (R, "measured", "this corpus", INK),
):
    add(f'<text x="{x}" y="{TOP - 34}" font-size="12.5" font-weight="700" '
        f'fill="{col}" text-anchor="middle">{label}</text>')
    add(f'<text x="{x}" y="{TOP - 19}" font-size="10.5" fill="{MUTE}" '
        f'text-anchor="middle">{sub}</text>')

# ---- semitone axis ----
add(f'<line x1="{AXIS}" y1="{TOP - 8}" x2="{AXIS}" y2="{BOT + 8}" '
    f'stroke="#e6e6e6" stroke-width="1"/>')
for tick in range(-5, 4):
    ty = y_measured(tick)
    if TOP - 10 <= ty <= BOT + 10:
        add(f'<line x1="{AXIS - 4}" y1="{ty:.1f}" x2="{AXIS}" y2="{ty:.1f}" '
            f'stroke="#cccccc" stroke-width="1"/>')
        add(f'<text x="{AXIS + 7}" y="{ty + 4:.1f}" font-size="10.5" '
            f'fill="{MUTE}">{tick:+d}</text>')
add(f'<text x="{AXIS + 2}" y="{TOP - 19}" font-size="10.5" fill="{MUTE}">semitones</text>')

# ---- ladder rungs: short ticks right of the labels, never through them ----
for rung in range(4):
    ry = y_rung(rung)
    add(f'<line x1="{L + 16}" y1="{ry:.1f}" x2="{L + 54}" y2="{ry:.1f}" '
        f'stroke="{FAINT}" stroke-width="1"/>')

# ---- connectors ----
for tone in sorted(levels):
    hit = tone in CONTRADICTS
    y0, y1 = y_rung(LADDER_0243[tone]), y_measured(levels[tone])
    add(f'<path d="M {L + 58} {y0:.1f} C {L + 170} {y0:.1f}, '
        f'{R - 180} {y1:.1f}, {R - 34} {y1:.1f}" fill="none" '
        f'stroke="{ACCENT if hit else "#e0e0e0"}" '
        f'stroke-width="{2.0 if hit else 1.2}"/>')

# ---- ladder-side labels (two tones share a rung twice) ----
by_rung = {}
for tone in sorted(levels):
    by_rung.setdefault(LADDER_0243[tone], []).append(tone)
for rung, tones in by_rung.items():
    ry = y_rung(rung)
    span = 16 * (len(tones) - 1)
    ys = [ry - span / 2 + i * 16 for i in range(len(tones))]
    if len(tones) > 1:
        # bracket showing the ladder puts these tones on one rung
        add(f'<line x1="{L + 34}" y1="{ys[0]:.1f}" x2="{L + 34}" y2="{ys[-1]:.1f}" '
            f'stroke="{FAINT}" stroke-width="1"/>')
    for ty, tone in zip(ys, sorted(tones)):
        hit = tone in CONTRADICTS
        col = ACCENT if hit else GREY
        add(f'<circle cx="{L + 34}" cy="{ty:.1f}" r="3.4" fill="{col}"/>')
        add(f'<text x="{L + 22}" y="{ty + 4:.1f}" font-size="11.5" fill="{col}" '
            f'text-anchor="end" font-weight="{700 if hit else 400}">tone {tone}</text>')

# ---- measured dots, with label declutter ----
order = sorted(levels, key=lambda t: -levels[t])
label_y = {}
prev = None
for tone in order:
    ty = y_measured(levels[tone])
    if prev is not None and ty - prev < 15:
        ty = prev + 15
    label_y[tone] = ty
    prev = ty

for tone in order:
    v = levels[tone]
    dy = y_measured(v)
    ly = label_y[tone]
    hit = tone in CONTRADICTS
    col = ACCENT if hit else GREY
    # leader line when the label had to move off its dot
    if abs(ly - dy) > 1.5:
        add(f'<path d="M {R - 22} {dy:.1f} L {R - 14} {ly:.1f}" fill="none" '
            f'stroke="{col}" stroke-width="0.9" opacity="0.55"/>')
    add(f'<circle cx="{R - 26}" cy="{dy:.1f}" r="{4.6 if hit else 3.6}" fill="{col}"/>')
    add(f'<text x="{R - 10}" y="{ly + 4:.1f}" font-size="11.5" fill="{col}" '
        f'font-weight="{700 if hit else 400}">tone {tone}'
        f'<tspan fill="{MUTE}" font-weight="400" font-size="10.5">'
        f'  {esc(NAMES[tone])}  {v:+.2f}</tspan></text>')
    if hit:
        add(f'<circle cx="{R - 40}" cy="{dy:.1f}" r="7" fill="{ACCENT}"/>')
        add(f'<text x="{R - 40}" y="{dy + 3.5:.1f}" font-size="9.5" fill="#ffffff" '
            f'font-weight="700" text-anchor="middle">{CONTRADICTS[tone]}</text>')

# ---- findings, as footnotes so nothing overlaps the plot ----
tr = MODEL["transitions"]
notes = [
    ("1", ['Tone 5 sits with tone 3, not tone 6. The ladder buckets 5 and 6 onto one rung,',
           f'but 6→5 rises {tr["65"]["up"] * 100:.1f}% of the time (n={tr["65"]["n"]:,}) '
           f'and 5→6 falls {tr["56"]["down"] * 100:.1f}% (n={tr["56"]["n"]:,}).']),
    ("2", [f'Tone 4 is a cliff, not a rung. The ladder puts it one step below tone 6; '
           f'measured, it is {levels["6"] - levels["4"]:.2f} semitones below,',
           'the largest gap between any two adjacent tones.']),
]
ny = BOT + 42
for num, lines in notes:
    add(f'<circle cx="39" cy="{ny - 4:.1f}" r="7" fill="{ACCENT}"/>')
    add(f'<text x="39" y="{ny - 0.5:.1f}" font-size="9.5" fill="#ffffff" '
        f'font-weight="700" text-anchor="middle">{num}</text>')
    for line in lines:
        add(f'<text x="54" y="{ny:.1f}" font-size="11" fill="{INK}">{esc(line)}</text>')
        ny += 16
    ny += 8

add(f'<text x="32" y="{H - 18}" font-size="10" fill="{MUTE}">'
    f'Ladder rungs are evenly spaced by construction: 0243 encodes order and '
    f'grouping, not distance.</text>')
add('</svg>')

out = ROOT / "docs" / "tone-levels.svg"
out.write_text("\n".join(o), encoding="utf-8")
print(f"wrote {out}")
