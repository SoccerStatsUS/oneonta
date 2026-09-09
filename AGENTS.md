# AGENTS.md

Read [README.md](README.md) first for what this package does and where it sits in the
pipeline; [ROADMAP.md](ROADMAP.md) has the open work.

This is a small repo — `feeds.py` is the whole of it. It is a sibling of `build`,
`s2`, `metadata` and `parse` under `~/soccer/`, and is imported as `oneonta.feeds`
with `~/soccer` on the path. There is no venv here; use the build's:

    cd ~/soccer
    build/.venv/bin/python -m oneonta.feeds

## Changing the feed list

- Verify a url before adding it. A live feed and a 200 are not the same thing: dead
  feeds have answered their old path with the site's HTML, with valid RSS holding no
  items, and with twenty items spread across three years. Check the content type,
  then check that the newest item is recent and that there are enough of them.
- Keep the display name matched to an entry in `metadata/data/sources`. An unmatched
  name doesn't fail, it quietly creates a second `Source` in s2.
- Feeds are fetched over the network in the middle of an otherwise offline build, so
  nothing here may raise on a dead host, a timeout or a malformed document. Warn and
  carry on.

## Output contract

`parse_feeds()` returns dicts consumed directly as `FeedItem(**row)` fields, so the
keys are fixed: `title`, `summary`, `url`, `dt`, `source`. Changing them means changing
`s2/build/load.py` and `s2/build/update.py` with it.

- s2 runs `USE_TZ = False`, so `dt` must be a naive *local* datetime. feedparser's
  `published_parsed` is UTC; convert with `calendar.timegm`, not `time.mktime`.
- Truncate `title`, `summary` and `url` to 1023 characters.
- Summaries arrive as HTML. Strip it — don't cut at the first `<`, which returns an
  empty string for any summary that opens with a tag.

## Be gentle

The sibling `scrapers` repo states the house request policy; the same spirit applies
here even though this is only a handful of feeds. Don't poll in a loop while testing —
save a response to a file and work against that. `tests/fixtures` has one per feed.
