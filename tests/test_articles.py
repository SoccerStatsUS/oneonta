import pathlib

from oneonta import articles

FIXTURES = pathlib.Path(__file__).parent / 'fixtures'
ESPN = 'https://www.espn.com/soccer/story/_/id/49883678/leading-line'
ASN = 'http://americansoccernow.com/articles/euro-notebook'


def test_espn():
    paragraphs = articles.extract(ESPN, (FIXTURES / 'espn_article.html').read_text())
    assert len(paragraphs) == 24
    assert paragraphs[0].startswith('BARCELONA, Spain -- The Spotify Camp Nou pitch')
    assert paragraphs[-1].startswith('"I\'m not talking about the Ballon d\'Or,"')


def test_asn():
    paragraphs = articles.extract(ASN, (FIXTURES / 'asn_article.html').read_text())
    assert len(paragraphs) == 45
    assert paragraphs[0].startswith('WE HOPE EVERYONE had a nice long Labor Day weekend')
    assert paragraphs[-1].startswith('Meanwhile in the 2.Bundesliga')


def test_guardian():
    url = 'https://www.theguardian.com/football/2026/sep/08/mls-transfer-window-spending'
    paragraphs = articles.extract(url, (FIXTURES / 'guardian_article.html').read_text())
    assert len(paragraphs) == 17
    assert paragraphs[0].startswith('With the shadow of the 2026 World Cup')
    assert paragraphs[-1].startswith('It’s perhaps remarkable')


def test_class_matches_one_of_several():
    html = '<div class="wrap article-body x"><p>one</p></div>'
    assert articles.extract(ESPN, html) == ['one']
    assert articles.extract(ESPN, '<div class="article-body-other"><p>no</p></div>') == []


def test_paragraphs_of_a_fragment():
    assert articles.paragraphs('<p>a</p><div><p>b &amp; c</p></div><p></p>') == ['a', 'b & c']


def test_soccer_america_has_no_extractor():
    assert articles.body_for('https://www.socceramerica.com/story/') is None


def test_only_the_article_element():
    html = '<p>nav</p><div class="article-body"><p>one</p><div><p>two</p></div></div><p>footer</p>'
    assert articles.extract(ESPN, html) == ['one', 'two']


def test_unknown_site():
    assert articles.extract('https://example.com/story', '<p>hello</p>') == []
