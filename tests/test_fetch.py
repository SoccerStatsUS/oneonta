import io
import urllib.request
from urllib.error import HTTPError

import pytest
from oneonta import archive, fetch

ESPN = 'https://www.espn.com/soccer/story/_/id/1/a'
PAGE = '<div class="article-body"><p>one</p><p>two</p></div>'


class Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        pass


def fake_urlopen(answers, calls):
    def urlopen(req, timeout=None):
        calls.append(req.full_url)
        answer = answers.pop(0)
        if isinstance(answer, int):
            raise HTTPError(req.full_url, answer, 'nope', {}, None)
        return Response(answer.encode())
    return urlopen


@pytest.fixture
def quiet(monkeypatch, tmp_path):
    monkeypatch.setattr(fetch.time, 'sleep', lambda s: None)
    monkeypatch.setattr(archive, 'TEXT_DIR', str(tmp_path / 'text'))
    monkeypatch.setattr(archive, 'ITEMS_PATH', str(tmp_path / 'items.jsonl'))


def item(url):
    return {'title': 't', 'summary': 's', 'url': url, 'source': 'ESPN.com', 'dt': '2026-09-09 12:00:00'}


def test_fetch_text(quiet, monkeypatch):
    calls = []
    monkeypatch.setattr(urllib.request, 'urlopen', fake_urlopen([PAGE], calls))
    assert fetch.fetch_text(item(ESPN)) == 2
    assert calls == [ESPN]
    assert archive.read_text(item(ESPN)) == ['one', 'two']


def test_non_ascii_url_is_quoted(quiet, monkeypatch):
    url = 'https://www.espn.com/soccer/story/_/id/1/kær?x=1&y=%20'
    calls = []
    monkeypatch.setattr(urllib.request, 'urlopen', fake_urlopen([PAGE], calls))
    assert fetch.fetch_text(item(url)) == 2
    assert calls == ['https://www.espn.com/soccer/story/_/id/1/k%C3%A6r?x=1&y=%20']
    # archived under the url as the feed gave it
    assert archive.read_text(item(url)) == ['one', 'two']


def test_404_is_recorded_not_retried(quiet, monkeypatch):
    calls = []
    monkeypatch.setattr(urllib.request, 'urlopen', fake_urlopen([404], calls))
    assert fetch.fetch_text(item(ESPN)) == 0
    assert calls == [ESPN]
    assert archive.has_text(item(ESPN))
    assert archive.read_text(item(ESPN)) == []


def test_transient_failure_retries(quiet, monkeypatch):
    calls = []
    monkeypatch.setattr(urllib.request, 'urlopen', fake_urlopen([503, 429, PAGE], calls))
    assert fetch.fetch_text(item(ESPN)) == 2
    assert len(calls) == 3


def test_gives_up_after_retries(quiet, monkeypatch):
    calls = []
    monkeypatch.setattr(urllib.request, 'urlopen', fake_urlopen([503, 503, 503], calls))
    with pytest.raises(HTTPError):
        fetch.fetch_text(item(ESPN))
    assert not archive.has_text(item(ESPN))


def test_fetch_missing_skips_archived(quiet, monkeypatch, capsys):
    other = ESPN + 'b'
    with open(archive.ITEMS_PATH, 'w') as f:
        f.write('{"title":"t","summary":"s","url":"%s","source":"ESPN.com","dt":"2026-09-09 12:00:00"}\n' % ESPN)
        f.write('{"title":"t","summary":"s","url":"%s","source":"ESPN.com","dt":"2026-09-09 13:00:00"}\n' % other)
    archive.write_text(item(ESPN), ['done'])
    calls = []
    monkeypatch.setattr(urllib.request, 'urlopen', fake_urlopen([PAGE], calls))
    fetch.fetch_missing()
    assert calls == [other]
    assert 'fetched 1, 0 with no text, 0 failed' in capsys.readouterr().out


def test_update_items_takes_text_from_the_feed(quiet, monkeypatch, capsys):
    import datetime
    sash = dict(item('https://www.ussoccerhistory.org/a/'), dt=datetime.datetime(2026, 9, 9, 12), text=['from', 'feed'])
    # a site with an extractor gets its page fetched; the feed's content is a teaser
    espn = dict(item(ESPN), dt=datetime.datetime(2026, 9, 9, 13), text=['teaser'])
    monkeypatch.setattr(fetch.feeds, 'parse_feeds', lambda: [sash, espn])
    assert fetch.update_items() == 2
    assert archive.read_text(sash) == ['from', 'feed']
    assert not archive.has_text(espn)
    assert '2 new items from the feeds, 1 texts taken from the feeds' in capsys.readouterr().out
    assert fetch.update_items() == 0


def test_fetch_missing_skips_sites_without_an_extractor(quiet, monkeypatch, capsys):
    sa = 'https://www.socceramerica.com/story/'
    with open(archive.ITEMS_PATH, 'w') as f:
        f.write('{"title":"t","summary":"s","url":"%s","source":"Soccer America","dt":"2026-09-09 12:00:00"}\n' % sa)
    calls = []
    monkeypatch.setattr(urllib.request, 'urlopen', fake_urlopen([], calls))
    fetch.fetch_missing()
    assert calls == []
    assert '1 items without text, 1 on sites with no extractor, fetching 0' in capsys.readouterr().out


def test_backfill_walks_the_pages(quiet, monkeypatch, capsys):
    import datetime
    url = 'https://dunord.blogspot.com/feeds/posts/default'
    monkeypatch.setattr(fetch.feeds, 'feeds', [('du Nord', url)])
    monkeypatch.setattr(fetch.feeds, 'PAGE', 2)
    pages = {
        1: [dict(item('https://dunord.blogspot.com/a'), source='du Nord', dt=datetime.datetime(2018, 1, 1), text=['a']),
            dict(item('https://dunord.blogspot.com/b'), source='du Nord', dt=datetime.datetime(2017, 1, 1), text=['b'])],
        3: [dict(item('https://dunord.blogspot.com/c'), source='du Nord', dt=datetime.datetime(2005, 1, 1), text=['c'])],
        5: [],
    }
    asked = []
    def parse_feed(page_url, source):
        asked.append(page_url)
        start = int(page_url.rsplit('=', 1)[1])
        return pages[start]
    monkeypatch.setattr(fetch.feeds, 'parse_feed', parse_feed)
    assert fetch.backfill('du Nord') == 3
    assert asked == [f'{url}?max-results=2&start-index={n}' for n in (1, 3, 5)]
    assert [e['title'] for e in archive.read_items()] == ['t', 't', 't']
    assert [e['dt'] for e in archive.read_items()] == ['2005-01-01 00:00:00', '2017-01-01 00:00:00', '2018-01-01 00:00:00']
    assert archive.read_text(pages[3][0]) == ['c']
    assert '3 items in the history of du Nord' in capsys.readouterr().out
