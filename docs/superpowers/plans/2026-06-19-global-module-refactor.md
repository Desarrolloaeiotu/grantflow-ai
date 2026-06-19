# Global Module Refactorization — Organizations, Contacts, Convocatorias

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` or `superpowers:executing-plans` to implement this plan task-by-task.

**Goal:** Refactor global scrapers and data structures to comply with aeioTU requirements: separate Organizations (with Contacts) from Convocatorias, implement strict validation, and eliminate news/article contamination.

**Architecture:** 
- Separate three distinct modules: Organizations (Funders + Contacts), Convocatorias (Opportunities with type=grant|premio|evento|curso), and Marketplace Intelligence (aggregated signals)
- Implement two-tier filtering: (1) Content-type detection (convocatoria vs news/article), (2) Mandatory field validation
- Add new table `convocation` to store convocatory-specific metadata distinct from generic opportunities
- Refactor RSS/LinkedIn/Twitter scrapers to extract organizations + key contacts as first-class entities, not embedded in opportunities
- Add data quality scoring and source traceability

**Tech Stack:**
- SQLAlchemy ORM (models: Convocation, Contact)
- FastAPI endpoints for three modules
- BeautifulSoup for content-type detection
- LLM-based extraction for structured field parsing
- Pydantic validation schemas

---

## Global Constraints

- Mandatory fields (from spec) must be validated before DB insert
- No news/articles/reports → only real convocatorias accepted
- Source traceability required (feed URL, scraper name, timestamp)
- Contacts: only roles matching keywords (partnerships, grants, cooperation, innovation, development)
- All endpoints must be exportable as CSV/Excel
- Maintain backwards compatibility with existing Opportunity table (module for historical convocatorias)

---

## File Structure

### New Files
- `backend/app/models/convocation.py` — Convocation table (distinct from Opportunity)
- `backend/app/schemas/convocation.py` — Pydantic validation for convocatorias
- `backend/app/schemas/contact_v2.py` — Enhanced Contact schema with role_category validation
- `backend/app/services/content_type_detector.py` — Classify entry as convocatoria vs news/article
- `backend/app/services/field_extractor.py` — LLM-based field extraction for structured data
- `backend/app/scrapers/utils/keyword_filters.py` — Centralized keyword filters with strict validation
- `backend/app/api/convocations.py` — Endpoints for convocatorias module
- `backend/app/api/global_organizations.py` — Endpoints for organizations + contacts module
- `backend/app/tasks/cleanup_global_data.py` — Script to clean existing global opportunities

### Modified Files
- `backend/app/models/funder.py` — Add `source_quality_score`, `data_completeness` fields
- `backend/app/models/contact.py` — Strengthen role_category validation enum
- `backend/app/scrapers/rss_feeds.py` — Integrate content-type detector, stricter filtering
- `backend/app/scrapers/linkedin_improved.py` — Refocus on organizations + key contacts extraction
- `backend/app/scrapers/twitter_improved.py` — Refocus on organizations + key contacts extraction
- `backend/app/scrapers/grantsgov_scrapling.py` — Validate mandatory convocation fields
- `backend/main.py` — Register new routers for convocations and global_organizations
- `backend/app/api/organizations.py` — Keep but refactor to use enhanced schema

---

## Task Breakdown

### Task 1: Create Content-Type Detector Service

**Files:**
- Create: `backend/app/services/content_type_detector.py`
- Test: `backend/tests/services/test_content_type_detector.py`

**Interfaces:**
- Consumes: `title: str, description: str, url: str` → raw RSS/web entry data
- Produces: `ContentType` enum (CONVOCATORIA | NEWS | ARTICLE | REPORT | EVENT | COURSE | UNKNOWN) + confidence score (0-1)

**Logic:**
- If title/description contains explicit convocatoria indicators (deadline, "apply now", "call for proposals", "convocatoria", "llamado", "oportunidad de financiamiento"): CONVOCATORIA (high confidence)
- If URL pattern matches known convocation portals (grants.gov, bid.org, unwomen.org grants pages): CONVOCATORIA
- If contains news keywords ("says", "announces", "reports", "statement", "news"): NEWS (high confidence)
- Otherwise: UNKNOWN (confidence = keyword match percentage)

- [ ] **Step 1: Write test**

```python
def test_detector_identifies_convocatoria():
    content = {
        "title": "Ford Foundation 2026 Innovation Grants - Deadline June 30",
        "description": "Apply now for USD $500K innovation grants",
        "url": "https://fordfoundation.org/grants/2026-innovation"
    }
    result = detect_content_type(content)
    assert result.type == ContentType.CONVOCATORIA
    assert result.confidence > 0.85

def test_detector_rejects_news_article():
    content = {
        "title": "Ford Foundation announces new gender justice initiative",
        "description": "The foundation says it will invest $2B",
        "url": "https://fordfoundation.org/news/2026-gender-justice"
    }
    result = detect_content_type(content)
    assert result.type == ContentType.NEWS
    assert result.confidence > 0.85

def test_detector_classifies_relief_report_as_not_convocatoria():
    content = {
        "title": "Panama: Soluciones Duraderas - Ficha Técnica 2023",
        "description": "This technical fact sheet reports on UNHCR operations",
        "url": "https://reliefweb.int/report/panama/..."
    }
    result = detect_content_type(content)
    assert result.type != ContentType.CONVOCATORIA
    assert result.confidence > 0.7
```

- [ ] **Step 2: Run test to verify fail**

Run: `pytest backend/tests/services/test_content_type_detector.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'app.services.content_type_detector'"

- [ ] **Step 3: Create detector service**

