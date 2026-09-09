"""
Article bodies: which element on each site holds the story, and the
paragraphs inside it.
"""
import urllib.parse
from html.parser import HTMLParser

# host -> (tag, attribute, value) of the element that wraps the article text.
# A class value matches one class among several.
BODIES = {
    'www.espn.com': ('div', 'class', 'article-body'),
    'americansoccernow.com': ('div', 'id', 'article'),
    'www.theguardian.com': ('div', 'data-gu-name', 'body'),
    # Soccer America's pages are paywalled to a teaser paragraph; feed only.
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


def body_for(url):
    return BODIES.get(urllib.parse.urlsplit(url).hostname)


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


def extract(url, html):
    """The article's paragraphs, or [] if the site is unknown or the page has none."""
    root = body_for(url)
    if not root:
        return []
    return paragraphs(html, root)
