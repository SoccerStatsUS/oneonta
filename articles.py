"""
Article bodies: which element on each site holds the story, and the
paragraphs inside it.
"""
import json
import re
import urllib.parse
from html.parser import HTMLParser

# host -> (tag, attribute, value) of the element that wraps the article text.
# A class value matches one class among several.
BODIES = {
    'www.espn.com': ('div', 'class', 'article-body'),
    'americansoccernow.com': ('div', 'id', 'article'),
    'www.theguardian.com': ('div', 'data-gu-name', 'body'),
    'www.uslchampionship.com': ('div', 'class', 'newsContentNode'),
    # Soccer America's pages are paywalled to a teaser paragraph; feed only.
}

# host -> the JSON record behind a story, by slug, for the Deltatre sites: the
# body is markdown parts there, and the NWSL page is a shell with no text at all.
STORY_APIS = {
    'www.mlssoccer.com': 'https://dapi.mlssoccer.com/v2/content/en-us/stories/{}',
    'www.nwslsoccer.com': 'https://dapi.nwslsoccer.com/v2/content/en-us/stories/{}',
}


def matches(attrs, attr, value):
    found = dict(attrs).get(attr)
    if found is None:
        return False
    if attr == 'class':
        return value in found.split()
    return found == value


class _Paragraphs(HTMLParser):
    """
    Collect the text of every <p> inside the first element matching root,
    or everywhere if root is None.
    """

    def __init__(self, root):
        super().__init__()
        self.root = root
        self.depth = 0 if root else 1
        self.done = False
        self.in_p = False
        self.current = []
        self.paragraphs = []

    def handle_starttag(self, tag, attrs):
        if self.done:
            return
        if not self.depth:
            root_tag, attr, value = self.root
            if tag == root_tag and matches(attrs, attr, value):
                self.depth = 1
            return
        self.depth += 1
        if tag == 'p':
            self.in_p = True
            self.current = []

    def handle_endtag(self, tag):
        if not self.depth or self.done:
            return
        if tag == 'p' and self.in_p:
            self.in_p = False
            text = ' '.join(''.join(self.current).split())
            if text:
                self.paragraphs.append(text)
        self.depth -= 1
        if not self.depth:
            self.done = True

    def handle_data(self, data):
        if self.in_p:
            self.current.append(data)


def has_extractor(url):
    host = urllib.parse.urlsplit(url).hostname
    return host in BODIES or host in STORY_APIS


def fetch_url(url):
    """What to fetch for the story at url: its API record where there is one, else the page."""
    host = urllib.parse.urlsplit(url).hostname
    if host in STORY_APIS:
        return STORY_APIS[host].format(url.rstrip('/').rsplit('/', 1)[1])
    return url


def markdown_paragraphs(md):
    """The paragraphs of a markdown body, markup removed; headings are dropped."""
    l = []
    for block in re.split(r'\n\s*\n|\n(?=\s*(?:[-*+]|\d+\.)\s)', md):
        lines = [line for line in block.split('\n') if not line.lstrip().startswith('#')]
        t = '\n'.join(re.sub(r'^\s*(?:[-*+]|\d+\.|>)\s+', '', line) for line in lines)
        t = re.sub(r'!\[[^\]]*\]\([^)]*\)', '', t)
        t = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', t)
        t = re.sub(r'(\*\*|__)(.+?)\1', r'\2', t)
        t = re.sub(r'(?<![\w*])[*_](?=\S)(.+?)(?<=\S)[*_](?![\w*])', r'\1', t)
        t = ' '.join(t.split())
        if t:
            l.append(t)
    return l


def story_paragraphs(record):
    return [p for part in record.get('parts', []) if part.get('type') == 'markdown'
            for p in markdown_paragraphs(part.get('content') or '')]


class _Blocks(HTMLParser):
    """Text split at line breaks and block elements, for markup with no <p>."""

    BREAKS = {'br', 'div', 'li', 'ul', 'ol', 'blockquote', 'h1', 'h2', 'h3', 'h4', 'tr'}

    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in self.BREAKS:
            self.parts.append('\n')

    def handle_endtag(self, tag):
        if tag in self.BREAKS:
            self.parts.append('\n')

    def handle_data(self, data):
        self.parts.append(data)


def paragraphs(html, root=None):
    p = _Paragraphs(root)
    p.feed(html)
    p.close()
    if p.paragraphs or root:
        return p.paragraphs
    # Blogger-era markup: <br> and lists, no <p>.
    b = _Blocks()
    b.feed(html)
    b.close()
    return [t for t in (' '.join(line.split()) for line in ''.join(b.parts).split('\n')) if t]


def extract(url, doc):
    """The article's paragraphs, or [] if the site is unknown or the page has none."""
    host = urllib.parse.urlsplit(url).hostname
    if host in STORY_APIS:
        return story_paragraphs(json.loads(doc))
    root = BODIES.get(host)
    if not root:
        return []
    return paragraphs(doc, root)
