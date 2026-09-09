"""
The news archive under data/: every feed item ever seen, and the text of
each article. The build reads this instead of the live feeds.

    data/items.jsonl                one line per item, in the order first seen
    data/text/<source>/<id>.txt     article paragraphs, one per blank-separated block;
                                    an empty file means the page was fetched and
                                    held no article
"""
import datetime
import hashlib
import json
import os
import re

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
ITEMS_PATH = os.path.join(DATA_DIR, 'items.jsonl')
TEXT_DIR = os.path.join(DATA_DIR, 'text')

ROW_KEYS = ('title', 'summary', 'url', 'dt', 'source')


def item_id(url):
    return hashlib.sha1(url.encode()).hexdigest()[:12]


def slug(name):
    return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')


def text_path(item):
    return os.path.join(TEXT_DIR, slug(item['source']), item_id(item['url']) + '.txt')


def read_items(path=None):
    path = path or ITEMS_PATH
    """Every archived item, as stored (dt is an ISO string)."""
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def add_items(rows, path=None):
    path = path or ITEMS_PATH
    """Append the feed rows whose url is not yet archived. Returns how many."""
    seen = {e['url'] for e in read_items(path)}
    today = datetime.date.today().isoformat()  # noqa: DTZ011
    added = 0
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'a') as f:
        for row in sorted(rows, key=lambda r: r['dt']):
            if row['url'] in seen:
                continue
            seen.add(row['url'])
            item = {k: row[k] for k in ROW_KEYS}
            item['dt'] = row['dt'].isoformat(' ')
            item['seen'] = today
            f.write(json.dumps(item) + '\n')
            added += 1
    return added


def load_items(path=None):
    path = path or ITEMS_PATH
    """The archive as the build loads it: the feed row keys, dt as a datetime."""
    rows = []
    for item in read_items(path):
        row = {k: item[k] for k in ROW_KEYS}
        row['dt'] = datetime.datetime.fromisoformat(item['dt'])
        rows.append(row)
    return rows


def has_text(item):
    return os.path.exists(text_path(item))


def write_text(item, paragraphs):
    path = text_path(item)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        f.write('\n\n'.join(paragraphs))
        if paragraphs:
            f.write('\n')


def read_text(item):
    with open(text_path(item)) as f:
        return [p.strip() for p in f.read().split('\n\n') if p.strip()]
