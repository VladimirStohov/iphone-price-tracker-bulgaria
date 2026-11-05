"""BuyBest public HTML: read the product object's EUR base price, never accessories."""
import json
import re
from urllib.parse import urlparse
from .bulgaria import PhoneCatalog

class BuyBest(PhoneCatalog):
    def product_path(self, url):
        return urlparse(url).path.startswith('/products/')

    def records(self, page, url, html):
        match = re.search(r'window\.product\s*=\s*', html)
        if not match:
            return []
        try:
            product, _ = json.JSONDecoder().raw_decode(html[match.end():])
        except (ValueError, TypeError):
            return []
        if not isinstance(product, dict) or not product.get('name'):
            return []
        # Explicit EUR field. Do not treat BGN, monthly credit or crossed-out
        # price as the selling price. Availability/condition are not inferred.
        amount = product.get('price_euro')
        if amount is None:
            return []
        return [{'@type': 'Product', 'name': product['name'], 'sku': str(product.get('id', '')),
                 'offers': {'@type': 'Offer', 'price': amount, 'priceCurrency': 'EUR',
                            'url': url, 'seller': {'name': 'BuyBest.bg'}}}]
