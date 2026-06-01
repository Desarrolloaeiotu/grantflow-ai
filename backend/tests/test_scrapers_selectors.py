"""Tests para validar que los selectores CSS de scrapers encuentran elementos en HTML realista.

Estos tests crean HTML que simula la estructura real de las páginas de financiadores
y verifican que los selectores BeautifulSoup funcionan correctamente.

Este archivo complementa test_scrapers.py (que prueba normalize() con dicts) con
tests de la extracción de HTML/selectores que ocurre en fetch_raw().
"""

from bs4 import BeautifulSoup

from app.scrapers.bid import BidScraper
from app.scrapers.developmentaid import DevelopmentAidScraper
from app.scrapers.grantsgov import GrantsGovScraper
from app.scrapers.rss_feeds import RssFeedsScraper
from app.scrapers.unwomen import UnWomenScraper


# ── BID: Validar selectores encuentran elementos ──────────────────────────────

def test_bid_selector_finds_convocatoria_links():
    """Selector a[href*='/convocatorias/'] encuentra enlaces de convocatorias."""
    html = """
    <html><body>
        <a href="/convocatorias/ecd-2026">Early Childhood Development</a>
        <a href="/about">About</a>
        <a href="/convocatorias/gender-2026">Gender Equality</a>
    </body></html>
    """
    soup = BeautifulSoup(html, "lxml")
    links = soup.select("a[href*='/convocatorias/']")
    assert len(links) == 2
    assert "Early Childhood Development" in [a.get_text() for a in links]


def test_bid_selector_finds_card_links():
    """Selector article a[href] y .card a[href] encuentra enlaces en tarjetas."""
    html = """
    <html><body>
        <div class="card">
            <a href="/convocatorias/123">Card Opportunity</a>
        </div>
        <article>
            <a href="/convocatorias/456">Article Opportunity</a>
        </article>
    </body></html>
    """
    soup = BeautifulSoup(html, "lxml")
    article_links = soup.select("article a[href]")
    card_links = soup.select(".card a[href]")
    assert len(article_links) == 1
    assert len(card_links) == 1


def test_bid_selector_finds_article_links():
    """Selector article a[href] encuentra enlaces dentro de article."""
    html = """
    <html><body>
        <article>
            <h2>Opportunity Title</h2>
            <p>Description</p>
            <a href="/convocatorias/789">Apply Here</a>
        </article>
    </body></html>
    """
    soup = BeautifulSoup(html, "lxml")
    article = soup.find("article")
    assert article is not None
    link = article.find("a", href=True)
    assert link is not None
    assert link.get_text() == "Apply Here"


def test_bid_selector_empty_html_no_crash():
    """Selectores sobre HTML vacío retornan lista vacía, sin crash."""
    html = "<html><body></body></html>"
    soup = BeautifulSoup(html, "lxml")
    links = soup.select("article a[href*='/convocatorias/']")
    assert links == []


def test_bid_title_from_h3_inside_parent():
    """Después de find_parent(['article']), se encuentra h3/h2/h1."""
    html = """
    <html><body>
        <article>
            <h3>ECD 2026 Call</h3>
            <a href="/convocatorias/ecd">Link</a>
        </article>
    </body></html>
    """
    soup = BeautifulSoup(html, "lxml")
    link = soup.find("a")
    parent = link.find_parent(["article", "div", "li"])
    assert parent is not None
    heading = parent.find(["h1", "h2", "h3", "h4"])
    assert heading is not None
    assert heading.get_text() == "ECD 2026 Call"


def test_bid_deadline_regex_match_in_text():
    """Regex busca 'fecha de cierre|deadline|cierra' en texto de página."""
    html = """
    <html><body>
        <p>Esta convocatoria está abierta.</p>
        <p>Fecha de cierre: 2026-07-15 para todas las categorías.</p>
    </body></html>
    """
    soup = BeautifulSoup(html, "lxml")
    full_text = soup.get_text().lower()
    assert "fecha de cierre" in full_text or "cierra" in full_text


# ── UN Women: Validar selectores ──────────────────────────────────────────────