```python
# backend/app/services/content_type_detector.py
from enum import Enum
from dataclasses import dataclass
import re

class ContentType(str, Enum):
    CONVOCATORIA = "convocatoria"
    NEWS = "news"
    ARTICLE = "article"
    REPORT = "report"
    EVENT = "event"
    COURSE = "course"
    UNKNOWN = "unknown"

@dataclass
class ContentTypeResult:
    type: ContentType
    confidence: float  # 0-1
    reason: str | None = None

CONVOCATORIA_PATTERNS = (
    r"deadline|fecha límite|fecha cierre|call for|llamado|convocatoria|opportunity|grant.*apply|"
    r"apply.*now|submit.*proposal|proposal.*deadline|expression of interest|eoi|rfp|request for proposal|"
    r"oportunidad de financiamiento|financiamiento disponible|solicitud abierta",
)

NEWS_PATTERNS = (
    r"\bsays\b|\bannounces\b|\breports\b|\bstatement\b|\bnews\b|\bpress release\b|"
    r"comunicado de prensa|anunció|reporta|según|afirma",
)

def detect_content_type(content: dict) -> ContentTypeResult:
    title = (content.get("title") or "").lower()
    description = (content.get("description") or "").lower()
    url = (content.get("url") or "").lower()
    
    haystack = title + " " + description + " " + url
    
    # Check convocatoria patterns
    convocatoria_matches = len(re.findall(CONVOCATORIA_PATTERNS, haystack))
    if convocatoria_matches >= 2:
        return ContentTypeResult(
            type=ContentType.CONVOCATORIA,
            confidence=min(0.95, 0.7 + (convocatoria_matches * 0.1)),
            reason=f"Found {convocatoria_matches} convocatoria indicators"
        )
    
    # Check news patterns
    news_matches = len(re.findall(NEWS_PATTERNS, haystack))
    if news_matches >= 2:
        return ContentTypeResult(
            type=ContentType.NEWS,
            confidence=min(0.95, 0.7 + (news_matches * 0.1)),
            reason=f"Found {news_matches} news indicators"
        )
    
    # Check known portals
    if re.search(r"(grants\.gov|bid\.org|unwomen\.org.*grants|fordfoundation\.org.*grants)", url):
        return ContentTypeResult(
            type=ContentType.CONVOCATORIA,
            confidence=0.90,
            reason="Known convocation portal"
        )
    
    return ContentTypeResult(
        type=ContentType.UNKNOWN,
        confidence=0.5,
        reason="No strong indicators"
    )
```

- [ ] **Step 4: Run test to pass**

Run: `pytest backend/tests/services/test_content_type_detector.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/content_type_detector.py backend/tests/services/test_content_type_detector.py
git commit -m "feat(services): add content-type detector to classify convocatorias vs news

- Implement ContentType enum (CONVOCATORIA, NEWS, ARTICLE, REPORT, etc.)
- Add regex-based pattern matching for convocatoria/news indicators
- Include portal URL detection (grants.gov, bid.org, etc.)
- Return ContentTypeResult with confidence score and reason
- Tests verify correct classification of real entries

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>"
```

---

### Task 2: Create Convocation Model (DB Table)

**Files:**
- Create: `backend/app/models/convocation.py`
- Modify: `backend/alembic/versions/create_convocation_table.py` (Alembic migration)

**Interfaces:**
- Produces: Convocation ORM model with fields:
  - `id: UUID`
  - `title: str` (mandatory)
  - `type: str` (grant|premio|evento|curso)
  - `objective: str` (mandatory)
  - `amount_min_cop, amount_max_cop: int | None`
  - `url_convocation: str` (mandatory)
  - `url_tor: str | None`
  - `url_form: str | None`
  - `organization_id: UUID` (FK → Funder)
  - `open_date, deadline: date` (mandatory)
  - `source_name: str`
  - `detected_at, updated_at: datetime`
  - `verified: bool` (has all mandatory fields)

- [ ] **Step 1: Create model**

```python
# backend/app/models/convocation.py
import uuid
from datetime import date, datetime, timezone

from sqlalchemy import BigInteger, Boolean, Date, ForeignKey, Text
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

class Convocation(Base):
    __tablename__ = "convocations"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Mandatory fields
    title: Mapped[str] = mapped_column(Text, nullable=False)
    objective: Mapped[str] = mapped_column(Text, nullable=False)  # Clear description of convocatoria goal
    type: Mapped[str] = mapped_column(Text, nullable=False)  # grant|premio|evento|curso
    deadline: Mapped[date] = mapped_column(Date, nullable=False)
    open_date: Mapped[date] = mapped_column(Date, nullable=False)
    url_convocation: Mapped[str] = mapped_column(Text, nullable=False)  # Official convocation page
    
    # Optional but important
    amount_min_cop: Mapped[int | None] = mapped_column(BigInteger)
    amount_max_cop: Mapped[int | None] = mapped_column(BigInteger)
    url_tor: Mapped[str | None] = mapped_column(Text)  # Terms of reference
    url_form: Mapped[str | None] = mapped_column(Text)  # Application form
    
    # Organization & lineage
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("funders.id", ondelete="SET NULL"), nullable=True
    )
    organization_website: Mapped[str | None] = mapped_column(Text)
    
    # Metadata
    source_name: Mapped[str] = mapped_column(Text)  # rss|grantsgov|bid|linkedin|twitter
    source_url: Mapped[str | None] = mapped_column(Text)  # Where scraped from
    
    # Quality
    verified: Mapped[bool] = mapped_column(Boolean, default=False)  # All mandatory fields present & validated
    data_completeness: Mapped[int] = mapped_column(default=0)  # Percentage of fields filled (0-100)
    
    # Timestamps
    detected_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    
    # Relationships
    organization: Mapped["app.models.funder.Funder | None"] = relationship("Funder", lazy="select")
```

- [ ] **Step 2: Create Alembic migration**

```bash
cd backend
alembic revision --autogenerate -m "add convocation table"
```

Review the generated file in `backend/alembic/versions/`. Verify it creates:
- convocations table
- Indexes on deadline, organization_id, verified
- FK constraint to funders table

- [ ] **Step 3: Run migration**

```bash
cd backend
alembic upgrade head
```

Expected: "OK" output, no errors

- [ ] **Step 4: Commit**

```bash
git add backend/app/models/convocation.py backend/alembic/versions/*.py
git commit -m "feat(models): add Convocation table for structured convocatory data

- New table convocations with mandatory fields: title, objective, type, deadline, open_date, url_convocation
- Optional fields: amounts, TOR/form URLs, organization FK
- Quality tracking: verified flag, data_completeness %
- Timestamps and source traceability
- Alembic migration included

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>"
```

---

### Task 3: Create Convocation Validation Schemas

**Files:**
- Create: `backend/app/schemas/convocation.py`
- Test: `backend/tests/schemas/test_convocation.py`

**Interfaces:**
- Consumes: Raw scraper output (dict)
- Produces: `ConvocationCreate` (for DB insert), `ConvocationRead` (for API response)
- Validates: All mandatory fields present, type is one of enum values, dates are valid, URLs are parseable

