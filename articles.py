"""
Article bodies: which element on each site holds the story, and the
paragraphs inside it.
"""
import urllib.parse
from html.parser import HTMLParser

# host -> (tag, attribute, value) of the element that wraps the article text.
BODIES = {
    'www.espn.com': ('div', 'class', 'article-body'),
    'americansoccernow.com': ('div', 'id', 'article'),
}


class _Paragraphs(HTMLParser):
    """Collect the text of every <p> inside the first element matching root."""

    def __init__(self, root):
        super().__init__()
        self.root = root
        self.depth = 0
        self.done = False
        self.in_p = False
        self.current = []
        self.paragraphs = []

    def handle_starttag(self, tag, attrs):
        if self.done:
            return
        if not self.depth:
            root_tag, attr, value = self.root
            if tag == root_tag and dict(attrs).get(attr) == value:
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


def extract(url, html):
    """The article's paragraphs, or [] if the site is unknown or the page has none."""
    root = body_for(url)
    if not root:
        return []
    p = _Paragraphs(root)
    p.feed(html)
    p.close()
    return p.paragraphs
