import hashlib
import json
import re
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from html import unescape
from html.parser import HTMLParser
from urllib.parse import urlparse

CAPACITIES = {
    'iPhone 15': [128,256,512], 'iPhone 15 Plus': [128,256,512],
    'iPhone 15 Pro': [128,256,512,1024], 'iPhone 15 Pro Max': [256,512,1024],
    'iPhone 16': [128,256,512], 'iPhone 16 Plus': [128,256,512],
    'iPhone 16 Pro': [128,256,512,1024], 'iPhone 16 Pro Max': [256,512,1024],
    'iPhone 17': [256,512], 'iPhone Air': [256,512,1024],
    'iPhone 17 Pro': [256,512,1024], 'iPhone 17 Pro Max': [256,512,1024,2048],
}
def utcnow(): return datetime.now(timezone.utc).isoformat()
def identify(title):
    text = re.sub(r'\s+', ' ', unescape(title)).strip()
    if re.search(r'case|cover|protector|калъф|протектор|refurb|used|renewed|употреб|разопаков', text, re.I):
        raise ValueError('Accessory, used, refurbished or open-box item')
    m = re.search(r'\biPhone\s+(?:(15|16|17)(?!\d|e)(?:\s+(Pro\s+Max|Pro|Plus|Air))?|Air)\b', text, re.I)
    if not m: raise ValueError('Unsupported model')
    model = 'iPhone Air' if not m[1] or (m[2] or '').lower()=='air' else 'iPhone '+m[1]+(' '+m[2].title() if m[2] else '')
    sizes = {int(Decimal(n)*(1024 if u.lower()=='tb' else 1)) for n,u in re.findall(r'\b(128|256|512|1|2)\s*(GB|TB)\b', text, re.I)}
    sizes = sizes.intersection(CAPACITIES.get(model, []))
    if len(sizes)!=1: raise ValueError('Missing, ambiguous or impossible storage')
    return model, sizes.pop(), 17 if model=='iPhone Air' else int(m[1])
def price(value, currency='EUR'):
    if currency!='EUR': raise ValueError('Only explicitly EUR prices accepted')
    raw = re.sub(r'[^\d.,-]', '', str(value).replace('\u00a0',''))
    if ',' in raw and '.' in raw: raw=raw.replace(',','') if raw.rfind('.')>raw.rfind(',') else raw.replace('.','').replace(',','.')
    elif ',' in raw: raw=raw.replace(',','.')
    try: amount=Decimal(raw)
    except InvalidOperation: raise ValueError('Invalid price')
    if not amount.is_finite() or amount<=0: raise ValueError('Price must be finite and positive')
    return float(amount.quantize(Decimal('.01')))
def valid_url(url, domain):
    p=urlparse(url)
    return p.scheme=='https' and p.hostname in (domain,'www.'+domain) and not p.username and p.port in (None,443) and len(p.path.strip('/'))>6
class Page(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True); self.jsons=[];self.links=[];self._script=False;self._buffer=[]
        self.feed(text)
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if tag=='a' and a.get('href'): self.links.append(a['href'])
        if tag=='script' and a.get('type','').lower()=='application/ld+json': self._script=True;self._buffer=[]
    def handle_data(self, text):
        if self._script:self._buffer.append(text)
    def handle_endtag(self, tag):
        if tag=='script' and self._script:
            try:self.jsons.append(json.loads(''.join(self._buffer)))
            except json.JSONDecodeError:pass
            self._script=False
def walk(value):
    if isinstance(value,dict):
        yield value
        for item in value.values(): yield from walk(item)
    elif isinstance(value,list):
        for item in value:yield from walk(item)
def history_stats(observations, current, now):
    rows=sorted((r for r in observations if r['verified_at']<=now),key=lambda r:r['verified_at'])
    if not rows: return {'classification':'POSSIBLE DISCOUNT' if current.get('reference_price') else 'FIRST OBSERVATION','previous_price':None,'drop_eur':None,'drop_percent':None,'low_7d':None,'low_30d':None,'low_all':None,'high_all':None,'average_30d':None,'historical_low':False}
    t=datetime.fromisoformat(now); p=current['price'];prev=rows[-1]['price'];all_prices=[r['price'] for r in rows]+[p]
    recent=lambda days:[r['price'] for r in rows if datetime.fromisoformat(r['verified_at'])>=t-timedelta(days=days)]+[p]
    low=min(all_prices)
    # Observations are event samples, not daily snapshots; average is explicitly observation-weighted.
    r30=recent(30);span=(t-datetime.fromisoformat(rows[0]['verified_at'])).total_seconds()/86400
    return {'classification':'NEW PRICE DROP' if p<prev else 'PRICE INCREASE' if p>prev else 'NO PRICE CHANGE',
      'previous_price':prev,'drop_eur':round(prev-p,2),'drop_percent':round((prev-p)/prev*100,2),
      'low_7d':min(recent(7)),'low_30d':min(r30),'low_all':low,'high_all':max(all_prices),
      'average_30d':round(sum(r30)/len(r30),2) if span>=7 and len(r30)>=3 else None,
      'historical_low':len(rows)>=2 and span>=1 and p==low}