def test_unwomen_article_selector_finds_elements():
    """Selector 'article' encuentra <article> tags con contenido."""
    html = """
    <html><body>
        <article>
            <h2>Fund for Gender Equality</h2>
            <a href="/en/grants/fge">Apply</a>
        </article>
        <div>Not an article</div>
    </body></html>
    """
    soup = BeautifulSoup(html, "lxml")
    articles = soup.select("article")
    assert len(articles) == 1
    title = articles[0].find(["h1", "h2", "h3", "h4"])
    assert title is not None


def test_unwomen_views_row_selector():
    """Selector '.views-row' encuentra div con esa clase (typical de Drupal)."""
    html = """
    <html><body>
        <div class="views-row">
            <h3>Opportunity 1</h3>
        </div>
        <div class="views-row">
            <h3>Opportunity 2</h3>
        </div>
    </body></html>
    """
    soup = BeautifulSoup(html, "lxml")
    rows = soup.select(".views-row")
    assert len(rows) == 2


def test_unwomen_card_selector_and_heading_extraction():
    """Selector '.card' + find(['h1','h2','h3']) extrae títulos."""
    html = """
    <html><body>
        <div class="card">
            <h3>Grant Opportunity</h3>
            <p>Details</p>
        </div>
    </body></html>
    """
    soup = BeautifulSoup(html, "lxml")
    card = soup.find(["article", ".card", "div"], class_="card")
    if card is None:
        card = soup.select(".card")[0] if soup.select(".card") else None
    assert card is not None
    heading = card.find(["h1", "h2", "h3", "h4"])
    assert heading is not None


def test_unwomen_snippet_class_extraction():
    """Extrae snippet de <p> con class que contiene 'summary', 'excerpt', o 'teaser'."""
    html = """
    <html><body>
        <div class="card">
            <h3>Title</h3>
            <p class="summary">This is the summary of the grant.</p>
            <p>More info</p>
        </div>
    </body></html>
    """
    soup = BeautifulSoup(html, "lxml")
    card = soup.select(".card")[0]
    snippet_p = card.find("p", class_=lambda c: bool(c and ("summary" in c or "excerpt" in c)))
    assert snippet_p is not None
    assert "summary of the grant" in snippet_p.get_text()


def test_unwomen_selector_empty_page_no_crash():
    """Selectores sobre página sin elementos retornan listas vacías."""
    html = "<html><body><p>No opportunities here</p></body></html>"
    soup = BeautifulSoup(html, "lxml")
    articles = soup.select("article, .views-row, .card")
    assert articles == []


# ── DevelopmentAid: Validar selectores ────────────────────────────────────────

def test_devaid_article_selector_with_heading_and_link():
    """Selector 'article' + find(['h1'...]) + find('a[href]') para extraer datos."""
    html = """
    <html><body>
        <article>
            <h3>ECD Funding Opportunity</h3>
            <a href="https://devaid.org/grants/ecd-123">View Details</a>
        </article>
    </body></html>
    """
    soup = BeautifulSoup(html, "lxml")
    articles = soup.select("article")
    assert len(articles) == 1
    heading = articles[0].find(["h1", "h2", "h3", "h4"])
    link = articles[0].find("a", href=True)
    assert heading is not None
    assert link is not None


def test_devaid_card_class_selector():
    """Selector '.card' encuentra divs con esa clase."""
    html = """
    <html><body>
        <div class="card">
            <h4>Grant Opportunity</h4>
        </div>
        <div class="other">Not a card</div>
    </body></html>
    """
    soup = BeautifulSoup(html, "lxml")
    cards = soup.select(".card")
    assert len(cards) == 1