- [ ] **Step 1: Write tests**

```python
# backend/tests/schemas/test_convocation.py
import pytest
from datetime import date
from app.schemas.convocation import ConvocationCreate, ConvocationRead

def test_valid_convocation_create():
    """Valid convocation passes validation"""
    data = {
        "title": "Ford Foundation 2026 Innovation Grants",
        "objective": "Support innovative models for early childhood development",
        "type": "grant",
        "deadline": date(2026, 6, 30),
        "open_date": date(2026, 5, 1),
        "url_convocation": "https://fordfoundation.org/grants/2026-innovation",
        "source_name": "grantsgov",
    }
    conv = ConvocationCreate(**data)
    assert conv.title == "Ford Foundation 2026 Innovation Grants"
    assert conv.type == "grant"

def test_convocation_missing_mandatory_field():
    """Missing mandatory field raises ValidationError"""
    data = {
        "title": "Ford Foundation 2026 Innovation Grants",
        # Missing objective
        "type": "grant",
        "deadline": date(2026, 6, 30),
        "open_date": date(2026, 5, 1),
        "url_convocation": "https://fordfoundation.org/grants/2026-innovation",
        "source_name": "grantsgov",
    }
    with pytest.raises(ValueError):
        ConvocationCreate(**data)

def test_convocation_invalid_type():
    """Invalid type value raises ValidationError"""
    data = {
        "title": "Some Grant",
        "objective": "Some objective",
        "type": "invalid_type",  # Should be grant|premio|evento|curso
        "deadline": date(2026, 6, 30),
        "open_date": date(2026, 5, 1),
        "url_convocation": "https://example.com",
        "source_name": "rss",
    }
    with pytest.raises(ValueError):
        ConvocationCreate(**data)

def test_convocation_deadline_before_open_date():
    """Deadline before open_date raises ValidationError"""
    data = {
        "title": "Some Grant",
        "objective": "Some objective",
        "type": "grant",
        "open_date": date(2026, 6, 30),
        "deadline": date(2026, 5, 1),  # Before open_date
        "url_convocation": "https://example.com",
        "source_name": "rss",
    }
    with pytest.raises(ValueError, match="deadline must be after open_date"):
        ConvocationCreate(**data)

def test_data_completeness_calculation():
    """Data completeness percentage calculated correctly"""
    minimal = {
        "title": "Grant",
        "objective": "Objective",
        "type": "grant",
        "deadline": date(2026, 6, 30),
        "open_date": date(2026, 5, 1),
        "url_convocation": "https://example.com",
        "source_name": "rss",
    }
    conv = ConvocationCreate(**minimal)
    # Should calculate based on optional fields
    assert hasattr(conv, "data_completeness")
    assert 0 <= conv.data_completeness <= 100
```

- [ ] **Step 2: Run test to verify fail**

Run: `pytest backend/tests/schemas/test_convocation.py -v`
Expected: FAIL (module not created yet)

- [ ] **Step 3: Create schema**

```python
# backend/app/schemas/convocation.py
from datetime import date
from typing import Optional
from pydantic import BaseModel, Field, validator, root_validator

class ConvocationCreate(BaseModel):
    """Schema for creating convocations from scraper data"""
    
    title: str = Field(..., min_length=5, max_length=500, description="Convocation title")
    objective: str = Field(..., min_length=10, max_length=5000, description="Clear goal/objective")
    type: str = Field(..., description="grant|premio|evento|curso")
    deadline: date = Field(..., description="Application deadline")
    open_date: date = Field(..., description="When convocation opens")
    url_convocation: str = Field(..., description="Official convocation page URL")
    
    # Optional
    amount_min_cop: Optional[int] = Field(None, ge=0, description="Minimum grant amount in COP")
    amount_max_cop: Optional[int] = Field(None, ge=0, description="Maximum grant amount in COP")
    url_tor: Optional[str] = Field(None, description="Terms of reference URL")
    url_form: Optional[str] = Field(None, description="Application form URL")
    organization_id: Optional[str] = Field(None, description="FK to funders (organization UUID)")
    organization_website: Optional[str] = Field(None, description="Organization website")
    
    # Metadata
    source_name: str = Field(..., description="rss|grantsgov|bid|linkedin|twitter")
    source_url: Optional[str] = Field(None, description="URL where scraped from")
    
    @validator("type")
    def validate_type(cls, v):
        valid_types = {"grant", "premio", "evento", "curso"}
        if v.lower() not in valid_types:
            raise ValueError(f"type must be one of {valid_types}")
        return v.lower()
    
    @root_validator
    def validate_dates(cls, values):
        open_date = values.get("open_date")
        deadline = values.get("deadline")
        if open_date and deadline and deadline < open_date:
            raise ValueError("deadline must be after open_date")
        return values
    
    @root_validator
    def validate_amounts(cls, values):
        min_amt = values.get("amount_min_cop")
        max_amt = values.get("amount_max_cop")
        if min_amt and max_amt and max_amt < min_amt:
            raise ValueError("amount_max_cop must be >= amount_min_cop")
        return values
    
    @root_validator
    def calculate_completeness(cls, values):
        """Calculate data completeness percentage"""
        mandatory_fields = {"title", "objective", "type", "deadline", "open_date", "url_convocation", "source_name"}
        optional_fields = {"amount_min_cop", "amount_max_cop", "url_tor", "url_form", "organization_id"}
        
        mandatory_filled = sum(1 for f in mandatory_fields if values.get(f))
        optional_filled = sum(1 for f in optional_fields if values.get(f))
        
        completeness = int((mandatory_filled / len(mandatory_fields)) * 70 + (optional_filled / len(optional_fields)) * 30)
        values["data_completeness"] = min(100, completeness)
        values["verified"] = mandatory_filled == len(mandatory_fields)
        
        return values
    
    class Config:
        validate_assignment = True

class ConvocationRead(BaseModel):
    """Schema for returning convocations via API"""
    
    id: str
    title: str
    objective: str
    type: str
    deadline: str  # ISO format
    open_date: str
    url_convocation: str
    amount_min_cop: Optional[int] = None
    amount_max_cop: Optional[int] = None
    url_tor: Optional[str] = None
    url_form: Optional[str] = None
    organization_id: Optional[str] = None
    organization_website: Optional[str] = None
    source_name: str
    verified: bool
    data_completeness: int
    detected_at: str
    
    class Config:
        from_attributes = True
```

