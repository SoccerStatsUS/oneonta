import datetime

from oneonta import archive

ROW = {'title': 'A', 'summary': 'a', 'url': 'http://x/a', 'source': 'ESPN.com',
       'dt': datetime.datetime(2026, 9, 9, 12, 30)}
ROW2 = dict(ROW, title='B', url='http://x/b', dt=datetime.datetime(2026, 9, 8, 1, 0))


def test_add_and_load(tmp_path):
    path = tmp_path / 'items.jsonl'
    assert archive.add_items([ROW, ROW2], path) == 2
    assert archive.add_items([ROW, dict(ROW, title='changed')], path) == 0

    rows = archive.load_items(path)
    assert [r['title'] for r in rows] == ['B', 'A']
    assert set(rows[0]) == set(archive.ROW_KEYS)
    assert rows[1]['dt'] == ROW['dt']
    assert archive.read_items(path)[0]['seen'] == datetime.date.today().isoformat()


def test_load_missing(tmp_path):
    assert archive.load_items(tmp_path / 'none.jsonl') == []


def test_text_round_trip(tmp_path, monkeypatch):
    monkeypatch.setattr(archive, 'TEXT_DIR', str(tmp_path))
    assert not archive.has_text(ROW)
    archive.write_text(ROW, ['one', 'two'])
    assert archive.has_text(ROW)
    assert archive.read_text(ROW) == ['one', 'two']
    assert archive.text_path(ROW).startswith(str(tmp_path / 'espn-com'))

    archive.write_text(ROW2, [])
    assert archive.has_text(ROW2)
    assert archive.read_text(ROW2) == []


def test_slug():
    assert archive.slug('ESPN.com') == 'espn-com'
    assert archive.slug('American Soccer Now') == 'american-soccer-now'
