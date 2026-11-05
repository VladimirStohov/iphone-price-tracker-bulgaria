import unittest
from tracker.adapters.buybest import BuyBest
from tracker.core import Page, normalize

class BuyBestTests(unittest.TestCase):
    def setUp(self):
        self.store={'id':'buybest','domain':'buybest.bg','channel':'retail'}
        self.adapter=BuyBest(self.store,None)
        self.url='https://buybest.bg/products/apple-iphone-17-pro-256gb-5'
    def test_explicit_eur_not_bgn_reference_or_accessories(self):
        html='<script>window.accessories={"price_euro":19}; window.product = {"id":2684,"name":"Apple iPhone 17 Pro 256GB","price_euro":1354.41,"price_bgn":2649,"sell_euro":"1517"};</script>'
        record=self.adapter.records(Page(html),self.url,html)[0]
        row=normalize(record,record['offers'],self.store,self.url,'2026-11-05T12:00:00+00:00')
        self.assertEqual(row['price'],1354.41)
        self.assertEqual(row['seller'],'BuyBest.bg')
        self.assertEqual(row['availability'],'unknown')
        self.assertEqual(row['condition'],'unknown')
        self.assertFalse(row['eligible'])
    def test_missing_explicit_eur_rejected(self):
        html='window.product={"name":"iPhone 17 256GB","price":2649};'
        self.assertEqual(self.adapter.records(Page(html),self.url,html),[])
    def test_non_json_is_never_executed(self):
        html='window.product=alert("hi");'
        self.assertEqual(self.adapter.records(Page(html),self.url,html),[])