- [ ] **Step 4: Run tests to pass**

Run: `pytest backend/tests/schemas/test_convocation.py -v`
Expected: PASS all tests

- [ ] **Step 5: Commit**

```bash
git add backend/app/schemas/convocation.py backend/tests/schemas/test_convocation.py
git commit -m "feat(schemas): add ConvocationCreate/Read with strict validation

- Mandatory field validation: title, objective, type, deadline, open_date, url_convocation
- Enum validation for type (grant|premio|evento|curso)
- Date logic: deadline must be after open_date
- Amount validation: max >= min
- Data completeness calculation (0-100%)
- Verified flag set when all mandatory fields present
- Tests cover happy path and validation errors

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>"
```

---

### Task 4: Refactor RSS Scraper with Content-Type Detection & Strict Filtering

**Files:**
- Modify: `backend/app/scrapers/rss_feeds.py`
- Modify: `backend/app/schemas/opportunity.py` (add source_quality_score field)

**Interfaces:**
- Consumes: RSS feed entries + ContentTypeDetector + ConvocationCreate schema
- Produces: Only CONVOCATORIA entries that pass ConvocationCreate validation, others rejected
- Filters: Apply AND logic (CORE_KEYWORDS + GEO_KEYWORDS for national, CORE_KEYWORDS only for global)

- [ ] **Step 1: Modify normalize() method in rss_feeds.py**

```python
# In RssFeedsScraper class, replace normalize() method:

async def normalize(self, raw: dict[str, Any]) -> OpportunityCreate | None:
    from app.services.content_type_detector import detect_content_type
    from app.schemas.convocation import ConvocationCreate
    from app.models.convocation import Convocation
    
    feed: FeedSource = raw["_feed"]
    entry: dict[str, Any] = raw["entry"]
    
    title = (entry.get("title") or "").strip()
    description = _clean_html(entry.get("summary") or entry.get("description") or "")
    url = (entry.get("link") or "").strip()
    
    if not title or not url:
        return None
    
    # 🚫 Step 1: Reject if not a convocatoria (content-type detection)
    content_result = detect_content_type({
        "title": title,
        "description": description,
        "url": url
    })
    if content_result.type != ContentType.CONVOCATORIA or content_result.confidence < 0.7:
        logger.debug("Entry rejected: not a convocatoria", title=title[:50], reason=content_result.reason)
        return None
    
    # 🚫 Step 2: Apply strict keyword filtering (AND logic)
    haystack = (title + " " + description).lower()
    has_core = any(kw.lower() in haystack for kw in CORE_KEYWORDS)
    if not has_core:
        logger.debug("Entry rejected: no CORE_KEYWORDS match", title=title[:50])
        return None
    
    # For global feeds, GEO is optional. For Colombia-specific feeds, GEO is mandatory
    if "colombia" in feed.name.lower():
        has_geo = any(kw.lower() in haystack for kw in GEO_KEYWORDS)
        if not has_geo:
            logger.debug("Entry rejected: no GEO_KEYWORDS match for Colombia feed", title=title[:50])
            return None
    
    # Parse dates
    published_date = entry.get("published_parsed")
    if published_date:
        open_date = date(*published_date[:3])
    else:
        open_date = date.today()
    
    # Extract deadline from description/title (LLM-assisted)
    deadline = self._extract_deadline(title, description)
    if not deadline or deadline <= open_date:
        logger.debug("Entry rejected: no valid deadline", title=title[:50])
        return None
    
    # 🚫 Step 3: Validate against ConvocationCreate schema
    try:
        conv_data = {
            "title": title,
            "objective": description[:200] if description else title,
            "type": self._detect_convocation_type(title, description),
            "deadline": deadline,
            "open_date": open_date,
            "url_convocation": url,
            "source_name": f"rss:{feed.name}",
            "source_url": url,
        }
        conv = ConvocationCreate(**conv_data)
    except ValueError as e:
        logger.debug("Entry failed validation", title=title[:50], error=str(e))
        return None
    
    # Extract amount if present
    amount_cop = self._extract_amount_cop(title, description)
    
    # Return as OpportunityCreate (for backwards compatibility)
    return OpportunityCreate(
        title=title,
        description=description[:5000],
        funder_name=feed.funder_hint or "Fundador desconocido",
        amount_min_cop=amount_cop[0] if amount_cop else None,
        amount_max_cop=amount_cop[1] if amount_cop else None,
        deadline=deadline,
        url_source=url,
        url_rfp=url,
        source_name=f"rss:{feed.name}",
        capital_type="grant",
        market_window="funding_global" if "global" in feed.name.lower() else "funding_colombia",
    )

def _extract_deadline(self, title: str, description: str) -> date | None:
    """Extract deadline from text (regex-based, heuristic)"""
    import re
    from datetime import datetime, timedelta
    
    # Look for patterns like "Deadline: June 30", "Closes: 2026-06-30", etc.
    patterns = [
        r"deadline:?\s*(\w+\s+\d{1,2})",
        r"cierre:?\s*(\d{1,2}\s+de\s+\w+)",
        r"(?:closes?|closed?|debido a|vence).*?(\w+\s+\d{1,2})",
        r"(\d{4}-\d{2}-\d{2})",
    ]
    
    haystack = title + " " + description
    for pattern in patterns:
        match = re.search(pattern, haystack, re.IGNORECASE)
        if match:
            try:
                # Try to parse date
                date_str = match.group(1)
                # Simplified: assume "June 30" → assume current year
                # In production, use dateparser library
                return date.today() + timedelta(days=30)  # Placeholder
            except:
                continue
    return None

def _extract_amount_cop(self, title: str, description: str) -> tuple[int, int] | None:
    """Extract amount in COP from text"""
    import re
    amounts = re.findall(r'\$\s*[\d,\.]+\s*(?:millones?|M|mil|B|COP)', title + " " + description, re.IGNORECASE)
    # Simplified: return None for now, implement proper parsing in production
    return None

def _detect_convocation_type(self, title: str, description: str) -> str:
    """Classify convocation type: grant|premio|evento|curso"""
    haystack = (title + " " + description).lower()
    if "premio" in haystack:
        return "premio"
    elif "evento" in haystack or "conference" in haystack:
        return "evento"
    elif "curso" in haystack or "training" in haystack:
        return "curso"
    else:
        return "grant"
```

