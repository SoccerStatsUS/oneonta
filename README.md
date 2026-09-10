# oneonta

Soccer news for the site. Reads RSS/Atom feeds (and one JSON index), keeps every
item and the text of its article in an archive under `data/`, and hands the build a
flat list of items.

## fetch.py

The command that talks to the network. It reads the feeds for new items, appends
them to the archive, then fetches the page of every archived item that has no text
yet, five seconds apart. Stop it whenever; the next run carries on.

    cd ~/soccer
    build/.venv/bin/python -m oneonta.fetch [--limit N] [--no-feeds]

`--backfill SOURCE` walks a feed back to its first post instead of reading the
feeds, for the feeds that page: Blogger, which is how du Nord and A Moment of
Brilliance, both long finished, got their whole runs into the archive, and the MLS
content index, which reaches back past 2016 and has not been walked.

Commit `data/` afterwards. The archive is the news history: the build reloads all of
it every time, so nothing is lost when the database is rebuilt.

## archive.py

- `data/items.jsonl` — one line per item in the order first seen, with the feed
  fields plus `seen`, the date it was first archived
- `data/text/<source>/<id>.txt` — the article's paragraphs, blank-line separated;
  `id` is the first twelve hex digits of the url's SHA-1. An empty file means the
  page was fetched and held no article (a 404, or a layout the extractor doesn't
  know), so it is not asked for again.
- `load_items()` — the archive as the build loads it
- `add_items(rows)` — append feed rows whose url is new

## articles.py

- `BODIES` — which element holds the story on each site, by host
- `extract(url, html)` — the paragraphs inside it, or `[]` for an unknown site
- `paragraphs(html)` — the paragraphs of a fragment, used for feeds that carry the
  article in the entry itself; markup with no `<p>` (Blogger) is split at line
  breaks and list items instead

A feed that carries the article text (The Equalizer, the Society for American
Soccer History, Backheeled) never needs a page fetch. A site with no `BODIES` entry
is never fetched at all; its items keep the feed summary only. Soccer America is
one, since its pages are paywalled to a teaser paragraph.

## feeds.py

- `feeds` — the feed list, `(source name, feed url)` pairs
- `parse_document(doc, source)` — a feed document (bytes or str), parsed into dicts
  sorted by date; this is what the tests exercise. A document opening with `{` is
  taken for the MLS content index and parsed by `parse_stories`
- `page(url, skip)` — the feed's items after the first `skip`, for `--backfill`
- `parse_feed(url, source)` — fetch one feed and parse it; warns and returns `[]`
  on any fetch or parse failure
- `parse_feeds()` — every feed in the list, concatenated

Each item is `{title, summary, url, dt, source}`. `dt` is a naive local datetime;
`source` is the display name from the feed list, not the url.

mlssoccer.com stopped publishing RSS; its feed here is the JSON content index behind
the site (`dapi.mlssoccer.com/v2/content/en-us/stories`), newest first, one hundred
stories a page. Each story's page is `https://www.mlssoccer.com/news/<slug>`, and the
article path fetches that like any other site. The index is the league's own output,
so it carries vote promos and highlight roundups alongside the news.

Run it on its own to print the newest items the feeds currently return:

    cd ~/soccer
    build/.venv/bin/python -m oneonta.feeds

Tests parse saved copies of the feeds and of one article page per site under
`tests/fixtures`, so they need no network:

    build/.venv/bin/python -m pytest oneonta/tests

Depends on `feedparser`.

## Where this fits

The feeds are one leaf of the soccer pipeline:

    feeds -> oneonta.fetch -> data/ -> archive.load_items() -> soccer_db.news
                                                          -> s2 news.FeedItem -> /news/

The build calls `load_items()` from `load_news()` (`build/make/load.py`), which loads
the items into mongo through `generic_load`. s2's own `load_news()`
(`s2/build/load.py`) reads that collection and creates a `FeedItem` per row, matching
the title, summary and text against the people on record to link each story to the
bios it names. Only the feed fields reach the database; the article text stays in
the archive.

Two couplings are worth knowing before editing the feed list:

- The source display name is looked up against `metadata/data/sources` by
  `make_source_getter` (`s2/build/getters.py`). A name that matches links the item to
  the existing `Source`; a name that doesn't creates a new one, silently.
- `news.FeedItem` declares `title`, `summary` and `url` as `CharField(max_length=1023)`.

## Current state

Ten feeds. ESPN soccer and Soccer America for the daily volume, American Soccer
Now (which publishes its whole archive back to 2012, about 6,500 items, a 6MB fetch),
The Equalizer for the women's game, the Society for American Soccer History,
Backheeled for the lower leagues, the Guardian's MLS tag, MLSsoccer.com through its
content index, and two finished Blogger blogs whose full runs are archived: du Nord,
the daily American soccer link roundup from 2005 to 2018, and A Moment of Brilliance. The archive holds them all and s2
serves them at `/news/`. See [ROADMAP.md](ROADMAP.md) for what needs doing.
