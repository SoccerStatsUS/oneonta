import calendar
import datetime
import json
import urllib.request
import warnings
from html.parser import HTMLParser

import feedparser

from oneonta import articles

MAX_LEN = 1023
TIMEOUT = 60
PAGE = 100

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
    # Blogger. Both finished; their whole runs are in the archive
    # (`python -m oneonta.fetch --backfill`).
    ('du Nord', 'https://dunord.blogspot.com/feeds/posts/default'),
    ('A Moment of Brilliance: A Soccer History Blog',
     'https://amofb.blogspot.com/feeds/posts/default'),
    # No RSS; this is the JSON content index behind the site, newest first.
    ('MLSSoccer.com', f'https://dapi.mlssoccer.com/v2/content/en-us/stories?$limit={PAGE}'),
]

STORY_URL = 'https://www.mlssoccer.com/news/{}'


def page(url, skip):
    """
    The feed's items after the first `skip`, for walking a whole history.
    Blogger counts entries from 1; the dapi index skips from 0.
    """
    if 'dapi.mlssoccer.com' in url:
        return f'{url}&$skip={skip}'
    return f'{url}?max-results={PAGE}&start-index={skip + 1}'


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


def parse_stories(data, source):
    """The dapi content index: title, slug, summary and a UTC contentDate."""
    l = []
    for item in data['items']:
        dt = datetime.datetime.fromisoformat(item['contentDate'])
        l.append({
            'title': item.get('title', '')[:MAX_LEN],
            'summary': strip_html(item.get('summary') or '')[:MAX_LEN],
            'url': STORY_URL.format(item['slug'])[:MAX_LEN],
            'dt': dt.astimezone().replace(tzinfo=None),
            'source': source,
        })
    return sorted(l, key=lambda e: e['dt'])


def parse_document(doc, source):
    if doc.lstrip()[:1] in (b'{', '{'):
        try:
            return parse_stories(json.loads(doc), source)
        except (ValueError, KeyError, TypeError):
            warnings.warn(f'{source}: not a feed')
            return []
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