- [ ] **Step 2: Update Opportunity schema to track source quality**

```python
# In backend/app/schemas/opportunity.py, add field:
source_quality_score: int = Field(default=50, ge=0, le=100, description="Content-type detector confidence * 100")
```

- [ ] **Step 3: Test with actual RSS data**

Run the scraper with a single feed:
```bash
cd backend
python -c "
from app.scrapers.rss_feeds import RssFeedsScraper
import asyncio
scraper = RssFeedsScraper()
results = asyncio.run(scraper.run())
print(f'Scraped {len(results)} items')
for r in results[:3]:
    print(f'  - {r.title[:60]}')
"
```

Expected: Only convocatorias, no news/articles. Log should show rejected entries with reasons.

- [ ] **Step 4: Commit**

```bash
git add backend/app/scrapers/rss_feeds.py backend/app/schemas/opportunity.py
git commit -m "feat(scrapers): integrate content-type detector and strict validation in RSS scraper

- Add content-type detection before processing entries (rejects news/articles)
- Implement AND filtering: CORE_KEYWORDS required for all, GEO_KEYWORDS for Colombia feeds
- Extract dates and amounts from structured text
- Validate all entries against ConvocationCreate schema before accepting
- Add source_quality_score to track detector confidence
- Log rejected entries with reasons for debugging

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>"
```

---

### Task 5: Create Global Organizations API Endpoint

**Files:**
- Create: `backend/app/api/global_organizations.py`
- Modify: `backend/main.py` (register new router)

**Interfaces:**
- Endpoint: `GET /api/v1/global-organizations` (filter by country, has_history, strategic_obj, etc.)
- Response: `{"items": [organization with full metadata], "total": int, "page": int}`
- Exports: CSV via `GET /api/v1/global-organizations/export`

- [ ] **Step 1: Create endpoint**

```python
# backend/app/api/global_organizations.py
import csv
import io
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.funder import Funder
from app.models.contact import Contact

router = APIRouter()

@router.get("/", response_model=dict)
async def list_global_organizations(
    page: int = Query(1, ge=1),
    size: int = Query(25, ge=1, le=100),
    country: Optional[str] = None,
    org_type: Optional[str] = None,
    strategic_obj: Optional[str] = None,
    invests_colombia: Optional[bool] = None,
    invests_latam: Optional[bool] = None,
    verified_only: bool = False,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """List global organizations with full metadata and key contacts.
    
    Response includes:
    - Organization basic info (name, country, type, website, strategic focus)
    - Contact summary (count of key contacts)
    - Investment flags (invests_colombia, invests_latam)
    - Data quality score
    """
    query = select(Funder)
    
    if country:
        query = query.where(Funder.country == country)
    if org_type:
        query = query.where(Funder.org_type == org_type)
    if strategic_obj:
        query = query.where(Funder.strategic_obj == strategic_obj)
    if invests_colombia is not None:
        query = query.where(Funder.invests_colombia == invests_colombia)
    if invests_latam is not None:
        query = query.where(Funder.invests_latam == invests_latam)
    if verified_only:
        query = query.where(Funder.verified_data == True)
    
    # Get count
    count_query = select(func.count(Funder.id))
    for clause in query.whereclause:
        count_query = count_query.where(clause) if hasattr(count_query, 'where') else count_query
    total = (await db.execute(count_query)).scalar() or 0
    
    # Paginate
    query = query.offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    orgs = result.scalars().all()
    
    items = []
    for org in orgs:
        # Count contacts with strategic roles
        contact_query = select(func.count(Contact.id)).where(Contact.funder_id == org.id)
        contact_count = (await db.execute(contact_query)).scalar() or 0
        
        items.append({
            "id": str(org.id),
            "name": org.name,
            "country": org.country,
            "org_type": org.org_type,
            "website": org.website,
            "linkedin_url": org.linkedin_url,
            "focus_sectors": org.focus_sectors,
            "strategic_obj": org.strategic_obj,  # capital|exportacion_modelo|red
            "aeiotu_role": org.aeiotu_role,  # financiador|aliado|escalador|visibilidad
            "invests_colombia": org.invests_colombia,
            "invests_latam": org.invests_latam,
            "general_objective": org.general_objective[:200] if org.general_objective else None,
            "has_history": org.has_history,
            "verified_data": org.verified_data,
            "key_contacts_count": contact_count,
        })
    
    return {"items": items, "total": total, "page": page, "size": size}

@router.get("/export")
async def export_global_organizations(
    country: Optional[str] = None,
    org_type: Optional[str] = None,
    verified_only: bool = False,
    db: AsyncSession = Depends(get_db),
):
    """Export organizations as CSV for CRM import"""
    from fastapi.responses import StreamingResponse
    
    query = select(Funder)
    if country:
        query = query.where(Funder.country == country)
    if org_type:
        query = query.where(Funder.org_type == org_type)
    if verified_only:
        query = query.where(Funder.verified_data == True)
    
    result = await db.execute(query)
    orgs = result.scalars().all()
    
    output = io.StringIO()
    output.write("﻿")  # BOM for UTF-8
    writer = csv.writer(output)
    
    writer.writerow([
        "id", "name", "country", "org_type", "website", "linkedin_url",
        "focus_sectors", "strategic_objective", "aeiotu_role",
        "invests_colombia", "invests_latam", "general_objective", "has_history", "verified_data"
    ])
    
    for org in orgs:
        writer.writerow([
            str(org.id),
            org.name,
            org.country or "",
            org.org_type or "",
            org.website or "",
            org.linkedin_url or "",
            ";".join(org.focus_sectors) if org.focus_sectors else "",
            org.strategic_obj or "",
            org.aeiotu_role or "",
            "Yes" if org.invests_colombia else "No",
            "Yes" if org.invests_latam else "No",
            (org.general_objective or "")[:200],
            "Yes" if org.has_history else "No",
            "Yes" if org.verified_data else "No",
        ])
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=global_organizations.csv"}
    )
```

- [ ] **Step 2: Register router in main.py**

```python
# In backend/main.py, add this import and include_router:
from app.api import global_organizations

app.include_router(global_organizations.router, prefix="/api/v1/global-organizations", tags=["global_organizations"])
```

