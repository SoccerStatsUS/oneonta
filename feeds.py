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

# The tags the USL Championship site's News section links; its feed answers
# only for a tag list, the bare path is a 404.
USL_TAGS = ('2425607,2356889,2356907,2356901,2356896,2356886,2356893,2356900,2356892,2356911,2356895,2356899,2356888,2356887,2356904,2356919,2356921,2356942,2356922,2356939,2356915,2356916,2356944,2356918,2356938,2356943,2356914,2356920,2356941,2356913,2430134,2424354,2427472,2424366,2427468,2424346,2430124,2424350,2424360,2427466,2580152,2424352,2427467,2424370,2453473,2482866,2482961,2482971,2453476,2447544,2580135,2639268,2428854,2454163,2357328,2451565,2424358,2603770,2425682')

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
    ('USL Championship', 'https://www.uslchampionship.com/news_rss_feed?tags=' + USL_TAGS),
]

# Sites with no RSS but a JSON content index behind them (Deltatre), newest
# first. Their stories live at https://www.<host>/news/<slug>, and the page is
# fetched through the same index (`articles.STORY_APIS`).
INDEXES = {
    'MLSSoccer.com': 'mlssoccer.com',
    'NWSLsoccer.com': 'nwslsoccer.com',
}
feeds += [(name, f'https://dapi.{host}/v2/content/en-us/stories?$limit={PAGE}')
          for name, host in INDEXES.items()]


def page(url, skip):
    """
    The feed's items after the first `skip`, for walking a whole history.
    Blogger counts entries from 1; the dapi index skips from 0.
    """
    if 'dapi.' in url:
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
    """A content index page: title, slug, summary and a UTC contentDate."""
    l = []
    for item in data['items']:
        dt = datetime.datetime.fromisoformat(item['contentDate'])
        l.append({
            'title': item.get('title', '')[:MAX_LEN],
            'summary': strip_html(item.get('summary') or '')[:MAX_LEN],
            'url': f'https://www.{INDEXES[source]}/news/{item["slug"]}'[:MAX_LEN],
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

        link = e.get('link', '')
        # SportsEngine tags every link with a referral; the archive keys on the url.
        if 'referral=rss' in link:
            link = link.split('?', 1)[0]
        row = {
            'title': e.get('title', '')[:MAX_LEN],
            'summary': strip_html(e.get('summary', ''))[:MAX_LEN],
            'url': link[:MAX_LEN],
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
    # SportsEngine answers Python's default agent with a 403.
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
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
