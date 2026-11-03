"""Bulgarian retailer-specific product data readers."""
import re
from html import unescape
from urllib.parse import urlparse
from .base import StructuredAdapter

class PhoneCatalog(StructuredAdapter):
    def candidate(self, url):
        return bool(re.search(r'iphone[-_]+(?:1[567](?![0-9a-z])|air)(?:[-_/]|$)', url, re.I))

class Ozone(PhoneCatalog):
    def product_path(self, url): return urlparse(url).path.startswith('/product/')
    def accept_offer(self, offer):
        return offer.get('seller', {}).get('name', '').casefold() == 'ozone.bg'

class EMag(PhoneCatalog):
    def product_path(self, url): return '/pd/' in urlparse(url).path
    def accept_offer(self, offer):
        # Unknown and marketplace sellers must not be presented as direct retail.
        return offer.get('seller', {}).get('name', '').strip().casefold() == 'emag'

class Technomarket(PhoneCatalog):
    def product_path(self, url): return urlparse(url).path.startswith('/telefoni/')
    def records(self, page, url, html):
        records = super().records(page, url, html)
        # Product JSON-LD omits seller and availability. Use first-party page
        # evidence and leave unproven condition/availability unknown.
        for record in records:
            offer = record.get('offers')
            if record.get('@type') == 'Product' and isinstance(offer, dict):
                offer.setdefault('seller', {'name': 'Technomarket'})
        return records

class Plesio(PhoneCatalog):
    def product_path(self, url): return bool(re.search(r'-p-\d+\.html$', urlparse(url).path))
    def records(self, page, url, html):
        def div(cls):
            m = re.search(r'<div\s+class="' + cls + r'">\s*([^<]+)</div>', html)
            return unescape(m[1]).strip() if m else ''
        name, amount, available = (div(c) for c in ('ptto-name', 'productPriceElement', 'ptto-availability'))
        if not name or not re.fullmatch(r'[\d\s.,]+\s*€', amount):
            return []
        # Visible EUR price is used, not the inconsistent legacy ptto currency tag.
        return [{'@type':'Product','name':name,'url':url,'offers':{
            '@type':'Offer','price':amount,'priceCurrency':'EUR','seller':{'name':'Plesio'},
            'availability':{'1':'https://schema.org/InStock','0':'https://schema.org/OutOfStock'}.get(available,'')
        }}]
