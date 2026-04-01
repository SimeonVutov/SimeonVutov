import os
import requests
import math
 
TOKEN = os.environ["GITHUB_TOKEN"]
USERNAME = os.environ.get("GITHUB_USERNAME", "SimeonVutov")
CURRENT_YEAR = 2026
 
HEADERS = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}
 
COLORS = {
    # Systems / Low-level
    "C": "#555555",
    "C++": "#f34b7d",
    "Assembly": "#6E4C13",
    "Rust": "#dea584",
    "Zig": "#ec915c",
    "VHDL": "#adb2cb",
    "Verilog": "#b2b7f8",
    "SystemVerilog": "#DAE1C2",
    "Ada": "#02f88c",
    "Fortran": "#4d41b1",
    "D": "#ba595e",
    # Scripting / Shell
    "Shell": "#89e051",
    "Bash": "#89e051",
    "PowerShell": "#012456",
    "Lua": "#000080",
    "Perl": "#0298c3",
    "Tcl": "#e4cc98",
    "Awk": "#c30e9b",
    # General purpose
    "Python": "#3572A5",
    "Java": "#b07219",
    "Scala": "#c22d40",
    "Kotlin": "#F18E33",
    "Go": "#00ADD8",
    "Swift": "#ffac45",
    "Ruby": "#701516",
    "PHP": "#4F5D95",
    "Haskell": "#5e5086",
    "Elixir": "#6e4a7e",
    "Erlang": "#B83998",
    "Clojure": "#db5855",
    "OCaml": "#ef7a08",
    "F#": "#b845fc",
    "Crystal": "#000100",
    "Nim": "#ffc200",
    "Dart": "#00B4AB",
    "Groovy": "#e69f56",
    # Web
    "JavaScript": "#f1e05a",
    "TypeScript": "#2b7489",
    "HTML": "#e34c26",
    "CSS": "#563d7c",
    "SCSS": "#c6538c",
    "Sass": "#a53b70",
    "CoffeeScript": "#244776",
    "WebAssembly": "#04133b",
    # Data / Scientific
    "R": "#198CE7",
    "Julia": "#a270ba",
    "MATLAB": "#e16737",
    "Jupyter Notebook": "#DA5B0B",
    # Infrastructure / Config
    "Makefile": "#427819",
    "CMake": "#DA3434",
    "Dockerfile": "#384d54",
    "Nix": "#7e7eff",
    "HCL": "#844FBA",
    "Nushell": "#4E9906",
    # Markup / Data
    "Markdown": "#083fa1",
    "YAML": "#cb171e",
    "TOML": "#9c4221",
    "JSON": "#292929",
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
        if not resp.ok:
            raise Exception(f"GitHub API error {resp.status_code}: {data.get('message', data)}")
        if not isinstance(data, list):
            raise Exception(f"Unexpected response: {data}")
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
 
 
def fetch_github_stats(repos):
    total_stars = sum(r.get("stargazers_count", 0) for r in repos if not r.get("fork"))
 
    commit_headers = {**HEADERS, "Accept": "application/vnd.github.cloak-preview"}
    commit_resp = requests.get(
        f"https://api.github.com/search/commits?q=author:{USERNAME}+committer-date:{CURRENT_YEAR}-01-01..{CURRENT_YEAR}-12-31&per_page=1",
        headers=commit_headers
    )
    total_commits = commit_resp.json().get("total_count", 0)
 
    pr_resp = requests.get(
        f"https://api.github.com/search/issues?q=type:pr+author:{USERNAME}&per_page=1",
        headers=HEADERS
    )
    total_prs = pr_resp.json().get("total_count", 0)
 
    issue_resp = requests.get(
        f"https://api.github.com/search/issues?q=type:issue+author:{USERNAME}&per_page=1",
        headers=HEADERS
    )
    total_issues = issue_resp.json().get("total_count", 0)
 
    events_resp = requests.get(
        f"https://api.github.com/users/{USERNAME}/events?per_page=100",
        headers=HEADERS
    )
    events = events_resp.json() if events_resp.ok else []
    contributed_repos = set()
    for event in events:
        repo_name = event.get("repo", {}).get("name", "")
        if repo_name and not repo_name.startswith(f"{USERNAME}/"):
            contributed_repos.add(repo_name)
    contributed_to = len(contributed_repos)
 
    return {
        "stars": total_stars,
        "commits": total_commits,
        "prs": total_prs,
        "issues": total_issues,
        "contributed_to": contributed_to,
    }
 
 
def compute_grade(stats):
    score = (
        stats["stars"] * 4 +
        stats["commits"] * 1.45 +
        stats["prs"] * 2.5 +
        stats["issues"] * 1 +
        stats["contributed_to"] * 2
    )
    if score >= 5000: return "S"
    if score >= 3500: return "A+"
    if score >= 2000: return "A"
    if score >= 1000: return "A-"
    if score >= 600:  return "B+"
    if score >= 400:  return "B"
    if score >= 200:  return "C+"
    if score >= 100:  return "C"
    if score >= 50:   return "D"
    return "F"
 
 
def get_grade_color(grade):
    colors = {
        "S":  "#bc8cff",
        "A+": "#39d353",
        "A":  "#39d353",
        "A-": "#39d353",
        "B+": "#e3b341",
        "B":  "#e3b341",
        "C+": "#f85149",
        "C":  "#f85149",
        "D":  "#8b949e",
        "F":  "#8b949e",
    }
    return colors.get(grade, "#39d353")
 
 
def generate_stats_svg(stats):
    card_width = 400
    card_height = 140
    padding = 20
    bg_color = "#0d1117"
    border_color = "#30363d"
    text_primary = "#e6edf3"
    text_secondary = "#8b949e"
 
    grade = compute_grade(stats)
    accent = get_grade_color(grade)
 
    rows = [
        ("☆", f"Total Stars Earned:", stats["stars"]),
        ("⏱", f"Total Commits ({CURRENT_YEAR}):", stats["commits"]),
        ("⑂", "Total PRs:", stats["prs"]),
        ("⊙", "Total Issues:", stats["issues"]),
        ("⊟", "Contributed to:", stats["contributed_to"]),
    ]
 
    row_height = 19
    content_top = 42
    items_str = ""
    for i, (icon, label, value) in enumerate(rows):
        y = content_top + i * row_height
        items_str += (
            f'<text x="{padding}" y="{y}" fill="{accent}" font-size="12" '
            f'font-family="\'Segoe UI\',Ubuntu,Sans-Serif">{icon}</text>'
            f'<text x="{padding + 16}" y="{y}" fill="{text_primary}" font-size="12" font-weight="600" '
            f'font-family="\'Segoe UI\',Ubuntu,Sans-Serif">{label}</text>'
            f'<text x="230" y="{y}" fill="{text_secondary}" font-size="12" font-weight="600" '
            f'font-family="\'Segoe UI\',Ubuntu,Sans-Serif">{value}</text>'
        )
 
    cx, cy, r = 340, card_height // 2, 38
    circumference = 2 * math.pi * r
    dash = round(circumference * 0.75, 2)
    gap = round(circumference - dash, 2)
 
    grade_svg = (
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{border_color}" stroke-width="5"/>'
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{accent}" stroke-width="5" '
        f'stroke-dasharray="{dash} {gap}" stroke-linecap="round" '
        f'transform="rotate(-90 {cx} {cy})"/>'
        f'<text x="{cx}" y="{cy + 6}" fill="{accent}" font-size="18" font-weight="700" '
        f'font-family="\'Segoe UI\',Ubuntu,Sans-Serif" text-anchor="middle">{grade}</text>'
    )
 
    return f'''<svg width="{card_width}" height="{card_height}" viewBox="0 0 {card_width} {card_height}" xmlns="http://www.w3.org/2000/svg">
  <rect width="{card_width}" height="{card_height}" rx="6" fill="{bg_color}" stroke="{border_color}" stroke-width="1"/>
  <text x="{padding}" y="26" fill="{text_primary}" font-size="14" font-weight="700"
    font-family="'Segoe UI',Ubuntu,Sans-Serif">{USERNAME}'s GitHub Stats</text>
  {items_str}
  {grade_svg}
</svg>'''
 
 
def generate_languages_svg(lang_totals, top_n=8):
    sorted_langs = sorted(lang_totals.items(), key=lambda x: x[1], reverse=True)[:top_n]
    total_bytes = sum(b for _, b in sorted_langs)
    if total_bytes == 0:
        return "<svg></svg>"
 
    items = [(lang, b, round(b / total_bytes * 100, 2)) for lang, b in sorted_langs]
    card_width = 300
    padding = 16
    title_height = 40
    bar_height = 12
    bar_margin = 18
    row_height = 22
    lang_rows = math.ceil(len(items) / 2)
    legend_height = lang_rows * row_height + 10
    card_height = title_height + bar_height + bar_margin + legend_height + padding
    inner_width = card_width - padding * 2
    col_width = inner_width / 2
 
    # single clipPath rounds all corners uniformly
    bar_parts = [
        f'<clipPath id="barclip">'
        f'<rect x="{padding}" y="{title_height}" width="{inner_width}" height="{bar_height}" rx="3"/>'
        f'</clipPath>'
        f'<g clip-path="url(#barclip)">'
    ]
    x = padding
    for lang, _, pct in items:
        seg_width = round(pct / 100 * inner_width, 2)
        color = COLORS.get(lang, DEFAULT_COLOR)
        bar_parts.append(
            f'<rect x="{x}" y="{title_height}" width="{seg_width}" height="{bar_height}" fill="{color}"/>'
        )
        x += seg_width
    bar_parts.append('</g>')
 
    legend_parts = []
    legend_y = title_height + bar_height + bar_margin
    for i, (lang, _, pct) in enumerate(items):
        col = i % 2
        row = i // 2
        lx = padding + col * col_width
        ly = legend_y + row * row_height + 12
        color = COLORS.get(lang, DEFAULT_COLOR)
        legend_parts.append(
            f'<circle cx="{lx + 5}" cy="{ly - 4}" r="4" fill="{color}"/>'
            f'<text x="{lx + 14}" y="{ly - 1}" fill="#e6edf3" font-size="11" font-family="\'Segoe UI\',Ubuntu,Sans-Serif">{lang}</text>'
            f'<text x="{lx + col_width - 4}" y="{ly - 1}" fill="#8b949e" font-size="11" font-family="\'Segoe UI\',Ubuntu,Sans-Serif" text-anchor="end">{pct}%</text>'
        )
 
    bar_str = "\n  ".join(bar_parts)
    legend_str = "\n  ".join(legend_parts)
 
    return f'''<svg width="{card_width}" height="{card_height}" viewBox="0 0 {card_width} {card_height}" xmlns="http://www.w3.org/2000/svg">
  <style>.title {{ font: 600 14px "Segoe UI", Ubuntu, Sans-Serif; fill: #e6edf3; }}</style>
  <rect width="{card_width}" height="{card_height}" rx="6" fill="#0d1117" stroke="#30363d" stroke-width="1"/>
  <text x="{padding}" y="26" class="title">Most Used Languages</text>
  <rect x="{padding}" y="{title_height}" width="{inner_width}" height="{bar_height}" rx="3" fill="#21262d"/>
  {bar_str}
  {legend_str}
</svg>'''
 
 
def main():
    print("Fetching repos...")
    repos = fetch_all_repos()
    print(f"Found {len(repos)} repos")
 
    print("Aggregating language data...")
    lang_totals = aggregate_languages(repos)
    print(f"Languages found: {list(lang_totals.keys())}")
 
    print("Fetching GitHub stats...")
    stats = fetch_github_stats(repos)
    print(f"Stats: {stats}")
 
    os.makedirs("stats", exist_ok=True)
 
    print("Generating language SVG...")
    with open("stats/languages.svg", "w") as f:
        f.write(generate_languages_svg(lang_totals))
 
    print("Generating stats SVG...")
    with open("stats/github-stats.svg", "w") as f:
        f.write(generate_stats_svg(stats))
 
    print("Done — stats/languages.svg and stats/github-stats.svg written")
 
 
if __name__ == "__main__":
    main()
 
