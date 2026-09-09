# ROADMAP.md — Development Roadmap

Open work only; completed items are removed as they land (see git history).

This package feeds `load_news()` in the build repo (`build/make/load.py`), which
loads `archive.load_items()` into `soccer_db.news`; s2 then builds `news.FeedItem`
from that collection.

---

## Feed List

- [ ] Find more US-soccer coverage. The list is ESPN soccer plus American Soccer Now;
  the MLS network and the federations no longer publish RSS. Candidates need checking
  the way AGENTS.md describes — the NYT soccer feed, for instance, still parses but
  holds twenty items spread across three years.

## Archive

- [ ] Run `python -m oneonta.fetch` on a schedule and commit `data/` after each run.
  Until then the archive only grows when someone runs it by hand, and ESPN's feed
  only exposes about a day of items.
- [ ] The article text is archived but nothing reads it yet. Decide what the site
  does with it: show it on the news detail page, index it for search, or keep it as
  a record only.
- [ ] Decide where feed URLs belong. They are hardcoded here while their display
  names have to match `metadata/data/sources` for `make_source_getter` to link a
  `FeedItem` to an existing `Source` rather than creating a new one.
