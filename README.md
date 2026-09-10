# oneonta

Soccer news for the site. Reads RSS/Atom feeds (and two JSON indexes), keeps every
item and the text of its article in an archive under `data/`, and hands the build a
flat list of items.

## fetch.py

The command that talks to the network. It reads the feeds for new items, appends
them to the archive, then fetches the page of every archived item that has no text
yet, five seconds apart. Stop it whenever; the next run carries on.

    cd ~/soccer
    build/.venv/bin/python -m oneonta.fetch [--limit N] [--no-feeds] [--source NAME]

The five seconds are per site, so `--source NAME` lets a run per site go side by
side. `--backfill SOURCE` walks a feed back to its first post instead of reading the
feeds, for the feeds that page: Blogger, which is how du Nord and A Moment of
Brilliance, both long finished, got their whole runs into the archive, and the MLS
and NWSL content indexes. `--since DATE` stops the walk there, for MLS's index, which
reaches back to 2013 and eighty thousand stories.

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
- `STORY_APIS` — the JSON record behind a story on the Deltatre sites (MLS, NWSL), by
  host; `fetch_url(url)` is what `fetch.py` asks for, the record where there is one
  and the page otherwise, and `has_extractor(url)` says whether a site has either
- `extract(url, doc)` — the paragraphs of the page or record, or `[]` for an unknown
  site. A record's body is markdown parts, which `markdown_paragraphs` reduces to
  text: links to their text, headings dropped, list items one paragraph each
- `paragraphs(html)` — the paragraphs of a fragment, used for feeds that carry the
  article in the entry itself; markup with no `<p>` (Blogger) is split at line
  breaks and list items instead

A feed that carries the article text (The Equalizer, the Society for American
Soccer History, Backheeled) never needs a page fetch. A site with no `BODIES` entry
is never fetched at all; its items keep the feed summary only. Soccer America is
one, since its pages are paywalled to a teaser paragraph.

## feeds.py

- `feeds` — the feed list, `(source name, feed url)` pairs
- `INDEXES` — the sites with no RSS but a JSON content index behind them, by source
  name; their feed entries are generated from it
- `parse_document(doc, source)` — a feed document (bytes or str), parsed into dicts
  sorted by date; this is what the tests exercise. A document opening with `{` is
  taken for a content index page and parsed by `parse_stories`
- `page(url, skip)` — the feed's items after the first `skip`, for `--backfill`
- `parse_feed(url, source)` — fetch one feed and parse it; warns and returns `[]`
  on any fetch or parse failure
- `parse_feeds()` — every feed in the list, concatenated

Each item is `{title, summary, url, dt, source}`. `dt` is a naive local datetime;
`source` is the display name from the feed list, not the url.

mlssoccer.com and nwslsoccer.com publish no RSS; their feeds here are the JSON
content index behind each site (`dapi.<host>/v2/content/en-us/stories`), newest
first, one hundred stories a page. A story's url is `https://www.<host>/news/<slug>`,
and its text comes from the same index (`articles.STORY_APIS`), since the NWSL page
is a client-rendered shell with no text in it. The indexes are the leagues' own
output, so they carry vote promos and highlight roundups alongside the news. The USL
Championship feed is SportsEngine's, which answers only for the tag list the site's
News section links; its links carry a referral query that `parse_document` drops.

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

Twelve feeds. ESPN soccer and Soccer America for the daily volume, American Soccer
Now (which publishes its whole archive back to 2012, about 6,500 items, a 6MB fetch),
The Equalizer for the women's game, the Society for American Soccer History,
Backheeled for the lower leagues, the Guardian's MLS tag, MLSsoccer.com and
NWSLsoccer.com through their content indexes, the USL Championship, and two finished
Blogger blogs whose full runs are archived: du Nord, the daily American soccer link
roundup from 2005 to 2018, and A Moment of Brilliance. The archive holds them all and s2
serves them at `/news/`. See [ROADMAP.md](ROADMAP.md) for what needs doing.
