import argparse,json,os,tempfile
from pathlib import Path
from tracker.core import utcnow,integrate
from tracker.http import Client
from tracker.adapters import ADAPTERS
ROOT=Path(__file__).resolve().parents[1]
def read(path,default):return json.loads(path.read_text(encoding='utf-8-sig')) if path.exists() else default
def write(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(dir=path.parent,suffix='.tmp')
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
def scan(data,mode='full',selected='',trigger='manual'):
    stores=read(data/'stores.json',[]);current=read(data/'current_prices.json',[]);history=read(data/'price_history.json',[]);previous=read(data/'run_status.json',{})
    now=utcnow();status={'started_at':now,'finished_at':None,'trigger':trigger,'mode':mode,'stores':{},'last_successful_scan':previous.get('last_successful_scan'),'new_price_reductions':0,'scope':'Enabled adapters only; partial market coverage'}
    chosen={s.strip() for s in selected.split(',') if s.strip()}
    if mode=='selected_stores' and (not chosen or chosen-set(ADAPTERS)):raise ValueError('Select enabled store IDs: '+', '.join(ADAPTERS))
    for store in stores:
        sid=store['id']
        if sid not in ADAPTERS:continue
        if mode=='retry_failed' and previous.get('stores',{}).get(sid,{}).get('status')=='success':continue
        if mode=='selected_stores' and sid not in chosen:continue
        try:
            fresh,report=ADAPTERS[sid](store,Client(store['domain'],delay=store.get('delay_seconds',2))).scan(now)
            if not fresh:raise ValueError('No valid product offers; adapter requires maintenance. '+str(report['errors'][:2]))
            current,history,drops=integrate(current,history,fresh,sid,now)
            # Page-level failures remain visible even when other products succeeded.
            report.update(status='partial' if report['errors'] else 'success',products_found=len(fresh),products_verified=sum(r['verification_status']=='verified' for r in fresh))
            status['stores'][sid]=report;status['new_price_reductions']+=drops
        except Exception as exc:
            current=[dict(r,stale=True,eligible=False) if r['store']==sid else r for r in current]
            status['stores'][sid]={'status':'failed','products_found':0,'products_verified':0,'errors':[{'error':type(exc).__name__+': '+str(exc)[:500]}]}
    status['finished_at']=utcnow();status['stores_checked']=len(status['stores'])
    status['successful_stores']=[sid for sid,r in status['stores'].items() if r['status']=='success']
    status['partial_stores']=[sid for sid,r in status['stores'].items() if r['status']=='partial']
    status['failed_stores']=[sid for sid,r in status['stores'].items() if r['status']=='failed']
    status['products_verified']=sum(r['products_verified'] for r in status['stores'].values())
    if status['successful_stores'] or status['partial_stores']:status['last_successful_scan']=status['finished_at']
    # Validate before writing any public data. History remains append-only.
    ids=[r['id'] for r in current]
    if len(ids)!=len(set(ids)) or any(r['currency']!='EUR' or r['price']<=0 for r in current):raise ValueError('Database integrity validation failed')
    if len(history)<len(read(data/'price_history.json',[])):raise ValueError('History truncation refused')
    write(data/'current_prices.json',current);write(data/'price_history.json',history);write(data/'run_status.json',status)
    print(json.dumps({k:v for k,v in status.items() if k!='stores'},indent=2));return status
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--mode',choices=['full','retry_failed','selected_stores'],default='full');p.add_argument('--stores',default='');p.add_argument('--trigger',default='manual');p.add_argument('--data-dir',type=Path,default=ROOT/'data');a=p.parse_args();scan(a.data_dir,a.mode,a.stores,a.trigger)
