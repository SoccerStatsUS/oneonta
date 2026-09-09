"""
Update the news archive: read the feeds for new items, then fetch the page of
every archived item that has no text yet.

    cd ~/soccer
    build/.venv/bin/python -m oneonta.fetch [--limit N] [--no-feeds]

Resumable: stop it whenever, and the next run carries on from the items still
missing text. Request policy is the scrapers repo's: five seconds between
requests, one minute then five before giving up on a transient failure, and
no retry on a 4xx other than 408 and 429.
"""
import argparse
import sys
import time
import urllib.request
from urllib.error import HTTPError

from oneonta import archive, articles, feeds

REQUEST_DELAY = 5
RETRY_DELAYS = [60, 300]
RETRIABLE_4XX = {408, 429}
TIMEOUT = 30


def fetch_page(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    for delay in [*RETRY_DELAYS, None]:
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                return resp.read().decode('utf-8', 'replace')
        except OSError as e:
            if delay is None or (isinstance(e, HTTPError) and 400 <= e.code < 500
                                 and e.code not in RETRIABLE_4XX):
                raise
            print(f'fetch failed ({e}), retrying in {delay}s', file=sys.stderr)
            time.sleep(delay)


def fetch_text(item):
    """Fetch one item's page and archive its text. Returns the paragraph count."""
    try:
        html = fetch_page(item['url'])
    except HTTPError as e:
        if 400 <= e.code < 500:
            # Gone for good; record that so it is not asked for again.
            archive.write_text(item, [])
            return 0
        raise
    paragraphs = articles.extract(item['url'], html)
    if not paragraphs:
        print(f'no article found at {item["url"]}', file=sys.stderr)
    archive.write_text(item, paragraphs)
    return len(paragraphs)


def update_items():
    rows = feeds.parse_feeds()
    added = archive.add_items(rows)
    from_feed = 0
    for row in rows:
        # Only where the page is not going to be fetched: a site with an
        # extractor gets the whole article, while its feed may carry a teaser.
        if row.get('text') and not articles.body_for(row['url']) and not archive.has_text(row):
            archive.write_text(row, row['text'])
            from_feed += 1
    print(f'{added} new items from the feeds, {from_feed} texts taken from the feeds')
    return added


def fetch_missing(limit=None):
    missing = [e for e in reversed(archive.read_items()) if not archive.has_text(e)]
    items = [e for e in missing if articles.body_for(e['url'])]
    skipped = len(missing) - len(items)
    if limit is not None:
        items = items[:limit]
    print(f'{len(missing)} items without text, {skipped} on sites with no extractor, '
          f'fetching {len(items)}')

    empty = failed = 0
    for i, item in enumerate(items):
        if i:
            time.sleep(REQUEST_DELAY)
        try:
            n = fetch_text(item)
        except OSError as e:
            failed += 1
            print(f'giving up on {item["url"]}: {e}', file=sys.stderr)
            continue
        if not n:
            empty += 1
        if (i + 1) % 50 == 0:
            print(f'{i + 1}/{len(items)}', flush=True)

    print(f'fetched {len(items) - failed}, {empty} with no text, {failed} failed')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    parser.add_argument('--limit', type=int, help='fetch at most this many pages')
    parser.add_argument('--no-feeds', action='store_true',
                        help='skip the feeds; only fetch text for archived items')
    args = parser.parse_args(argv)

    if not args.no_feeds:
        update_items()
    fetch_missing(args.limit)


if __name__ == '__main__':
    main()
