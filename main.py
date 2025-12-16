import os
import json
import time
import logging
import requests
from collections import Counter
from datetime import datetime

# -----------------------------
# CONFIGURAÇÃO GERAL
# -----------------------------
logging.basicConfig(level=logging.INFO)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {
    "Accept": "application/vnd.github+json",
    **({"Authorization": f"Bearer {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}),
}

CACHE_FILE = ".cache_top_langs.json"
CACHE_TTL = 60 * 60 * 24  # 24h

# -----------------------------
# TEMAS
# -----------------------------
THEMES = {
    "merko": {
        "background": "#0a0f0d",
        "text": "#e6f1e8",
        "accent": "#00ffa6",
        "track": "#1f2d2a",
        "muted": "#7fa89a",
    },
    "dracula": {
        "background": "#282a36",
        "text": "#f8f8f2",
        "accent": "#bd93f9",
        "track": "#44475a",
        "muted": "#9a9a9a",
    },
    "radical": {
        "background": "#141321",
        "text": "#eaeaea",
        "accent": "#fe428e",
        "track": "#2a2a3a",
        "muted": "#9f9f9f",
    },
}

# -----------------------------
# CACHE
# -----------------------------
def load_cache() -> Counter | None:
    if not os.path.exists(CACHE_FILE):
        return None
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if time.time() - data.get("timestamp", 0) < CACHE_TTL:
            return Counter(data.get("langs", {}))
    except Exception:
        pass
    return None


def save_cache(langs: Counter):
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(
                {"timestamp": time.time(), "langs": dict(langs)},
                f,
            )
    except Exception:
        pass


# -----------------------------
# GITHUB API
# -----------------------------
def fetch_top_languages(username: str) -> Counter:
    cached = load_cache()
    if cached:
        logging.info("Usando cache de linguagens")
        return cached

    logging.info("Buscando linguagens na API do GitHub")
    url = f"https://api.github.com/users/{username}/repos?per_page=100&type=owner"
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status()

    counter = Counter()

    for repo in r.json():
        lang_url = repo.get("languages_url")
        if not lang_url:
            continue
        lr = requests.get(lang_url, headers=HEADERS, timeout=10)
        if lr.ok:
            for lang, size in lr.json().items():
                counter[lang] += size

    if counter:
        save_cache(counter)

    return counter


# -----------------------------
# SVG WOW — LANGUAGE INSIGHT
# -----------------------------
def render_language_insight_svg(langs: Counter, theme: dict) -> str:
    if not langs:
        return f'''
<svg width="720" height="200" xmlns="http://www.w3.org/2000/svg">
  <rect width="100%" height="100%" rx="16" fill="{theme['background']}"/>
  <text x="360" y="110" text-anchor="middle"
        font-family="Segoe UI, sans-serif"
        font-size="16" fill="{theme['text']}">
    Language data unavailable
  </text>
</svg>
'''

    total = sum(langs.values())
    top = langs.most_common(5)

    dominant_lang, dominant_size = top[0]
    dominant_pct = dominant_size / total * 100

    max_bar_width = 360
    updated = datetime.utcnow().strftime("%Y-%m-%d")

    def bar_width(value):
        return max(6, int((value / dominant_size) * max_bar_width))

    rows = []
    y = 180

    for i, (lang, size) in enumerate(top, start=1):
        pct = size / total * 100
        width = bar_width(size)
        color = theme["accent"] if i == 1 else theme["muted"]

        rows.append(f'''
  <text x="40" y="{y}" font-size="13" fill="{theme['text']}">{i}</text>
  <text x="70" y="{y}" font-size="13" fill="{theme['text']}">{lang}</text>
  <rect x="220" y="{y - 10}" width="{width}" height="10" rx="5"
        fill="{color}"/>
  <text x="600" y="{y}" font-size="13" fill="{theme['text']}">
    {pct:.1f}%
  </text>
''')
        y += 34

    return f'''
<svg width="720" height="360" viewBox="0 0 720 360"
     xmlns="http://www.w3.org/2000/svg">

  <rect width="100%" height="100%" rx="16"
        fill="{theme['background']}"/>

  <text x="32" y="40"
        font-family="Segoe UI, sans-serif"
        font-size="20" font-weight="700"
        fill="{theme['text']}">
    Top Languages · GitHub Activity
  </text>

  <text x="32" y="64"
        font-family="Segoe UI, sans-serif"
        font-size="14"
        fill="{theme['accent']}">
    Dominant Stack: {dominant_lang} ({dominant_pct:.1f}%)
  </text>

  <!-- Global bar -->
  <rect x="32" y="86" width="656" height="14" rx="7"
        fill="{theme['track']}"/>
  <rect x="32" y="86"
        width="{int((dominant_pct / 100) * 656)}"
        height="14" rx="7"
        fill="{theme['accent']}"/>

  {''.join(rows)}

  <text x="32" y="332"
        font-family="Segoe UI, sans-serif"
        font-size="12"
        fill="{theme['muted']}">
    Languages: {len(langs)} · Updated: {updated}
  </text>

</svg>
'''


# -----------------------------
# MAIN
# -----------------------------
def main():
    import sys

    if len(sys.argv) < 2:
        print("Uso: python main.py <github_username> [theme]")
        return

    username = sys.argv[1]
    theme_name = sys.argv[2] if len(sys.argv) > 2 else "merko"
    theme = THEMES.get(theme_name, THEMES["merko"])

    langs = fetch_top_languages(username)
    svg = render_language_insight_svg(langs, theme)

    with open("top-langs.svg", "w", encoding="utf-8") as f:
        f.write(svg)

    logging.info("SVG gerado com sucesso: top-langs.svg")


if __name__ == "__main__":
    main()