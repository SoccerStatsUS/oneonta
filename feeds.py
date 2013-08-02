import datetime
import feedparser
import time


feeds = [
    'http://www.ussoccer.com/news/news-landing.aspx?rss=true',
    'http://www.mlssoccer.com/news/feed',
    'http://feeds.washingtonpost.com/rss/rss_soccer-insider',
    'http://www.soccerbyives.net/feed',
    'http://www.concacaf.com/news/feed',
]


def parse_feed(url):
    data = feedparser.parse(url)

    entries = data['entries']

    l = []

    for e in entries:
        t = time.mktime(e['published_parsed'])
        l.append({
                'title': e['title'],
                'summary': e['summary'],
                'url': e['link'],
                'dt': datetime.datetime.fromtimestamp(t),
                })
        
    return sorted(l, key=lambda e: e['dt'])


def parse_feeds():
    l = []
    for feed in feeds:
        l.extend(parse_feed(feed))
    return l



if __name__ == "__main__":
    f = parse_feeds()
    print(f)
    print(len(f))
