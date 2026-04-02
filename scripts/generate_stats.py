import os
import requests
import math
import datetime

# --- Configuration ---
TOKEN = os.environ.get("GITHUB_TOKEN")
USERNAME = os.environ.get("GITHUB_USERNAME", "SimeonVutov")
CURRENT_YEAR = datetime.datetime.now().year

# Check for token
if not TOKEN:
    raise ValueError("GITHUB_TOKEN is missing! Ensure it's passed in the workflow env.")

HEADERS = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

COLORS = {
    # Systems / Low-level
    "C": "#555555", "C++": "#f34b7d", "Assembly": "#6E4C13",
    "Rust": "#dea584", "Zig": "#ec915c", "VHDL": "#adb2cb",
    "Verilog": "#b2b7f8", "SystemVerilog": "#DAE1C2", "Ada": "#02f88c",
    "Fortran": "#4d41b1", "D": "#ba595e",
    # Scripting / Shell
    "Shell": "#89e051", "Bash": "#89e051", "PowerShell": "#012456",
    "Lua": "#000080", "Perl": "#0298c3", "Tcl": "#e4cc98", "Awk": "#c30e9b",
    # General purpose / Software
    "Python": "#3572A5", "Java": "#b07219", "Scala": "#c22d40",
    "Kotlin": "#F18E33", "Go": "#00ADD8", "Swift": "#ffac45",
    "C#": "#178600", "Dart": "#00B4AB",
    # Web
    "JavaScript": "#f1e05a", "TypeScript": "#2b7489", "HTML": "#e34c26",
    "CSS": "#563d7c", "SCSS": "#c6538c", "WebAssembly": "#04133b",
    # Data / Persistence
    "R": "#198CE7", "Julia": "#a270ba", "MariaDB": "#003545", "SQLite": "#07405e",
    "NumPy": "#013243", "Jupyter Notebook": "#DA5B0B",
    # Infrastructure
    "Makefile": "#427819", "CMake": "#DA3434", "Dockerfile": "#384d54",
    "YAML": "#cb171e", "JSON": "#292929",
}

DEFAULT_COLOR = "#8b949e"

# --- Data Fetching ---

def fetch_all_repos():
    repos = []
    page = 1
    while True:
        resp = requests.get(
            f"https://api.github.com/user/repos?visibility=all&affiliation=owner&per_page=100&page={page}",
            headers=HEADERS
        )
        if not resp.ok: return repos
        data = resp.json()
        if not data or not isinstance(data, list): break
        repos.extend(data)
        if len(data) < 100: break
        page += 1
    return repos

def fetch_languages(repo):
    resp = requests.get(repo["languages_url"], headers=HEADERS)
    return resp.json() if resp.ok else {}

def aggregate_languages(repos):
    totals = {}
    for repo in repos:
        if repo.get("fork"): continue
        langs = fetch_languages(repo)
        for lang, byte_count in langs.items():
            if isinstance(byte_count, int):
                totals[lang] = totals.get(lang, 0) + byte_count
    return totals

def fetch_github_stats(repos):
    """Uses GraphQL for real-time contribution tracking to bypass Search indexing lag."""
    total_stars = sum(r.get("stargazers_count", 0) for r in repos if not r.get("fork"))

    query = """
    query($username: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $username) {
        contributionsCollection(from: $from, to: $to) {
          totalCommitContributions
          totalPullRequestContributions
          totalIssueContributions
        }
        # Lifetime totals for PRs and Issues
        pullRequests { totalCount }
        issues { totalCount }
      }
    }
    """
    variables = {
        "username": USERNAME,
        "from": f"{CURRENT_YEAR}-01-01T00:00:00Z",
        "to": f"{CURRENT_YEAR}-12-31T23:59:59Z"
    }

    resp = requests.post("https://api.github.com/graphql", headers=HEADERS, json={"query": query, "variables": variables})
    
    commits, prs, issues = 0, 0, 0
    if resp.ok:
        u = resp.json().get("data", {}).get("user", {})
        c_coll = u.get("contributionsCollection", {})
        commits = c_coll.get("totalCommitContributions", 0)
        prs = u.get("pullRequests", {}).get("totalCount", 0)
        issues = u.get("issues", {}).get("totalCount", 0)

    # Contributed to (repos pushed to but doesn't own)
    events_resp = requests.get(f"https://api.github.com/users/{USERNAME}/events?per_page=100", headers=HEADERS)
    events = events_resp.json() if events_resp.ok else []
    contrib_repos = {e.get("repo", {}).get("name") for e in events if e.get("repo") and not e["repo"]["name"].startswith(f"{USERNAME}/")}
    
    return {
        "stars": total_stars,
        "commits": commits,
        "prs": prs,
        "issues": issues,
        "contributed_to": len(contrib_repos),
    }

# --- Logic & SVG Generation ---

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
        "S": "#bc8cff", "A+": "#39d353", "A": "#39d353", "A-": "#39d353",
        "B+": "#e3b341", "B": "#e3b341", "C+": "#f85149", "C": "#f85149",
        "D": "#8b949e", "F": "#8b949e"
    }
    return colors.get(grade, "#39d353")

