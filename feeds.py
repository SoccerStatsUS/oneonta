import datetime
import feedparser
import time


feeds = [
    ('USSoccer.com', 'http://www.ussoccer.com/news/news-landing.aspx?rss=true'),
    ('MLSSoccer.com', 'http://www.mlssoccer.com/news/feed'),
    ('Soccer Insider', 'http://feeds.washingtonpost.com/rss/rss_soccer-insider'),
    ('SoccerByIves', 'http://www.soccerbyives.net/feed'),
    ('CONCACAF.com', 'http://www.concacaf.com/news/feed'),
    ('New York Times', 'http://www.nytimes.com/services/xml/rss/nyt/Soccer.xml'),
    ('American Soccer Now', 'http://http://americansoccernow.com/feed'),
    ('Fifa.com', 'http://www.fifa.com/associations/association=usa/news/rss.xml'),
    ('HoustonDynamo.com', 'http://www.houstondynamo.com/news/feed'),
    ('FCDallas.com', 'http://www.fcdallas.com/news/feed'),
    ('SoundersFC.com', 'http://feeds2.feedburner.com/Sounders'),
    ('PortlandTimbers.com', 'http://www.portlandtimbers.com/news/feed'),
    ('SportingKC.com', 'http://www.sportingkc.com/news/feed'),
    ('LAGalaxy.com', 'http://www.lagalaxy.com/news/feed'),
    ('NewYorkRedBulls.com', 'http://www.newyorkredbulls.com/news/feed'),
    ('DCUnited.com', 'http://www.dcunited.com/news/feed'),
    ('Chicago-Fire.com', 'http://www.chicago-fire.com/news/feed'),
]


def parse_feed(url, source):
    data = feedparser.parse(url)

    entries = data['entries']

    l = []

    for e in entries:
        t = time.mktime(e['published_parsed'])

        summary = e['summary']
        summary = summary.split('<')[0]

        l.append({
                'title': e['title'],
                'summary': summary,
                'url': e['link'],
                'dt': datetime.datetime.fromtimestamp(t),
                'source': source,
                })
        
    return sorted(l, key=lambda e: e['dt'])


def parse_feeds():
    l = []
    for source, url in feeds:
        l.extend(parse_feed(url, source))
    return l



if __name__ == "__main__":
    f = parse_feeds()
    print(f)
    print(len(f))
