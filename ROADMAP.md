# ROADMAP.md — Development Roadmap

Open work only; completed items are removed as they land (see git history).

This package feeds `load_news()` in the build repo (`build/make/load.py`), which
loads `archive.load_items()` into `soccer_db.news`; s2 then builds `news.FeedItem`
from that collection.

---

## Feed List

- [ ] The federations no longer publish RSS, so nothing here speaks for U.S. Soccer
  directly (mlssoccer.com is in through its JSON content index). Candidates need
  checking the way AGENTS.md describes — checked and rejected on 2026-09-09: the NYT
  soccer feed (twenty items across three years), US Soccer Players (quiet since July),
  Pro Soccer Wire, Sports Illustrated, NBC and the Guardian's USA tag (all answer
  with HTML). Checked 2026-09-10: ussoccer.com is a Next.js site with no feed and
  no data endpoint in the page, stories listed twelve at a time on `/stories`;
  mlsnextpro.com is the same Deltatre index as MLS and would work with one line in
  `feeds.INDEXES` and one in `articles.STORY_APIS`, but is twenty match previews
  and recaps every two days, so it wants a tag filter first.
- [ ] `--backfill MLSSoccer.com` would walk the content index back past 2016, some
  fifty thousand stories: about five hundred index pages, then days of page fetches
  at five seconds each. Decide whether the history is wanted before running it.
  `--backfill NWSLsoccer.com` is the same walk on a much smaller index, unchecked
  how far back it goes.
- [ ] USL League One and the USL Super League are probably the same SportsEngine
  setup as the Championship (a tagged `news_rss_feed`); unchecked.
- [ ] Soccer America's article pages are paywalled, so its items carry the feed
  summary only. Revisit if a subscription or a full-text feed turns up.

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