def generate_stats_svg(stats):
    card_width, card_height, padding = 400, 140, 20
    bg, border, p_text, s_text = "#0d1117", "#30363d", "#e6edf3", "#8b949e"
    
    grade = compute_grade(stats)
    accent = get_grade_color(grade)

    rows = [
        ("☆", "Total Stars Earned:", stats["stars"]),
        ("⏱", f"Total Commits ({CURRENT_YEAR}):", stats["commits"]),
        ("⑂", "Total PRs:", stats["prs"]),
        ("⊙", "Total Issues:", stats["issues"]),
        ("⊟", "Contributed to:", stats["contributed_to"]),
    ]

    items_str = ""
    for i, (icon, label, value) in enumerate(rows):
        y = 42 + i * 19
        items_str += (
            f'<text x="{padding}" y="{y}" fill="{accent}" font-size="12" font-family="\'Segoe UI\',Ubuntu,Sans-Serif">{icon}</text>'
            f'<text x="{padding + 16}" y="{y}" fill="{p_text}" font-size="12" font-weight="600" font-family="\'Segoe UI\',Sans-Serif">{label}</text>'
            f'<text x="230" y="{y}" fill="{s_text}" font-size="12" font-weight="600" font-family="\'Segoe UI\',Sans-Serif">{value}</text>'
        )

    cx, cy, r = 340, 70, 38
    dash = round(2 * math.pi * r * 0.75, 2)
    gap = round(2 * math.pi * r - dash, 2)

    return f'''<svg width="{card_width}" height="{card_height}" viewBox="0 0 {card_width} {card_height}" xmlns="http://www.w3.org/2000/svg">
  <rect width="{card_width}" height="{card_height}" rx="6" fill="{bg}" stroke="{border}" stroke-width="1"/>
  <text x="{padding}" y="26" fill="{p_text}" font-size="14" font-weight="700" font-family="'Segoe UI',Sans-Serif">{USERNAME}'s GitHub Stats</text>
  {items_str}
  <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{border}" stroke-width="5"/>
  <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{accent}" stroke-width="5" stroke-dasharray="{dash} {gap}" stroke-linecap="round" transform="rotate(-90 {cx} {cy})"/>
  <text x="{cx}" y="{cy + 6}" fill="{accent}" font-size="18" font-weight="700" font-family="'Segoe UI',Sans-Serif" text-anchor="middle">{grade}</text>
</svg>'''

def generate_languages_svg(lang_totals, top_n=8):
    sorted_langs = sorted(lang_totals.items(), key=lambda x: x[1], reverse=True)[:top_n]
    total_bytes = sum(b for _, b in sorted_langs)
    if total_bytes == 0: return "<svg></svg>"

    items = [(l, b, round(b/total_bytes*100, 2)) for l, b in sorted_langs]
    card_width, padding, bar_h = 300, 16, 12
    card_height = 80 + (math.ceil(len(items)/2) * 22)
    inner_w = card_width - padding*2

    bar_parts = [f'<clipPath id="bc"><rect x="{padding}" y="40" width="{inner_w}" height="{bar_h}" rx="3"/></clipPath>', '<g clip-path="url(#bc)">']
    x_off = padding
    for l, _, p in items:
        w = round(p/100 * inner_w, 2)
        bar_parts.append(f'<rect x="{x_off}" y="40" width="{w}" height="{bar_h}" fill="{COLORS.get(l, DEFAULT_COLOR)}"/>')
        x_off += w
    bar_parts.append('</g>')

    legend_parts = []
    for i, (l, _, p) in enumerate(items):
        lx, ly = padding + (i%2)*(inner_w/2), 70 + (i//2)*22
        legend_parts.append(f'<circle cx="{lx+5}" cy="{ly-4}" r="4" fill="{COLORS.get(l, DEFAULT_COLOR)}"/>'
                           f'<text x="{lx+14}" y="{ly-1}" fill="#e6edf3" font-size="11" font-family="\'Segoe UI\',Sans-Serif">{l}</text>'
                           f'<text x="{lx+(inner_w/2)-4}" y="{ly-1}" fill="#8b949e" font-size="11" font-family="\'Segoe UI\',Sans-Serif" text-anchor="end">{p}%</text>')

    return f'''<svg width="{card_width}" height="{card_height}" viewBox="0 0 {card_width} {card_height}" xmlns="http://www.w3.org/2000/svg">
  <rect width="{card_width}" height="{card_height}" rx="6" fill="#0d1117" stroke="#30363d" stroke-width="1"/>
  <text x="{padding}" y="26" fill="#e6edf3" font-size="14" font-weight="700" font-family="'Segoe UI',Sans-Serif">Most Used Languages</text>
  <rect x="{padding}" y="40" width="{inner_w}" height="{bar_h}" rx="3" fill="#21262d"/>
  {"".join(bar_parts)} {"".join(legend_parts)}
</svg>'''

# --- Main ---

def main():
    repos = fetch_all_repos()
    lang_totals = aggregate_languages(repos)
    stats = fetch_github_stats(repos)
    
    os.makedirs("stats", exist_ok=True)
    with open("stats/languages.svg", "w") as f: f.write(generate_languages_svg(lang_totals))
    with open("stats/github-stats.svg", "w") as f: f.write(generate_stats_svg(stats))
    print(f"Stats generated for {USERNAME} (Grade: {compute_grade(stats)})")

if __name__ == "__main__":
    main()
