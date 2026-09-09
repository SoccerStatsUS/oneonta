import datetime
import pathlib

import pytest
from oneonta import feeds

FIXTURES = pathlib.Path(__file__).parent / 'fixtures'
KEYS = {'title', 'summary', 'url', 'dt', 'source'}


def local(*utc):
    tz = datetime.timezone.utc
    return datetime.datetime(*utc, tzinfo=tz).astimezone().replace(tzinfo=None)


def test_espn_rss():
    rows = feeds.parse_document((FIXTURES / 'espn.xml').read_bytes(), 'ESPN.com')
    assert len(rows) == 17
    assert all(set(r) == KEYS for r in rows)
    assert all(r['source'] == 'ESPN.com' for r in rows)
    assert rows == sorted(rows, key=lambda r: r['dt'])
    assert rows[0]['dt'] == local(2026, 9, 8, 23, 1, 14)
    assert rows[0]['url'].startswith('https://www.espn.com/soccer/')
    assert not any(r['dt'].tzinfo for r in rows)


def test_asn_atom():
    rows = feeds.parse_document((FIXTURES / 'asn.xml').read_bytes(), 'American Soccer Now')
    assert [r['dt'] for r in rows] == [
        local(2026, 9, 3, 16, 8, 17),
        local(2026, 9, 8, 14, 44, 52),
        local(2026, 9, 9, 2, 17, 16),
    ]
    assert rows[2]['title'].startswith('Euro Notebook')
    assert rows[2]['summary'].startswith("ASN's Brian Sciaretta")
    # HTML summary opening with a tag is stripped, not emptied
    assert rows[1]['summary'] == 'Pulisic & McKennie start for Milan & Juve.'
    # entry with no summary element falls back to its content, stripped
    assert rows[0]['summary'].startswith('ASN is here to get your Thursday')
    assert '<' not in rows[0]['summary']


def test_text_from_feed_content():
    rows = feeds.parse_document((FIXTURES / 'sash.xml').read_bytes(), 'Society for American Soccer History')
    assert len(rows) == 2
    assert all(len(r['text']) >= 5 for r in rows)
    assert rows[-1]['text'][0].startswith('I’m a retired newspaperman')
    assert rows[-1]['summary'].startswith('The “Milt Miller Collection”')
    for name in ('equalizer', 'backheeled'):
        rows = feeds.parse_document((FIXTURES / f'{name}.xml').read_bytes(), name)
        assert all(r['text'] for r in rows), name


def test_blogger_text():
    rows = feeds.parse_document((FIXTURES / 'dunord.atom').read_bytes(), 'du Nord')
    assert len(rows) == 2
    # a day's link roundup, split at its line breaks; then a one-line sign-off
    assert len(rows[0]['text']) > 50
    assert rows[1]['text'] == ['Just needed a break from things, sorry about that. Back soon.'] or len(rows[1]['text']) == 1
    assert rows[0]['url'].startswith('https://dunord.blogspot.com/2018/')
    assert feeds.blogger_page('https://b.blogspot.com/feeds/posts/default', 151) == \
        'https://b.blogspot.com/feeds/posts/default?max-results=150&start-index=151'


def test_no_text_key_without_content():
    for name in ('socceramerica', 'guardian-mls', 'espn'):
        rows = feeds.parse_document((FIXTURES / f'{name}.xml').read_bytes(), name)
        assert rows and not any('text' in r for r in rows), name


def test_strip_html():
    assert feeds.strip_html('<p>a <b>b</b>\n c</p>') == 'a b c'
    assert feeds.strip_html('plain &amp; simple') == 'plain & simple'
    assert feeds.strip_html('') == ''


def test_truncation():
    doc = (FIXTURES / 'espn.xml').read_text()
    head, items = doc.split('<item>', 1)
    doc = head + '<item>' + items.replace('<title>', '<title>' + 'x' * 2000, 1)
    rows = feeds.parse_document(doc, 'ESPN.com')
    assert max(len(r['title']) for r in rows) == 1023


def test_not_a_feed_warns():
    with pytest.warns(UserWarning, match='not a feed'):
        assert feeds.parse_document('<html><body>nope</body></html>', 'X') == []


def test_dead_host_warns():
    with pytest.warns(UserWarning, match='could not fetch'):
        assert feeds.parse_feed('http://127.0.0.1:9/feed', 'X') == []