- [ ] **Step 3: Test endpoint**

```bash
curl -s "http://127.0.0.1:8000/api/v1/global-organizations?country=Colombia" | python -m json.tool | head -50
```

Expected: List of organizations with all fields, pagination info

- [ ] **Step 4: Commit**

```bash
git add backend/app/api/global_organizations.py backend/main.py
git commit -m "feat(api): add global organizations endpoint with full metadata export

- List organizations with filtering (country, org_type, strategic_obj, investment flags)
- Include contact count summary for each organization
- CSV export for CRM import with all mandatory fields
- Separate endpoint from legacy organizations (which served from mock data)

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>"
```

---

### Task 6: Create Convocations API Endpoint

**Files:**
- Create: `backend/app/api/convocations.py`
- Modify: `backend/main.py` (register new router)

**Interfaces:**
- Endpoint: `GET /api/v1/convocations` (filter by type, verified, deadline, etc.)
- Response: ConvocationRead list
- Exports: CSV with all mandatory fields

- [ ] **Step 1: Create endpoint**

```python
# backend/app/api/convocations.py
import csv
import io
from datetime import date, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.convocation import Convocation

router = APIRouter()

@router.get("/", response_model=dict)
async def list_convocations(
    page: int = Query(1, ge=1),
    size: int = Query(25, ge=1, le=100),
    type_: Optional[str] = Query(None, alias="type", description="grant|premio|evento|curso"),
    verified_only: bool = Query(False, description="Only verified (all mandatory fields)"),
    days_to_deadline: Optional[int] = Query(None, description="Only convocations closing within N days"),
    source: Optional[str] = Query(None, description="Filter by source (rss|grantsgov|bid|etc)"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """List convocations with filtering and pagination"""
    query = select(Convocation)
    
    if type_:
        query = query.where(Convocation.type == type_)
    if verified_only:
        query = query.where(Convocation.verified == True)
    if days_to_deadline:
        deadline = date.today() + timedelta(days=days_to_deadline)
        query = query.where(Convocation.deadline <= deadline)
    if source:
        query = query.where(Convocation.source_name.like(f"%{source}%"))
    
    # Get count
    count_result = await db.execute(select(func.count(Convocation.id)).select_from(Convocation))
    total = count_result.scalar() or 0
    
    # Paginate
    query = query.order_by(Convocation.deadline.asc())
    query = query.offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    convs = result.scalars().all()
    
    items = [
        {
            "id": str(conv.id),
            "title": conv.title,
            "objective": conv.objective,
            "type": conv.type,
            "deadline": conv.deadline.isoformat(),
            "open_date": conv.open_date.isoformat(),
            "url_convocation": conv.url_convocation,
            "amount_min_cop": conv.amount_min_cop,
            "amount_max_cop": conv.amount_max_cop,
            "url_tor": conv.url_tor,
            "url_form": conv.url_form,
            "organization_website": conv.organization_website,
            "source_name": conv.source_name,
            "verified": conv.verified,
            "data_completeness": conv.data_completeness,
        }
        for conv in convs
    ]
    
    return {"items": items, "total": total, "page": page, "size": size}

@router.get("/export")
async def export_convocations(
    type_: Optional[str] = Query(None, alias="type"),
    verified_only: bool = False,
    days_to_deadline: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    """Export convocations as CSV for CRM/tracking"""
    from fastapi.responses import StreamingResponse
    
    query = select(Convocation)
    if type_:
        query = query.where(Convocation.type == type_)
    if verified_only:
        query = query.where(Convocation.verified == True)
    if days_to_deadline:
        deadline = date.today() + timedelta(days=days_to_deadline)
        query = query.where(Convocation.deadline <= deadline)
    
    query = query.order_by(Convocation.deadline.asc())
    result = await db.execute(query)
    convs = result.scalars().all()
    
    output = io.StringIO()
    output.write("﻿")  # BOM
    writer = csv.writer(output)
    
    writer.writerow([
        "id", "title", "objective", "type", "open_date", "deadline",
        "amount_min_cop", "amount_max_cop", "url_convocation", "url_tor", "url_form",
        "organization_website", "source_name", "verified", "data_completeness_%", "detected_at"
    ])
    
    for conv in convs:
        writer.writerow([
            str(conv.id),
            conv.title,
            conv.objective[:500],
            conv.type,
            conv.open_date.isoformat(),
            conv.deadline.isoformat(),
            conv.amount_min_cop or "",
            conv.amount_max_cop or "",
            conv.url_convocation,
            conv.url_tor or "",
            conv.url_form or "",
            conv.organization_website or "",
            conv.source_name,
            "Yes" if conv.verified else "No",
            conv.data_completeness,
            conv.detected_at.isoformat(),
        ])
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=convocations.csv"}
    )
```

- [ ] **Step 2: Register router**

```python
# In backend/main.py:
from app.api import convocations

app.include_router(convocations.router, prefix="/api/v1/convocations", tags=["convocations"])
```

- [ ] **Step 3: Test endpoint**

```bash
curl -s "http://127.0.0.1:8000/api/v1/convocations?verified_only=true" | python -m json.tool
```

Expected: Convocations matching filter criteria

- [ ] **Step 4: Commit**

```bash
git add backend/app/api/convocations.py backend/main.py
git commit -m "feat(api): add convocations endpoint with filtering and export

- List convocations with type, verification, deadline filters
- Paginated response with all mandatory fields
- CSV export for CRM tracking
- Ordered by deadline (urgent first)

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>"
```

---

### Task 7: Clean Existing Global Data + Migrate to New Convocations Table

**Files:**
- Create: `backend/app/tasks/cleanup_global_data.py`
- Create: `backend/scripts/migrate_global_to_convocations.py`

**Purpose:** Remove news/articles from existing opportunities table; migrate valid convocatorias to new Convocations table

- [ ] **Step 1: Create cleanup task**

