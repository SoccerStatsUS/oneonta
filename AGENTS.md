# AGENTS.md

Read [README.md](README.md) first for what this package does and where it sits in the
pipeline; [ROADMAP.md](ROADMAP.md) has the open work.

This is a small repo: `feeds.py` reads the feeds, `articles.py` finds the story on a
page, `archive.py` is the store under `data/`, and `fetch.py` is the command that
runs them. It is a sibling of `build`, `s2`, `metadata` and `parse` under `~/soccer/`,
and is imported as `oneonta.<module>` with `~/soccer` on the path. There is no venv
here; use the build's:

    cd ~/soccer
    build/.venv/bin/python -m oneonta.fetch

## Changing the feed list

- Verify a url before adding it. A live feed and a 200 are not the same thing: dead
  feeds have answered their old path with the site's HTML, with valid RSS holding no
  items, and with twenty items spread across three years. Check the content type,
  then check that the newest item is recent and that there are enough of them.
- Keep the display name matched to an entry in `metadata/data/sources`. An unmatched
  name doesn't fail, it quietly creates a second `Source` in s2.
- Nothing in `feeds.py` may raise on a dead host, a timeout or a malformed document.
  Warn and carry on, so a fetch run with one feed down still archives the other.
- A new site needs an entry in `articles.BODIES` and a saved page in `tests/fixtures`,
  unless its feed carries the article text (`content`), in which case the archive takes
  it from there. A site with neither is never fetched and keeps the feed summary only.

## Output contract

`archive.load_items()` returns dicts consumed directly as `FeedItem(**row)` fields, so
the keys are fixed: `title`, `summary`, `url`, `dt`, `source`. Changing them means
changing `s2/build/load.py` and `s2/build/update.py` with it. Feed rows may also
carry `text`, a list of paragraphs, which the archive files away and drops from the
index; the database keeps the summary only.

The build never touches the network. Only `fetch.py` does, and `data/` is committed,
so a build on a fresh clone has the whole history.

- s2 runs `USE_TZ = False`, so `dt` must be a naive *local* datetime. feedparser's
  `published_parsed` is UTC; convert with `calendar.timegm`, not `time.mktime`.
- Truncate `title`, `summary` and `url` to 1023 characters.
- Summaries arrive as HTML. Strip it — don't cut at the first `<`, which returns an
  empty string for any summary that opens with a tag.

## Be gentle

`fetch.py` follows the sibling `scrapers` repo's request policy: five seconds between
page requests, retries only on transient failures, and never a second request for a
page already archived. Keep it that way. Don't poll in a loop while testing — save a
response to a file and work against that. `tests/fixtures` has one per feed and one
article page per site.