def normalize(product, offer, store, url, now, organizations=()):
    title=product.get('name','');model,storage,generation=identify(title)
    if not valid_url(url,store['domain']):raise ValueError('Invalid product URL')
    amount=price(offer.get('price'),offer.get('priceCurrency'))
    seller=offer.get('seller') or product.get('seller')
    seller=seller.get('name') if isinstance(seller,dict) else seller
    evidence='offer seller'
    if not seller and organizations:
        seller=organizations[0].get('name');evidence='same-domain retailer Organization on product page'
    if not seller:raise ValueError('Missing actual seller')
    condition=offer.get('itemCondition') or product.get('itemCondition') or ''
    state='new' if condition.endswith('/NewCondition') else 'unknown'
    if condition and state!='new':raise ValueError('Not a new device')
    availability=(offer.get('availability') or '').rsplit('/',1)[-1]
    available={'InStock':'in_stock','OutOfStock':'out_of_stock','PreOrder':'preorder','BackOrder':'backorder','Discontinued':'discontinued'}.get(availability,'unknown')
    identity=store['id']+'|'+urlparse(url).path+'|'+model+'|'+str(storage)+'|'+str(seller)
    reference=None
    specs=offer.get('priceSpecification',[]);specs=specs if isinstance(specs,list) else [specs]
    for spec in specs:
        if str(spec.get('priceType','')).endswith('StrikethroughPrice'):
            reference=price(spec.get('price'),spec.get('priceCurrency',offer.get('priceCurrency')))
    promotion=bool(reference and reference>amount)
    return {'id':hashlib.sha256(identity.encode()).hexdigest()[:24], 'configuration':model+'|'+str(storage),
      'model':model,'generation':generation,'storage_gb':storage,'colour':product.get('color'), 'title':title,
      'price':amount,'currency':'EUR','reference_price':reference,'advertised_discount_percent':round((reference-amount)/reference*100,2) if promotion else None,
      'store':store['id'],'seller':seller,'seller_evidence':evidence,'channel':store.get('channel','retail'),
      'url':url,'source_url':url,'availability':available,'condition':state,
      'promotion_start':None,'promotion_end':None,'advertised_promotion':promotion,
      'price_valid_until':offer.get('priceValidUntil'),
      'verified_at':now,'verification_status':'verified' if state=='new' else 'condition_unconfirmed',
      'stale':False,'eligible':state=='new' and available=='in_stock'}
def integrate(current, history, fresh, store_id, now, complete=False):
    merged={r['id']:dict(r,stale=True) if r['store']==store_id else dict(r) for r in current}
    existing={(r['id'],r['verified_at']) for r in history};drops=0
    for item in {r['id']:r for r in fresh}.values():
        old=merged.get(item['id']); prior=[r for r in history if r['id']==item['id']]
        if old and abs(item['price']/old['price']-1)>.40:
            merged[item['id']]=dict(old,stale=True,validation_warning='Price changed over 40%; manual verification required',suspected_price=item['price']);continue
        item=dict(item); item['history']=history_stats(prior,item,now)
        if item.get('advertised_promotion'):
            item['promotion_first_observed']=(old or {}).get('promotion_first_observed') or now
            item['promotion_active']=not item.get('promotion_end') or item['promotion_end']>=now[:10]
            item['promotion_disappeared_at']=None
        elif old and old.get('advertised_promotion'):
            item['promotion_first_observed']=old.get('promotion_first_observed')
            item['promotion_active']=False
            item['promotion_disappeared_at']=now
        else:
            item['promotion_first_observed']=(old or {}).get('promotion_first_observed')
            item['promotion_active']=False
            item['promotion_disappeared_at']=(old or {}).get('promotion_disappeared_at')
        # Preserve the last observed change; never reannounce a drop on unchanged observations.
        changed=not old or any(item.get(k)!=old.get(k) for k in ['price','availability','reference_price','promotion_start','promotion_end','advertised_promotion','condition'])
        if old and not changed:item['last_change']=old.get('last_change')
        elif old:item['last_change']={'at':now,'previous_price':old['price'],'price':item['price']}
        else:item['last_change']=None
        if item['history']['classification']=='NEW PRICE DROP':drops+=1
        if changed and (item['id'],now) not in existing:
            history.append({k:v for k,v in item.items() if k not in ('history','last_change','stale','eligible')});existing.add((item['id'],now))
        merged[item['id']]=item
    # Bounded/partial discovery never establishes that an unobserved product disappeared.
    if complete:
        seen={r['id'] for r in fresh}
        for ident,item in merged.items():
            if item['store']==store_id and ident not in seen:item.update(availability='unknown',stale=True,eligible=False)
    return list(merged.values()),history,drops