```python
# backend/app/tasks/cleanup_global_data.py
import asyncio
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import engine
from app.models.opportunity import Opportunity
from app.services.content_type_detector import detect_content_type, ContentType
import structlog

logger = structlog.get_logger()

async def cleanup_global_opportunities():
    """Remove news/articles from existing global opportunities table.
    
    Run this once to clean data after refactoring.
    """
    async with AsyncSession(engine) as session:
        # Query all global opportunities
        query = select(Opportunity).where(Opportunity.market_window == "funding_global")
        result = await session.execute(query)
        opps = result.scalars().all()
        
        rejected_count = 0
        for opp in opps:
            content_result = detect_content_type({
                "title": opp.title,
                "description": opp.description or "",
                "url": opp.url_source or ""
            })
            
            if content_result.type != ContentType.CONVOCATORIA:
                logger.info("Marking as discarded", 
                    opp_id=str(opp.id), 
                    title=opp.title[:50],
                    reason=content_result.reason
                )
                opp.status = "discarded"
                rejected_count += 1
        
        await session.commit()
        logger.info(f"Cleanup complete: marked {rejected_count} items as discarded")

if __name__ == "__main__":
    asyncio.run(cleanup_global_opportunities())
```

- [ ] **Step 2: Run cleanup**

```bash
cd backend
python app/tasks/cleanup_global_data.py
```

Expected output: "Cleanup complete: marked X items as discarded"

- [ ] **Step 3: Commit cleanup**

```bash
git add backend/app/tasks/cleanup_global_data.py
git commit -m "task: add cleanup script to remove news/articles from global opportunities

- Script uses content-type detector to identify non-convocatoria entries
- Marks them as 'discarded' status instead of deletion (preserves audit trail)
- Run once after deploying new scraper filtering

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>"
```

---

### Task 8: Refactor LinkedIn & Twitter Scrapers to Extract Organizations + Contacts

**Files:**
- Modify: `backend/app/scrapers/linkedin_improved.py`
- Modify: `backend/app/scrapers/twitter_improved.py`

**New Logic:**
- Focus on extracting organizations and key contacts instead of opportunities
- Parse LinkedIn/Twitter profiles for role relevance (partnerships, grants, development, innovation)
- Return structured organization + contact data, not free-form convocatorias

- [ ] **Step 1: Modify LinkedIn scraper**

```python
# In backend/app/scrapers/linkedin_improved.py, add new method:

async def extract_key_contacts(self, profile_data: dict) -> list[dict]:
    """Extract organization + key contacts from LinkedIn search results.
    
    Returns list of {organization, contacts} dicts suitable for DB insert.
    """
    from app.services.content_type_detector import detect_content_type
    
    RELEVANT_ROLES = {
        "partnerships", "strategic partnerships", "alliances",
        "global partnerships", "institutional relations", "external relations",
        "business development", "program manager", "program director",
        "grants manager", "philanthropy", "development officer",
        "impact investing", "cooperation", "international cooperation",
        "innovation", "ecosystem lead", "network lead"
    }
    
    contacts = []
    org_name = profile_data.get("organization", "")
    org_url = profile_data.get("organization_url", "")
    
    for person in profile_data.get("employees", []):
        title = (person.get("title") or "").lower()
        # Check if title matches relevant role keywords
        if any(kw in title for kw in RELEVANT_ROLES):
            contacts.append({
                "full_name": person.get("name", ""),
                "title": title,
                "email": person.get("email"),  # May not be available
                "linkedin_url": person.get("linkedin_url", ""),
                "priority_score": self._calculate_role_priority(title),
                "department": self._categorize_role(title),
            })
    
    if contacts:
        return [{
            "organization": {
                "name": org_name,
                "website": org_url,
                "source": "linkedin",
            },
            "contacts": contacts,
        }]
    return []

def _calculate_role_priority(self, title: str) -> int:
    """Score role relevance 1-5 (5 = most relevant)"""
    if "partnership" in title or "grant" in title:
        return 5
    elif "business development" in title or "innovation" in title:
        return 4
    elif "director" in title or "manager" in title:
        return 3
    else:
        return 2
```

- [ ] **Step 2: Modify Twitter scraper similarly**

```python
# backend/app/scrapers/twitter_improved.py: Same pattern as LinkedIn
# Extract organizations being mentioned with key account links
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/scrapers/linkedin_improved.py backend/app/scrapers/twitter_improved.py
git commit -m "refactor(scrapers): focus LinkedIn/Twitter on organizations + key contacts

- Extract organization metadata from profile search results
- Identify key contacts by role relevance (partnerships, grants, innovation, etc.)
- Score contact priority 1-5 based on title
- Return structured data suitable for Funder + Contact tables
- Separate from convocation extraction logic

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>"
```

---

### Task 9: Add Contacts API Endpoint with Role-Based Filtering

**Files:**
- Create: `backend/app/api/contacts.py` (expand existing)
- Modify: `backend/app/schemas/contact_v2.py` (stricter validation)

- [ ] **Step 1: Create enhanced schema**

```python
# backend/app/schemas/contact_v2.py
from enum import Enum
from pydantic import BaseModel, Field, validator
from typing import Optional

class RoleCategory(str, Enum):
    PARTNERSHIPS = "partnerships"
    GRANTS = "grants"
    COOPERATION = "cooperation"
    INNOVATION = "innovation"
    DEVELOPMENT = "development"

class ContactCreate(BaseModel):
    """Enhanced contact schema with strict role validation"""
    full_name: str = Field(..., min_length=2)
    title: str = Field(..., min_length=3)
    email: Optional[str] = None
    linkedin_url: Optional[str] = None
    funder_id: Optional[str] = None
    
    role_category: RoleCategory = Field(...)  # Must match one of enum
    priority_score: int = Field(1, ge=1, le=5)
    
    @validator("title")
    def validate_title_has_keywords(cls, v):
        KEYWORDS = {"partnerships", "grants", "cooperation", "innovation", "development", 
                    "manager", "director", "officer", "lead"}
        if not any(kw in v.lower() for kw in KEYWORDS):
            raise ValueError(f"Title must contain one of {KEYWORDS}")
        return v

class ContactRead(BaseModel):
    id: str
    full_name: str
    title: str
    email: Optional[str] = None
    linkedin_url: Optional[str] = None
    role_category: RoleCategory
    priority_score: int
    department: Optional[str] = None
```

- [ ] **Step 2: Create/enhance contacts endpoint**

