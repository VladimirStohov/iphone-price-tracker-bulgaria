from .base import StructuredAdapter
class Ardes(StructuredAdapter):
    """Ardes public /product/ pages; Organization supplies retailer seller evidence."""
    def product_path(self,url):return '/product/' in url
