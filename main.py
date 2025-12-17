import json
from pathlib import Path

# =========================
# THEMES (ORDEM ALFABÉTICA)
# =========================
THEMES = {
    "amber": {
        "bg": "#0b0f0d",
        "border": "#ffb300",
        "primary": "#ffca28",
        "secondary": "#ffe082",
        "text": "#eaeaea",
        "muted": "#9e9e9e",
    },
    "crimson": {
        "bg": "#0b0a0a",
        "border": "#c62828",
        "primary": "#e53935",
        "secondary": "#ef9a9a",
        "text": "#f5f5f5",
        "muted": "#9e9e9e",
    },
    "cyan": {
        "bg": "#050f12",
        "border": "#00acc1",
        "primary": "#26c6da",
        "secondary": "#80deea",
        "text": "#e0f7fa",
        "muted": "#90a4ae",
    },
    "emerald": {
        "bg": "#050d0a",
        "border": "#2e7d32",
        "primary": "#43a047",
        "secondary": "#a5d6a7",
        "text": "#e8f5e9",
        "muted": "#9e9e9e",
    },
    "orange": {
        "bg": "#0f0a05",
        "border": "#ef6c00",
        "primary": "#fb8c00",
        "secondary": "#ffcc80",
        "text": "#fff3e0",
        "muted": "#bdbdbd",
    },
    "purple": {
        "bg": "#0a0610",
        "border": "#7e57c2",
        "primary": "#9575cd",
        "secondary": "#d1c4e9",
        "text": "#ede7f6",
        "muted": "#b0bec5",
    },
    "red": {
        "bg": "#0f0505",
        "border": "#d32f2f",
        "primary": "#f44336",
        "secondary": "#ffcdd2",
        "text": "#ffebee",
        "muted": "#bdbdbd",
    },
    "slate": {
        "bg": "#0b0d10",
        "border": "#455a64",
        "primary": "#607d8b",
        "secondary": "#b0bec5",
        "text": "#eceff1",
        "muted": "#90a4ae",
    },
}

# =========================
# LOAD DATA
# =========================
BASE_DIR = Path(__file__).parent
LANG_FILE = BASE_DIR / "templates" / "cache_top_langs.json"

if LANG_FILE.exists():
    with open(LANG_FILE, encoding="utf-8") as f:
        LANGS = json.load(f)
else:
    # Fallback seguro (primeira execução / dev / preview)
    LANGS = {
        "Python": 42.0,
        "JavaScript": 28.5,
        "TypeScript": 14.3,
        "HTML": 9.2,
        "CSS": 6.0
    }


# =========================
# SVG GENERATOR
# =========================
def generate_svg(theme_name="orange"):
    t = THEMES[theme_name]

    lang_items = sorted(LANGS.items(), key=lambda x: x[1], reverse=True)[:5]

    lang_svg = ""
    y = 250
    for lang, percent in lang_items:
        width = int(420 * (percent / 100))
        lang_svg += f"""
        <text x="120" y="{y}" fill="{t['text']}" font-size="14">{lang}</text>
        <rect x="220" y="{y - 12}" width="420" height="8" rx="4" fill="#1c1c1c"/>
        <rect x="220" y="{y - 12}" width="{width}" height="8" rx="4" fill="{t['primary']}"/>
        <text x="650" y="{y}" fill="{t['muted']}" font-size="12">{percent:.1f}%</text>
        """
        y += 28

    return f"""
<svg width="1000" height="360" viewBox="0 0 1000 360" xmlns="http://www.w3.org/2000/svg">
  <rect x="10" y="10" rx="18" ry="18" width="980" height="340"
        fill="{t['bg']}" stroke="{t['border']}" stroke-width="2"/>

  <!-- ICON -->
  <circle cx="80" cy="80" r="34" fill="none" stroke="{t['primary']}" stroke-width="3"/>
  <text x="80" y="88" text-anchor="middle" font-size="22"
        fill="{t['primary']}" font-family="monospace">&lt;/&gt;</text>

  <!-- TITLE -->
  <text x="140" y="70" fill="{t['primary']}" font-size="24" font-weight="bold">
    Domisnnet · Developer Dashboard
  </text>
  <text x="140" y="96" fill="{t['muted']}" font-size="14">
    Da faísca da ideia à Constelação do código. Construindo um Universo de possibilidades!!
  </text>

  <!-- STATS -->
  <text x="140" y="130" fill="{t['text']}" font-size="14">📦 Repositórios: 39</text>
  <text x="300" y="130" fill="{t['text']}" font-size="14">⭐ Stars: 28</text>

  <!-- GRADE -->
  <circle cx="900" cy="80" r="36" fill="none" stroke="#1c1c1c" stroke-width="6"/>
  <circle cx="900" cy="80" r="36" fill="none" stroke="{t['primary']}"
          stroke-width="6" stroke-dasharray="170 60" transform="rotate(-90 900 80)"/>
  <text x="900" y="88" text-anchor="middle" font-size="22"
        fill="{t['text']}" font-weight="bold">A</text>

  <!-- LANGUAGES -->
  <text x="120" y="220" fill="{t['primary']}" font-size="18" font-weight="bold">
    Top Languages
  </text>

  {lang_svg}
</svg>
"""

# =========================
# OUTPUT
# =========================
svg = generate_svg("orange")
(Path("dashboard.svg")).write_text(svg, encoding="utf-8")