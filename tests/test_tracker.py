import copy,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from tracker.core import identify,price,valid_url,history_stats,normalize,integrate,Page,CAPACITIES
from tracker.scan import scan,write
NOW='2026-11-03T12:00:00+00:00'
STORE={'id':'test','domain':'shop.bg','channel':'retail'}
def sample(amount=800):
    return normalize({'name':'Apple iPhone 17 256GB Black','color':'Black'},{'price':amount,'priceCurrency':'EUR','availability':'https://schema.org/InStock','itemCondition':'https://schema.org/NewCondition','seller':{'name':'Shop'}},STORE,'https://shop.bg/products/iphone-17',NOW)
class Parsing(unittest.TestCase):
    def test_models(self):
        for title,model,size in [('iPhone 15 Pro Max 1 TB','iPhone 15 Pro Max',1024),('iPhone 17 Air 256 GB','iPhone Air',256),('iPhone 17 Pro Max 2TB','iPhone 17 Pro Max',2048),('iPhone 16 8GB 128GB','iPhone 16',128)]:self.assertEqual(identify(title)[:2],(model,size))
    def test_invalid_models(self):
        for title in ['iPhone 17 128GB','iPhone 17e 256GB','Case iPhone 17 256GB','iPhone 15 Pro Max 128GB','used iPhone 16 256GB','iPhone 16 256GB 512GB']:
            with self.assertRaises(ValueError,msg=title):identify(title)
    def test_prices(self):
        for value in ['1 049,99 €','1.049,99','1,049.99','1049.99']:self.assertEqual(price(value),1049.99)
        for value,currency in [('999','BGN'),('NaN','EUR'),('-1','EUR'),('0','EUR')]:
            with self.assertRaises(ValueError):price(value,currency)
    def test_urls(self):
        for u in ['http://shop.bg/product/phone','https://evil.bg/product/phone','https://shop.bg/','https://shop.bg.evil.com/products/phone','https://user@shop.bg/products/phone']:self.assertFalse(valid_url(u,'shop.bg'))
        self.assertTrue(valid_url('https://shop.bg/products/phone?variant=123','shop.bg'))
    def test_duplicate_variant_identity(self):
        a=sample();b=normalize({'name':'iPhone 17 256GB'},dict(price=800,priceCurrency='EUR',seller='Shop',itemCondition='https://schema.org/NewCondition'),STORE,'https://shop.bg/products/iphone-17?variant=12',NOW)
        self.assertEqual(a['id'],b['id'])
    def test_missing_promo_dates(self):
        r=sample();self.assertIsNone(r['promotion_end']);self.assertFalse(r['advertised_promotion'])
    def test_seller_and_condition(self):
        with self.assertRaises(ValueError):normalize({'name':'iPhone 17 256GB'},{'price':800,'priceCurrency':'EUR'},STORE,'https://shop.bg/products/iphone-17',NOW)
        r=normalize({'name':'iPhone 17 256GB'},{'price':800,'priceCurrency':'EUR','seller':'Shop'},STORE,'https://shop.bg/products/iphone-17',NOW);self.assertFalse(r['eligible']);self.assertEqual(r['condition'],'unknown')
    def test_jsonld(self):
        p=Page('<script type="application/ld+json">{"@type":"Product","name":"iPhone 17"}</script><a href="/a">x</a>');self.assertEqual(p.jsons[0]['@type'],'Product');self.assertEqual(p.links,['/a'])
class History(unittest.TestCase):
    def test_real_drop(self):
        rows=[dict(sample(1000),verified_at='2026-10-15T12:00:00+00:00'),dict(sample(950),verified_at='2026-10-25T12:00:00+00:00')];r=history_stats(rows,sample(800),NOW);self.assertEqual(r['drop_eur'],150);self.assertEqual(r['low_30d'],800);self.assertEqual(r['high_all'],1000);self.assertEqual(r['classification'],'NEW PRICE DROP');self.assertTrue(r['historical_low'])
    def test_advertised_not_new_drop(self):
        old=dict(sample(),verified_at='2026-11-01T12:00:00+00:00');current=dict(sample(),reference_price=1000);r=history_stats([old],current,NOW);self.assertEqual(r['classification'],'NO PRICE CHANGE');self.assertEqual(r['drop_eur'],0)
    def test_insufficient_history(self):
        self.assertEqual(history_stats([],sample(),NOW)['classification'],'FIRST OBSERVATION');self.assertIsNone(history_stats([],sample(),NOW)['average_30d'])
    def test_duplicates_and_unchanged(self):
        row=sample();current,h,_=integrate([],[],[row,row],'test',NOW);self.assertEqual(len(h),1);current,h,_=integrate(current,h,[row],'test',NOW);self.assertEqual(len(h),1);self.assertFalse(current[0]['stale'])
    def test_suspicious_price(self):
        old=sample();current,h,d=integrate([old],[old],[sample(100)],'test',NOW);self.assertEqual(current[0]['price'],800);self.assertTrue(current[0]['stale']);self.assertIn('validation_warning',current[0]);self.assertEqual(d,0)
    def test_failed_preserves_data(self):
        old=sample();current,h,_=integrate([old],[old],[],'test',NOW);self.assertEqual(current[0]['price'],800);self.assertTrue(current[0]['stale']);self.assertEqual(h,[old])
    def test_partial_scan(self):
        class Good:
            def __init__(self,*args):pass
            def scan(self,now):return [sample()],{'errors':[]}
        class Bad:
            def __init__(self,*args):pass
            def scan(self,now):raise RuntimeError('blocked')
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as tmp:
            p=Path(tmp);write(p/'stores.json',[STORE,dict(STORE,id='bad')]);write(p/'price_history.json',[])
            with patch('tracker.scan.ADAPTERS',{'test':Good,'bad':Bad}):r=scan(p)
            self.assertEqual(r['successful_stores'],['test']);self.assertEqual(r['failed_stores'],['bad']);self.assertEqual(len(json.loads((p/'current_prices.json').read_text())),1)
    def test_config_count(self):self.assertEqual(sum(map(len,CAPACITIES.values())),38)
if __name__=='__main__':unittest.main()
