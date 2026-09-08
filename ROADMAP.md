# ROADMAP.md — Development Roadmap

Open work only; completed items are removed as they land (see git history).

This package feeds `load_news()` in the build repo (`build/make/load.py`), which
loads `parse_feeds()` into `soccer_db.news`; s2 then builds `news.FeedItem` from
that collection. `load_news()` is currently commented out at `build/make/load.py:204`.

---

## Feed List

Every URL below was checked on 2026-09-08.

- [ ] Replace the dead feeds. Of the 17 entries in `feeds.py`, two still return a
  parseable, current feed: New York Times (only via `rss.nytimes.com`, not the
  `www.nytimes.com` path in the list) and American Soccer Now (once the doubled
  `http://http://` in its URL is fixed).
- [ ] Drop the MLS network feeds — MLSSoccer.com and all nine club feeds 404. The
  league consolidated onto one site that publishes no RSS.
- [ ] Drop USSoccer.com and CONCACAF.com — both now answer the old feed URLs with
  the site's HTML, so feedparser gets a page, not a feed.
- [ ] Drop Fifa.com (403), SoccerByIves (404), Washington Post Soccer Insider (valid
  RSS, zero items) and the Sounders feedburner (newest item 2015-10-01).
- [ ] Add ESPN soccer — `https://www.espn.com/espn/rss/soccer/news` is live and
  current, and `ESPN.com` is already in `metadata/data/sources`.
- [ ] Find replacements for the US-soccer-specific coverage the MLS and federation
  feeds used to supply. The surviving list is two general feeds.
- [ ] The American Soccer Now feed returns ~6MB of Atom on every fetch and appears
  to carry its whole archive. Decide whether to cap what gets parsed from it.

## Parsing

- [ ] `parse_feed` raises `KeyError` on any entry without `published_parsed` or
  `summary`. Skip undated entries and fall back for a missing summary.
- [ ] Timestamps are off by the local UTC offset — `published_parsed` is a UTC
  `struct_time` and `time.mktime` reads it as local. Use `calendar.timegm`, which
  gives the naive local datetime s2 expects (`USE_TZ = False`).
- [ ] `summary.split('<')[0]` returns an empty string whenever the summary opens
  with a tag, which is most of them. Strip the markup instead.
- [ ] Truncate title, summary and url to 1023 characters — `news.FeedItem` declares
  all three as `CharField(max_length=1023)`.
- [ ] One unreachable or malformed feed currently fails the whole run. Catch per
  feed, warn, and continue, so a build without network still completes.

## Build Integration

- [ ] Enable `load_news()` at `build/make/load.py:204` and replace the stale comment
  above it ("the oneonta package it imports is not installed").
- [ ] Declare the `feedparser` dependency and add it to the build's
  `requirements3.txt` and `.venv`. It is imported here and listed nowhere.
- [ ] No tests. At minimum, parse a saved feed fixture and assert the shape of the
  returned dicts against what `FeedItem` accepts.

## News History

- [ ] Every full build wipes the news history. `news` is in `SINGLE_SOURCES`, so
  `clear_all()` drops it, and the reload only recovers whatever the live feeds
  currently expose — roughly the last few weeks. `news/models.py` carries a note
  about this ("Going to have to figure out how to save these while rebuilding the
  database"). Either accept the rolling window or stop dropping `news` and insert
  only URLs not already present; `s2/build/update.py` already has that logic.
- [ ] Decide where feed URLs belong. They are hardcoded here while their display
  names have to match `metadata/data/sources` for `make_source_getter` to link a
  `FeedItem` to an existing `Source` rather than creating a new one — "American
  Soccer Now" has no entry there today.

## Deferred

- Fetching feeds during the build at all. It puts a network dependency in the middle
  of an otherwise offline pipeline. Splitting the fetch into a separate scheduled job
  that appends to mongo would be better, but that only matters once the news history
  is worth preserving.
