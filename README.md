# oneonta

Processing soccer news feeds. Reads RSS/Atom feeds and returns a flat list of news
items for the build to load.

## feeds.py

- `feeds` — the feed list, `(source name, feed url)` pairs
- `parse_feed(url, source)` — one feed, parsed into dicts sorted by date
- `parse_feeds()` — every feed in the list, concatenated

Each item is `{title, summary, url, dt, source}`. `dt` is a naive local datetime;
`source` is the display name from the feed list, not the url.

Run it on its own to print what the feeds currently return:

    cd ~/soccer
    build/.venv/bin/python -m oneonta.feeds

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

`load_news()` is commented out in the build, and most of the feed list has gone dead
since it was written — the MLS network dropped RSS entirely, and several other feeds
now answer their old urls with HTML. See [ROADMAP.md](ROADMAP.md) for what is still
live and what needs doing.
