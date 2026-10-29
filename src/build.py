"""Usage: python3 build.py [--standalone] out.html mon=mon.json tue=tue.json ...
Drops a week of puzzles into template.html. --standalone adds the html/head/body skeleton
the artifact host normally supplies, so the file works on any static host or opened locally."""
import json, os, sys

args = sys.argv[1:]
standalone = '--standalone' in args
args = [a for a in args if a != '--standalone']
week = {}
for arg in args[1:]:
    day, path = arg.split('=')
    P = json.load(open(path))
    week[day] = dict(seed=P['seed'], cells=P['cells'], clues=P['clues'], solution=P['solution'])
here = os.path.dirname(os.path.abspath(__file__))
html = open(os.path.join(here, 'template.html')).read().replace('__WEEK__', json.dumps(week, separators=(',', ':')))
if standalone:
    head, body = html.split('</style>\n', 1)
    html = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            '<meta name="description" content="A week of three-colour hex logic puzzles, after Inkwell\'s Fields.">\n'
            '<meta property="og:title" content="Hex Fields">\n'
            '<meta property="og:description" content="A week of three-colour hex logic puzzles, Monday to Sunday.">\n'
            + head + '\n:root { padding-block: env(safe-area-inset-top, 0px) env(safe-area-inset-bottom, 0px); }\n'
            'body { margin: 0; } [hidden] { display: none !important; }\n</style>\n</head>\n<body>\n'
            + body + '\n</body>\n</html>\n')
open(args[0], 'w').write(html)
