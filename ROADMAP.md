# ROADMAP.md — Development Roadmap

Open work only; completed items are removed as they land (see git history).

This package feeds `load_news()` in the build repo (`build/make/load.py`), which
loads `parse_feeds()` into `soccer_db.news`; s2 then builds `news.FeedItem` from
that collection.

---

## Feed List

- [ ] Find more US-soccer coverage. The list is ESPN soccer plus American Soccer Now;
  the MLS network and the federations no longer publish RSS. Candidates need checking
  the way AGENTS.md describes — the NYT soccer feed, for instance, still parses but
  holds twenty items spread across three years.

## News History

- [ ] Every full build wipes the news history. `news` is in `SINGLE_SOURCES`, so
  `clear_all()` drops it, and the reload only recovers whatever the live feeds
  currently expose. That is fine for American Soccer Now, which republishes its
  whole archive, but ESPN only ever shows the last day. `news/models.py` carries a
  note about this ("Going to have to figure out how to save these while rebuilding
  the database"). Either accept the rolling window or stop dropping `news` and
  insert only URLs not already present; `s2/build/update.py` already has that logic.
- [ ] Decide where feed URLs belong. They are hardcoded here while their display
  names have to match `metadata/data/sources` for `make_source_getter` to link a
  `FeedItem` to an existing `Source` rather than creating a new one.

## Deferred

- Fetching feeds during the build at all. It puts a network dependency in the middle
  of an otherwise offline pipeline. Splitting the fetch into a separate scheduled job
  that appends to mongo would be better, but that only matters once the news history
  is worth preserving.
