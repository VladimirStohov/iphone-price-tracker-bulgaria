from .base import StructuredAdapter
class IStyle(StructuredAdapter):
    """iSTYLE Shopify product pages: JSON-LD condition/variants, never collection prices."""
    def product_path(self,url):return '/products/' in url
