import calendar
import datetime
import urllib.request
import warnings
from html.parser import HTMLParser

import feedparser

MAX_LEN = 1023
TIMEOUT = 60

feeds = [
    ('ESPN.com', 'https://www.espn.com/espn/rss/soccer/news'),
    # Refuses https; carries its whole archive back to 2012 (~6MB per fetch).
    ('American Soccer Now', 'http://americansoccernow.com/feed'),
]


class _Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


def strip_html(s):
    p = _Text()
    p.feed(s)
    p.close()
    return ' '.join(''.join(p.parts).split())


def parse_document(doc, source):
    data = feedparser.parse(doc)
    if not data.version:
        warnings.warn(f'{source}: not a feed')
        return []

    l = []
    for e in data.entries:
        published = e.get('published_parsed') or e.get('updated_parsed')
        if not published:
            continue

        l.append({
            'title': e.get('title', '')[:MAX_LEN],
            'summary': strip_html(e.get('summary', ''))[:MAX_LEN],
            'url': e.get('link', '')[:MAX_LEN],
            # published_parsed is UTC; s2 runs USE_TZ=False and wants naive local.
            'dt': datetime.datetime.fromtimestamp(calendar.timegm(published)),  # noqa: DTZ006
            'source': source,
        })

    return sorted(l, key=lambda e: e['dt'])


def parse_feed(url, source):
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT) as r:
            doc = r.read()
    except (OSError, ValueError) as e:
        warnings.warn(f'{source}: could not fetch {url} ({e})')
        return []
    return parse_document(doc, source)


def parse_feeds():
    l = []
    for source, url in feeds:
        l.extend(parse_feed(url, source))
    return l


if __name__ == "__main__":
    f = parse_feeds()
    for e in f[-10:]:
        print(e['dt'], e['source'], e['title'])
    print(len(f))
