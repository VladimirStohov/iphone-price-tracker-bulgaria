from urllib.parse import urljoin,urlparse
from tracker.core import Page,walk,identify,normalize

class StructuredAdapter:
    def __init__(self,store,client):self.store=store;self.client=client
    def scan(self,now):
        candidates=set(self.store.get('seeds',[]));errors=[];found=[]
        for listing in self.store['listings']:
            try:
                page=Page(self.client.get(listing))
                for href in page.links:
                    url=urljoin(listing,href).split('#')[0].split('?')[0]
                    if urlparse(url).hostname not in (self.store['domain'],'www.'+self.store['domain']):continue
                    if not self.product_path(url):continue
                    if 'iphone' not in url.lower():continue
                    candidates.add(url)
            except Exception as exc:errors.append({'url':listing,'error':type(exc).__name__+': '+str(exc)[:160]})
        # Prefer each supported model before filling remaining slots with colour variants.
        def model_key(url):
            import re
            m=re.search(r'iphone-(?:1[567](?:-pro-max|-pro|-plus)?|air)',url)
            return m[0] if m else 'zz'
        buckets={}
        for url in sorted(candidates):buckets.setdefault(model_key(url),[]).append(url)
        queue=[]
        while any(buckets.values()):
            for bucket in buckets.values():
                if bucket:queue.append(bucket.pop(0))
        limit=self.store.get('max_products',36);skipped=0
        for url in queue[:limit]:
            try:
                page=Page(self.client.get(url));objects=[o for blob in page.jsons for o in walk(blob)]
                organizations=[o for o in objects if o.get('@type')=='Organization' and urlparse(o.get('url','')).hostname in (self.store['domain'],'www.'+self.store['domain'])]
                products=[o for o in objects if o.get('@type') in ('Product','ProductGroup')]
                count_before=len(found)
                for p in products:
                    try:identify(p.get('name',''))
                    except ValueError:continue
                    offers=p.get('offers',[]);offers=offers if isinstance(offers,list) else [offers]
                    # Prefer richer explicit condition evidence for otherwise identical offers.
                    for offer in offers:
                        if offer.get('@type')=='AggregateOffer':continue
                        offer_url=urljoin(url,offer.get('url') or p.get('url') or url)
                        try:found.append(normalize(p,offer,self.store,offer_url,now,organizations))
                        except ValueError as exc:errors.append({'url':url,'error':str(exc)})
                if len(found)==count_before:skipped+=1
            except Exception as exc:errors.append({'url':url,'error':type(exc).__name__+': '+str(exc)[:160]})
        unique={}
        for row in found:
            key=row['id']
            if key not in unique or row['condition']=='new':unique[key]=row
        return list(unique.values()),{'errors':errors,'discovered':len(candidates),'attempted':min(len(queue),limit),'skipped':skipped,'coverage':'bounded discovery; not all store inventory','requests':self.client.requests}
