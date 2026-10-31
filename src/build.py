"""Build the whole site from sets.json:  python3 src/build.py [other-manifest.json]
The first set in sets.json is the latest and becomes index.html; every other set becomes
archive/<id>/index.html, and archive/index.html lists them all."""
import html as H, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = open(os.path.join(ROOT, 'src', 'template.html')).read()
HEAD = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
        '<meta name="description" content="Three-colour hex logic puzzles, after Inkwell\'s Fields.">\n'
        '<meta property="og:title" content="{title}">\n'
        '<meta property="og:description" content="Three-colour hex logic puzzles: specially shaped boards and a week from Monday to Sunday.">\n')
TAIL_CSS = ('\n:root { padding-block: env(safe-area-inset-top, 0px) env(safe-area-inset-bottom, 0px); }\n'
            'body { margin: 0; } [hidden] { display: none !important; }\n</style>\n</head>\n<body>\n')


def page(set_, links, title):
    week = {}
    for key, path in set_['puzzles'].items():
        P = json.load(open(os.path.join(ROOT, path)))
        week[key] = dict(seed=P['seed'], cells=P['cells'], clues=P['clues'], solution=P['solution'])
    meta = dict(id=set_['id'], title=set_['title'], date=set_['date'], links=links)
    doc = (TEMPLATE.replace('__WEEK__', json.dumps(week, separators=(',', ':')))
           .replace('__SET__', json.dumps(meta, separators=(',', ':')))
           .replace('<title>Hex Fields</title>', f'<title>{H.escape(title)}</title>'))
    head, body = doc.split('</style>\n', 1)
    return HEAD.format(title=H.escape(title)) + head + TAIL_CSS + body + '\n</body>\n</html>\n'


def archive_index(sets):
    items = []
    for i, s in enumerate(sets):
        href = '../' if i == 0 else f"{s['id']}/"
        tag = ' <span class="now">current</span>' if i == 0 else ''
        items.append(f'<li><a href="{href}">{H.escape(s["title"])}</a>{tag}'
                     f'<span class="date">{H.escape(s["date"])}</span><p>{H.escape(s["blurb"])}</p></li>')
    # styles mirror the game's tokens so the archive reads as the same site
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Hex Fields archive</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible:wght@400;700&family=Bricolage+Grotesque:opsz,wght@12..96,800&display=swap">
<style>
:root {{ --bg: #e9eee8; --surface: #f6f8f4; --ink: #16201a; --muted: #56655c; --line: #c6d0c7; --g: #3d9461;
  --display: "Bricolage Grotesque", "Avenir Next", system-ui, sans-serif; --body: "Atkinson Hyperlegible", Verdana, system-ui, sans-serif; }}
@media (prefers-color-scheme: dark) {{ :root {{ --bg: #111713; --surface: #18201b; --ink: #e6eee8; --muted: #95a59b; --line: #2b362f; --g: #46a46c; color-scheme: dark; }} }}
body {{ margin: 0; background: var(--bg); color: var(--ink); font: 16px/1.5 var(--body); }}
main {{ max-width: 600px; margin: 0 auto; padding: 28px max(16px, env(safe-area-inset-left, 0px)) 40px; }}
h1 {{ font-family: var(--display); font-weight: 800; font-size: 2rem; letter-spacing: -0.02em; margin: 0 0 4px; line-height: 1; }}
.sub {{ margin: 0 0 22px; color: var(--muted); }}
ul {{ list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 10px; }}
li {{ background: var(--surface); border: 1px solid var(--line); border-radius: 10px; padding: 14px 16px; }}
li a {{ font-family: var(--display); font-weight: 800; font-size: 1.25rem; color: var(--ink); text-underline-offset: 3px; }}
.date {{ color: var(--muted); margin-left: 10px; font-size: 0.9rem; }}
.now {{ font-size: 0.7rem; letter-spacing: 0.08em; text-transform: uppercase; color: var(--g); font-weight: 700; margin-left: 8px; }}
li p {{ margin: 4px 0 0; color: var(--muted); }}
</style>
</head>
<body>
<main>
<h1>Hex Fields</h1>
<p class="sub">Every set so far. Your progress on each puzzle is kept in this browser.</p>
<ul>{''.join(items)}</ul>
</main>
</body>
</html>
'''


def write(rel, text):
    path = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, 'w').write(text)
    print('wrote', rel)


sets = json.load(open(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'sets.json')))
latest, older = sets[0], sets[1:]
write('index.html', page(latest, [dict(label='Earlier puzzles', href='archive/')] if older else [], 'Hex Fields'))
for s in older:
    write(f"archive/{s['id']}/index.html",
          page(s, [dict(label='Latest puzzles', href='../../'), dict(label='All sets', href='../')], f"Hex Fields · {s['title']}"))
if older:
    write('archive/index.html', archive_index(sets))
