import calendar
import datetime
import urllib.request
import warnings
from html.parser import HTMLParser

import feedparser

from oneonta import articles

MAX_LEN = 1023
TIMEOUT = 60

feeds = [
    ('ESPN.com', 'https://www.espn.com/espn/rss/soccer/news'),
    # Refuses https; carries its whole archive back to 2012 (~6MB per fetch).
    ('American Soccer Now', 'http://americansoccernow.com/feed'),
    ('Soccer America', 'https://www.socceramerica.com/feed/'),
    # These three carry the article text in the feed.
    ('The Equalizer', 'https://equalizersoccer.com/feed/'),
    ('Society for American Soccer History', 'https://www.ussoccerhistory.org/feed/'),
    ('Backheeled', 'https://www.backheeled.com/rss/'),
    ('The Guardian', 'https://www.theguardian.com/football/mls/rss'),
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

        row = {
            'title': e.get('title', '')[:MAX_LEN],
            'summary': strip_html(e.get('summary', ''))[:MAX_LEN],
            'url': e.get('link', '')[:MAX_LEN],
            # published_parsed is UTC; s2 runs USE_TZ=False and wants naive local.
            'dt': datetime.datetime.fromtimestamp(calendar.timegm(published)),  # noqa: DTZ006
            'source': source,
        }
        # Some feeds carry the whole article. The archive keeps it; the
        # database never sees it.
        if e.get('content'):
            row['text'] = articles.paragraphs(e.content[0].value)
        l.append(row)

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
