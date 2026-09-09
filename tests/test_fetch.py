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
