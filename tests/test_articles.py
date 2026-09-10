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


def test_usl():
    url = 'https://www.uslchampionship.com/news_article/show/1366482'
    paragraphs = articles.extract(url, (FIXTURES / 'usl_article.html').read_text())
    assert len(paragraphs) == 60
    assert paragraphs[0].startswith('Hartford Athletic advanced to its second consecutive')
    assert paragraphs[-1].startswith('FC Tulsa (1): Jamie Webber')


def test_story_api_records():
    # the Deltatre sites: the story is fetched as JSON, its body is markdown parts
    mls = 'https://www.mlssoccer.com/news/brotherly-love-cavan-sullivan-steals-show-in-philadelphia-rout'
    assert articles.fetch_url(mls) == \
        'https://dapi.mlssoccer.com/v2/content/en-us/stories/brotherly-love-cavan-sullivan-steals-show-in-philadelphia-rout'
    paragraphs = articles.extract(mls, (FIXTURES / 'mlssoccer_story.json').read_text())
    assert len(paragraphs) == 17
    assert paragraphs[0] == 'Another Philadelphia Union victory, another record-setting night for Cavan Sullivan.'
    assert paragraphs[-1].startswith('The Union now take their show on the road')
    # links are reduced to their text; the embedded tweets and photos are left out
    assert not any('](' in p or 'pic.twitter' in p for p in paragraphs)

    nwsl = 'https://www.nwslsoccer.com/news/matchweek-21'
    assert articles.fetch_url(nwsl) == 'https://dapi.nwslsoccer.com/v2/content/en-us/stories/matchweek-21'
    paragraphs = articles.extract(nwsl, (FIXTURES / 'nwsl_story.json').read_text())
    assert len(paragraphs) == 22
    assert paragraphs[0].startswith('Upsets! Last-minute game-winners!')
    # a list of fixtures, one paragraph each; the SCHEDULE heading is dropped
    assert paragraphs[2].startswith('Racing Louisville vs. Gotham FC')
    assert not any('SCHEDULE' in p for p in paragraphs)
    assert paragraphs[-1] == 'Tune in to find out.'

    assert articles.fetch_url(ESPN) == ESPN
    assert articles.has_extractor(nwsl) and articles.has_extractor(ESPN)
    assert not articles.has_extractor('https://www.socceramerica.com/story/')


def test_markdown_paragraphs():
    md = '### **Head**\n\nA [link](/x) and **bold** and _it_.\n\n* one\n* two\n\n> quote\n![pic](/p.jpg)\n\n'
    assert articles.markdown_paragraphs(md) == ['A link and bold and it.', 'one', 'two', 'quote']
    assert articles.markdown_paragraphs('') == []


def test_class_matches_one_of_several():
    html = '<div class="wrap article-body x"><p>one</p></div>'
    assert articles.extract(ESPN, html) == ['one']
    assert articles.extract(ESPN, '<div class="article-body-other"><p>no</p></div>') == []


def test_paragraphs_of_a_fragment():
    assert articles.paragraphs('<p>a</p><div><p>b &amp; c</p></div><p></p>') == ['a', 'b & c']


def test_paragraphs_fall_back_to_line_breaks():
    html = 'one<br /> <br />two <a href="x">link</a>.<br /><ul><li>three</li></ul><div class="f"><!-- ad --></div>'
    assert articles.paragraphs(html) == ['one', 'two link.', 'three']
    # a page extractor never falls back: no <p> in the body means no article
    assert articles.paragraphs('<div id="a">one<br>two</div>', ('div', 'id', 'a')) == []


def test_soccer_america_has_no_extractor():
    assert not articles.has_extractor('https://www.socceramerica.com/story/')


def test_only_the_article_element():
    html = '<p>nav</p><div class="article-body"><p>one</p><div><p>two</p></div></div><p>footer</p>'
    assert articles.extract(ESPN, html) == ['one', 'two']


def test_unknown_site():
    assert articles.extract('https://example.com/story', '<p>hello</p>') == []