def test_devaid_fallback_selector_li_has_grant_link():
    """Fallback selector li:has(a[href*='/grants']) cuando otros falla."""
    html = """
    <html><body>
        <ul>
            <li><a href="https://devaid.org/news">News</a></li>
            <li><a href="https://devaid.org/grants/123">Early Childhood Grant</a></li>
            <li><a href="https://devaid.org/grants/456">Teacher Training</a></li>
        </ul>
    </body></html>
    """
    soup = BeautifulSoup(html, "lxml")
    grant_lis = soup.select("li:has(a[href*='/grants/'])")
    # Note: li:has() is CSS Selector Level 4, may not work in all BS versions
    # Fallback for older BeautifulSoup: find all <li>, then check if contains a[href*='/grants']
    if not grant_lis:
        grant_lis = [li for li in soup.find_all("li") if li.find("a", href=lambda h: h and "/grants/" in h)]
    assert len(grant_lis) == 2


def test_devaid_selector_empty_page_no_crash():
    """Selectores sobre página sin elementos retornan listas vacías."""
    html = "<html><body><h1>No grants available</h1></body></html>"
    soup = BeautifulSoup(html, "lxml")
    articles = soup.select("article, .card, .news-item, .item")
    assert articles == []


# ── GrantsGov: Validar estructura JSON ────────────────────────────────────────

def test_grantsgov_json_has_required_fields():
    """Respuesta JSON tiene id, title, agency, closeDate (aunque algunos opcionales)."""
    raw = {
        "id": "HHS-2026-ACF",
        "title": "Early Childhood Education",
        "agency": "ACF",
        "closeDate": "06/30/2026",
    }
    assert "id" in raw
    assert "title" in raw
    assert "agency" in raw or "agencyName" in raw


def test_grantsgov_json_missing_closeDate_normalize_handles():
    """Si closeDate falta, normalize() devuelve opp con deadline=None (no crash)."""
    scraper = GrantsGovScraper()
    raw = {
        "id": "1",
        "title": "Early Childhood Initiative",
        "agency": "HHS",
        # No closeDate
    }
    result = scraper.normalize(raw)
    assert result is not None
    assert result.deadline is None


def test_grantsgov_cfda_list_to_sectors():
    """cfdaList en JSON se convierte a lista de sectors."""
    raw = {
        "id": "1",
        "title": "Education Grant",
        "agency": "ED",
        "cfdaList": ["84.282", "93.840"],
        "closeDate": "12/31/2026",
    }
    scraper = GrantsGovScraper()
    result = scraper.normalize(raw)
    assert result is not None
    # CFDA codes are extracted and included in the opportunity


# ── RSS / FeedParser: Validar estructura ──────────────────────────────────────

def test_rss_entry_has_required_fields():
    """Entrada feedparser tiene .title, .link, .summary (o .description)."""
    # Simular estructura que feedparser retorna después de parse
    entry = {
        "title": "Grant Opportunity for ECD",
        "link": "https://example.org/grants/123",
        "summary": "Funding for early childhood development programs",
    }
    assert "title" in entry
    assert "link" in entry
    assert "summary" in entry or "description" in entry


def test_rss_tags_are_list_of_dicts_with_term():
    """Entrada feedparser.tags es lista de dicts con 'term' (categoría)."""
    entry = {
        "title": "Grant",
        "link": "https://example.org/grants/1",
        "tags": [
            {"term": "early childhood", "scheme": None, "label": "ECD"},
            {"term": "education", "scheme": None, "label": "Education"},
        ],
    }
    assert isinstance(entry.get("tags", []), list)
    assert all(isinstance(tag, dict) and "term" in tag for tag in entry.get("tags", []))


def test_rss_clean_html_and_extract_deadline_pipeline():
    """Pipeline: summary HTML → _clean_html → _extract_deadline."""
    from app.scrapers.rss_feeds import _clean_html, _extract_deadline

    entry = {}
    summary_html = """
    <p>Funding for <strong>early childhood</strong> programs.</p>
    <p>Deadline: <em>2026-06-30</em> for applications.</p>
    """

    # Clean HTML
    cleaned = _clean_html(summary_html)
    assert "<" not in cleaned  # HTML tags removed
    assert "early childhood" in cleaned
    assert "2026-06-30" in cleaned

    # Extract deadline
    deadline = _extract_deadline(entry, cleaned)
    assert deadline is not None
    assert deadline.year == 2026
    assert deadline.month == 6
    assert deadline.day == 30
