"""URL helpers — prefer navigation.load_navigation() for prefix/hub from config."""

from navigation import article_url as nav_article_url
from navigation import hub_url, load_navigation, slug_from_url

HUB_URL = "/how-to"
PAGE_PREFIX = "/how-to-"


def article_url(slug: str) -> str:
    """Article URL using defaults (same as navigation.json pageUrlPrefix)."""
    return nav_article_url(slug)
