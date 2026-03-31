import os
import requests
import math

TOKEN = os.environ["GITHUB_TOKEN"]
USERNAME = os.environ.get("GITHUB_USERNAME", "SimeonVutov")

HEADERS = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

COLORS = {
    "C": "#555555",
    "C++": "#f34b7d",
    "Python": "#3572A5",
    "JavaScript": "#f1e05a",
    "TypeScript": "#2b7489",
    "Rust": "#dea584",
    "Go": "#00ADD8",
    "Java": "#b07219",
    "Scala": "#c22d40",
    "Shell": "#89e051",
    "Lua": "#000080",
    "HTML": "#e34c26",
    "CSS": "#563d7c",
    "Assembly": "#6E4C13",
    "VHDL": "#adb2cb",
    "Makefile": "#427819",
    "Nix": "#7e7eff",
    "Kotlin": "#F18E33",
    "Swift": "#ffac45",
    "Ruby": "#701516",
    "PHP": "#4F5D95",
    "Haskell": "#5e5086",
    "Zig": "#ec915c",
}

DEFAULT_COLOR = "#8b949e"


def fetch_all_repos():
    repos = []
    page = 1
    while True:
        resp = requests.get(
            f"https://api.github.com/user/repos?visibility=all&affiliation=owner&per_page=100&page={page}",
            headers=HEADERS
        )
        data = resp.json()
        if not data:
            break
        repos.extend(data)
        if len(data) < 100:
            break
        page += 1
    return repos


def fetch_languages(repo):
    resp = requests.get(repo["languages_url"], headers=HEADERS)
    return resp.json()


def aggregate_languages(repos):
    totals = {}
    for repo in repos:
        if repo.get("fork"):
            continue
        langs = fetch_languages(repo)
        for lang, byte_count in langs.items():
            totals[lang] = totals.get(lang, 0) + byte_count
    return totals


def generate_svg(lang_totals, top_n=8):
    sorted_langs = sorted(lang_totals.items(), key=lambda x: x[1], reverse=True)[:top_n]
    total_bytes = sum(b for _, b in sorted_langs)

    if total_bytes == 0:
        return "<svg></svg>"

    items = [(lang, b, round(b / total_bytes * 100, 2)) for lang, b in sorted_langs]

    card_width = 300
    padding = 16
    title_height = 40
    bar_section_height = 12
    bar_section_margin = 18
    lang_row_height = 22
    lang_rows = math.ceil(len(items) / 2)
    legend_height = lang_rows * lang_row_height + 10
    card_height = title_height + bar_section_height + bar_section_margin + legend_height + padding

    inner_width = card_width - padding * 2

    # compute cumulative x positions for each segment
    segments = []
    x = padding
    for i, (lang, _, pct) in enumerate(items):
        seg_width = round(pct / 100 * inner_width, 2)
        color = COLORS.get(lang, DEFAULT_COLOR)
        segments.append((lang, pct, seg_width, x, color))
        x += seg_width

    total_duration = 1.8  # seconds for full bar to load

    bar_parts = []
    cumulative_pct = 0
    for i, (lang, pct, seg_width, sx, color) in enumerate(segments):
        delay = round(cumulative_pct / 100 * total_duration, 3)
        dur = round(pct / 100 * total_duration, 3)
        cumulative_pct += pct

        # clip each segment growing from its own left edge
        clip_id = f"clip{i}"
        bar_parts.append(f'''
  <clipPath id="{clip_id}">
    <rect x="{sx}" y="{title_height}" width="{seg_width}" height="{bar_section_height}">
      <animate attributeName="width" from="0" to="{seg_width}" dur="{dur}s" begin="{delay}s" fill="freeze" calcMode="spline" keySplines="0.4 0 0.2 1" keyTimes="0;1"/>
    </rect>
  </clipPath>''')

        rx_attr = 'rx="3" ry="3"' if i == 0 or i == len(segments) - 1 else ''
        bar_parts.append(
            f'  <rect x="{sx}" y="{title_height}" width="{seg_width}" height="{bar_section_height}" '
            f'fill="{color}" {rx_attr} clip-path="url(#{clip_id})"/>'
        )

    legend_items = []
    legend_start_y = title_height + bar_section_height + bar_section_margin
    col_width = inner_width / 2

    for i, (lang, pct, _, _, color) in enumerate(segments):
        col = i % 2
        row = i // 2
        lx = padding + col * col_width
        ly = legend_start_y + row * lang_row_height + 12

        # stagger legend fade-in after bar finishes
        fade_delay = round(0.3 + i * 0.08, 2)
        legend_items.append(f'''
  <g opacity="0">
    <animate attributeName="opacity" from="0" to="1" dur="0.4s" begin="{fade_delay}s" fill="freeze"/>
    <circle cx="{lx + 5}" cy="{ly - 4}" r="4" fill="{color}"/>
    <text x="{lx + 14}" y="{ly - 1}" fill="#e6edf3" font-size="11" font-family="'Segoe UI',Ubuntu,Sans-Serif">{lang}</text>
    <text x="{lx + col_width - 4}" y="{ly - 1}" fill="#8b949e" font-size="11" font-family="'Segoe UI',Ubuntu,Sans-Serif" text-anchor="end">{pct}%</text>
  </g>''')

    bar_str = "\n".join(bar_parts)
    legend_str = "\n".join(legend_items)

    svg = f'''<svg width="{card_width}" height="{card_height}" viewBox="0 0 {card_width} {card_height}" xmlns="http://www.w3.org/2000/svg">
  <style>
    .title {{ font: 600 14px "Segoe UI", Ubuntu, Sans-Serif; fill: #e6edf3; }}
    .subtitle {{ font: 400 11px "Segoe UI", Ubuntu, Sans-Serif; fill: #8b949e; }}
  </style>
  <rect width="{card_width}" height="{card_height}" rx="6" fill="#0d1117" stroke="#30363d" stroke-width="1"/>
  <text x="{padding}" y="26" class="title">Most Used Languages</text>
  <!-- bar background -->
  <rect x="{padding}" y="{title_height}" width="{inner_width}" height="{bar_section_height}" rx="3" fill="#21262d"/>
{bar_str}
{legend_str}
</svg>'''

    return svg


def main():
    print("Fetching repos...")
    repos = fetch_all_repos()
    print(f"Found {len(repos)} repos (excluding forks)")

    print("Aggregating language data...")
    lang_totals = aggregate_languages(repos)
    print(f"Languages found: {list(lang_totals.keys())}")

    print("Generating SVG...")
    svg = generate_svg(lang_totals)

    os.makedirs("stats", exist_ok=True)
    with open("stats/languages.svg", "w") as f:
        f.write(svg)

    print("Done — stats/languages.svg written")


if __name__ == "__main__":
    main()
