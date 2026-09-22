"""Faithful report extraction. Generated book artifacts; never executes report scripts."""
from pathlib import Path
from urllib.request import urlopen
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup, Tag
import json, hashlib, re, sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'public/books/f1'
SOURCE = 'https://brianbzeng.github.io/f1-stewarding-analysis/reports/the_cost_of_discretion_study_v2.html'
raw = Path(sys.argv[1]).read_bytes()
soup = BeautifulSoup(raw, 'html.parser')
main = soup.find('main')
OUT.mkdir(parents=True, exist_ok=True)
for node in main.select('script,style,.anchor-link'):
    node.decompose()
for a in main.find_all('a', href=True):
    if not a['href'].startswith('#'):
        a['href'] = urljoin(SOURCE, a['href'])
        a['target'] = '_blank'
        a['rel'] = 'noopener noreferrer'
for el in main.find_all(True):
    for attr in list(el.attrs):
        if attr not in ('href', 'id', 'src', 'alt', 'class', 'target', 'rel'):
            del el[attr]

blocks, chapters, figures, tables = [], [], [], []
chapter, section, number, pending = 'Introduction', 'introduction', 0, []
fig_counts = {}
def add(html, kind='text', **extra):
    global pending
    blocks.append(dict(html=html, kind=kind, chapter=chapter, section=section, anchors=pending, **extra))
    pending = []

def walk(el):
    global chapter, section, number, pending
    if not isinstance(el, Tag):
        return
    if el.get('id') and not el.get('id').startswith('cell-id'):
        pending.append(el['id'])
    if el.name == 'p' and not el.get_text(strip=True) and not el.find('img'):
        pending.extend(a['id'] for a in el.find_all('a', id=True))
        return
    if el.name == 'h1':
        return
    if 'report-author' in el.get('class', []):
        return
    if el.name == 'h3' and el.get_text(strip=True) == 'Index':
        return
    if 'toc' in el.get('class', []):
        return
    if el.name == 'h2':
        title = el.get_text(' ', strip=True)
        match = re.match(r'Chapter (\d+): (.*)', title)
        if match:
            number, chapter = int(match[1]), match[2]
            section = f'chapter-{number}'
        elif not chapters:
            add('<h2>Introduction</h2>', 'heading')
            return
        else:
            chapter = title
            section = 'methods' if title.startswith('Methods') else 'citations'
        chapters.append(dict(title=chapter, section=section, number=number if match else None))
        add(f'<p class="chapter-kicker">{("Chapter " + str(number)) if match else "Appendix"}</p><h2>{chapter}</h2>', 'chapter')
        return
    if el.name == 'p' and el.find('img'):
        for img in el.find_all('img'):
            fig_counts[number] = fig_counts.get(number, 0) + 1
            label = f'{number}.{fig_counts[number]}'
            url = urljoin(SOURCE, img['src'])
            filename = Path(urlparse(url).path).name
            dest = OUT / filename
            if not dest.exists():
                dest.write_bytes(urlopen(url).read())
            img['src'] = f'/books/f1/{filename}'
            figures.append(dict(number=label, src=img['src'], alt=img.get('alt', ''), source=url, sha256=hashlib.sha256(dest.read_bytes()).hexdigest()))
            add(str(img), 'figure', figure=label, src=img['src'], alt=img.get('alt', ''), caption='')
        return
    if 'figure-caption' in el.get('class', []):
        blocks[-1]['caption'] = el.decode_contents()
        return
    if el.name == 'table':
        rows = el.find_all('tr')
        heads = [th.get_text(' ', strip=True) for th in rows[0].find_all(['th', 'td'])]
        table_index = len(tables) + 1
        data_rows = rows[1:]
        tables.append(dict(index=table_index, headers=heads, rows=len(data_rows)))
        # Wide report tables become labeled entries, retaining every cell and URL.
        # This avoids shrinking six-column tables below readable book typography.
        for ri, row in enumerate(data_rows):
            cells = row.find_all(['td', 'th'])
            if table_index == 9:
                values = [cell.decode_contents() for cell in cells]
                add(f'<section class="citation-entry"><p class="entry-label">Decision {ri+1} / 418 · {values[0]} · {values[2]}</p><h4>{values[1]}</h4><p>{values[3]}</p><p class="citation-id">{values[4]}</p><p>{values[5]}</p></section>', 'entry', table=table_index, row=ri+1)
                continue
            fields = ''.join(f'<div class="table-field"><dt>{head.replace("_", " ")}</dt><dd>{cell.decode_contents()}</dd></div>' for head, cell in zip(heads, cells))
            add(f'<section class="table-entry"><p class="entry-label">Table {table_index} · Entry {ri+1} of {len(data_rows)}</p><dl>{fields}</dl></section>', 'entry', table=table_index, row=ri+1)
        return
    if el.name in ('ul', 'ol'):
        for i, li in enumerate(el.find_all('li', recursive=False)):
            add(f'<p class="list-item"><span>{str(i+1)+"." if el.name == "ol" else "•"}</span> {li.decode_contents()}</p>')
        return
    if el.name in ('p', 'h3', 'h4', 'blockquote', 'pre', 'summary') or any(c in el.get('class', []) for c in ('report-note', 'report-answer', 'report-method', 'stat-grid')):
        if el.get_text(strip=True):
            html = str(el)
            if el.name == 'summary':
                html = '<h3>' + el.decode_contents() + '</h3>'
            add(html, 'heading' if el.name in ('h3', 'h4', 'summary') else 'text')
        return
    for child in list(el.children):
        walk(child)

for child in list(main.children):
    walk(child)
assert len(figures) == 9
assert [t['rows'] for t in tables] == [5, 2, 4, 7, 9, 4, 5, 3, 418]
payload = dict(title='How Consistent Is Formula 1 Stewarding?', subtitle='What FIA decisions from 2018 to 2025 show about fault, penalties, and fairness', author='Brian Zeng', source=SOURCE, sourceSha256=hashlib.sha256(raw).hexdigest(), chapters=chapters, figures=figures, tables=tables, blocks=blocks)
(OUT / 'source.json').write_text(json.dumps(payload, ensure_ascii=False), encoding='utf-8')
print(json.dumps(dict(blocks=len(blocks), figures=len(figures), tables=tables, sourceSha256=payload['sourceSha256'])))