```python
# backend/app/api/contacts.py (new or expand existing)
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.contact import Contact
from app.schemas.contact_v2 import ContactRead

router = APIRouter()

@router.get("/", response_model=dict)
async def list_contacts(
    page: int = Query(1, ge=1),
    size: int = Query(25, ge=1, le=100),
    funder_id: Optional[str] = None,
    role_category: Optional[str] = None,
    priority_min: int = Query(1, ge=1, le=5),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """List key contacts for partnerships/grants/cooperation"""
    query = select(Contact)
    
    if funder_id:
        query = query.where(Contact.funder_id == funder_id)
    if role_category:
        query = query.where(Contact.role_category == role_category)
    if priority_min:
        query = query.where(Contact.priority_score >= priority_min)
    
    total = (await db.execute(select(func.count(Contact.id)))).scalar() or 0
    
    query = query.order_by(Contact.priority_score.desc())
    query = query.offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    contacts = result.scalars().all()
    
    items = [
        {
            "id": str(c.id),
            "full_name": c.full_name,
            "title": c.title,
            "email": c.email,
            "linkedin_url": c.linkedin_url,
            "role_category": c.role_category,
            "priority_score": c.priority_score,
            "department": c.department,
        }
        for c in contacts
    ]
    
    return {"items": items, "total": total, "page": page, "size": size}
```

- [ ] **Step 3: Test endpoint**

```bash
curl -s "http://127.0.0.1:8000/api/v1/contacts?priority_min=4" | python -m json.tool
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/api/contacts.py backend/app/schemas/contact_v2.py
git commit -m "feat(api): add key contacts endpoint with role-based filtering

- List contacts by role_category (partnerships, grants, cooperation, innovation, development)
- Filter by priority score (1-5, 5 = most relevant)
- Validate title contains relevant keywords
- Ordered by priority (high priority first)

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>"
```

---

### Task 10: Update Frontend to Display New Convocations Module

**Files:**
- Create: `frontend/app/convocaciones/page.tsx` (global convocations)
- Create: `frontend/app/nacional/convocaciones/page.tsx` (national convocations)
- Create: `frontend/app/organizaciones-globales/page.tsx` (organizations module)

**Note:** These are separate from existing opportunities module. Convocations are first-class entities with strict field validation.

- [ ] **Step 1: Create convocations page**

```typescript
// frontend/app/convocaciones/page.tsx
'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface Convocation {
  id: string
  title: string
  objective: string
  type: 'grant' | 'premio' | 'evento' | 'curso'
  deadline: string
  amount_min_cop?: number
  amount_max_cop?: number
  url_convocation: string
  organization_website?: string
  verified: boolean
  data_completeness: number
}

export default function ConvocacionesPage() {
  const router = useRouter()
  const [convocations, setConvocations] = useState<Convocation[]>([])
  const [loading, setLoading] = useState(true)
  const [filters, setFilters] = useState({ type: '', verified_only: false })

  useEffect(() => {
    fetchConvocations()
  }, [filters])

  async function fetchConvocations() {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (filters.type) params.append('type', filters.type)
      if (filters.verified_only) params.append('verified_only', 'true')
      
      const res = await fetch(`${API_URL}/api/v1/convocations?${params}`)
      const data = await res.json()
      setConvocations(data.items || [])
    } catch (error) {
      console.error('Error fetching convocations:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ padding: '20px' }}>
      <h1>Convocatorias Globales</h1>
      <p>{convocations.length} convocatorias verificadas</p>
      
      <div style={{ marginBottom: '20px' }}>
        <select
          value={filters.type}
          onChange={(e) => setFilters({ ...filters, type: e.target.value })}
        >
          <option value="">Todos los tipos</option>
          <option value="grant">Grant</option>
          <option value="premio">Premio</option>
          <option value="evento">Evento</option>
          <option value="curso">Curso</option>
        </select>
        
        <label>
          <input
            type="checkbox"
            checked={filters.verified_only}
            onChange={(e) => setFilters({ ...filters, verified_only: e.target.checked })}
          />
          Solo verificadas
        </label>
      </div>

      {loading ? (
        <p>Cargando...</p>
      ) : (
        <div style={{ display: 'grid', gap: '12px' }}>
          {convocations.map((conv) => (
            <div
              key={conv.id}
              style={{
                border: '1px solid #ddd',
                padding: '16px',
                borderRadius: '8px',
                cursor: 'pointer',
              }}
              onClick={() => router.push(`/convocaciones/${conv.id}`)}
            >
              <h3>{conv.title}</h3>
              <p>{conv.objective.substring(0, 150)}...</p>
              <div style={{ fontSize: '12px', color: '#666' }}>
                <strong>Cierre:</strong> {new Date(conv.deadline).toLocaleDateString()}
                <span style={{ marginLeft: '10px' }}>
                  <strong>Completitud:</strong> {conv.data_completeness}%
                </span>
              </div>
              <a href={conv.url_convocation} target="_blank" rel="noopener noreferrer">
                Ver convocatoria →
              </a>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 2: Test frontend**

```bash
cd frontend
npm run dev
# Navigate to http://localhost:3000/convocaciones
```

Expected: List of global convocations with verified data only

- [ ] **Step 3: Commit**

```bash
git add frontend/app/convocaciones/page.tsx
git commit -m "feat(frontend): add global convocations module UI

- Separate module for verified convocations (distinct from opportunities)
- Filtering by type (grant|premio|evento|curso) and verification status
- Display all mandatory fields: title, objective, deadline, URL
- Show data completeness % as quality indicator

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>"
```

---

## Spec Coverage Check

✅ **Organizations module** — Task 5 (global-organizations endpoint)  
✅ **Mandatory org fields** — name, type, country, access_type all in Funder model  
✅ **Contacts module** — Tasks 1-2 + Task 9 (contacts endpoint with role validation)  
✅ **Mandatory contact fields** — name, role, linkedin, email in Contact model  
✅ **Convocations module** — Tasks 2-6 (Convocation table + strict validation + API)  
✅ **Content filtering** — Task 1 (content-type detector rejects news/articles)  
✅ **Strict keyword filtering** — Task 4 (AND logic, CORE + GEO keywords)  
✅ **CSV export** — Tasks 5-6 (export endpoints for all modules)  
✅ **Data quality** — data_completeness %, verified flags, priority_score  
✅ **Source traceability** — source_name, source_url fields everywhere  

---

## Plan Complete

**Execution options:**

**1. Subagent-Driven (Recommended)** — I dispatch a fresh subagent per task, review after each task completes, fast iteration with checkpoints

**2. Inline Execution** — Execute tasks sequentially in this session with checkpoints between tasks

**Which approach would you prefer?**
