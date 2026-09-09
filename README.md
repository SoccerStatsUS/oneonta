# oneonta

Processing soccer news feeds. Reads RSS/Atom feeds and returns a flat list of news
items for the build to load.

## feeds.py

- `feeds` — the feed list, `(source name, feed url)` pairs
- `parse_document(doc, source)` — a feed document (bytes or str), parsed into dicts
  sorted by date; this is what the tests exercise
- `parse_feed(url, source)` — fetch one feed and parse it; warns and returns `[]`
  on any fetch or parse failure
- `parse_feeds()` — every feed in the list, concatenated

Each item is `{title, summary, url, dt, source}`. `dt` is a naive local datetime;
`source` is the display name from the feed list, not the url.

Run it on its own to print the newest items and the total count:

    cd ~/soccer
    build/.venv/bin/python -m oneonta.feeds

Tests parse saved copies of the feeds under `tests/fixtures`, so they need no network:

    build/.venv/bin/python -m pytest oneonta/tests

Depends on `feedparser`.

## Where this fits

The feeds are one leaf of the soccer pipeline:

    oneonta.parse_feeds() -> soccer_db.news -> s2 news.FeedItem -> /news/

The build calls it from `load_news()` (`build/make/load.py`), which loads the items
into mongo through `generic_load`. s2's own `load_news()` (`s2/build/load.py`) reads
that collection and creates a `FeedItem` per row.

Two couplings are worth knowing before editing the feed list:

- The source display name is looked up against `metadata/data/sources` by
  `make_source_getter` (`s2/build/getters.py`). A name that matches links the item to
  the existing `Source`; a name that doesn't creates a new one, silently.
- `news.FeedItem` declares `title`, `summary` and `url` as `CharField(max_length=1023)`.

## Current state

Two feeds: ESPN soccer, which exposes only the last day or so of items, and American
Soccer Now, which publishes its entire archive back to 2012 (about 6,500 items, a
6MB fetch) and is loaded in full. `load_news()` is still commented out in the build.
See [ROADMAP.md](ROADMAP.md) for what needs doing.
