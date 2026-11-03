import time
from urllib.request import Request,urlopen
from urllib.parse import urlparse,urljoin
from urllib.robotparser import RobotFileParser
from urllib.error import HTTPError

AGENT='iPhonePriceTrackerBG/1.0'
class Client:
    def __init__(self,domain,timeout=20,delay=2):
        self.domain=domain;self.timeout=timeout;self.delay=delay;self.last=0;self.cache={};self.robot=None;self.requests=0;self.blocked=False
    def _read(self,url):
        time.sleep(max(0,self.delay-(time.monotonic()-self.last)))
        req=Request(url,headers={'User-Agent':AGENT,'Accept':'text/html,application/json,application/xml'})
        self.last=time.monotonic();self.requests+=1
        try: response=urlopen(req,timeout=self.timeout)
        except HTTPError as exc:
            if exc.code in (403,429):self.blocked=True
            raise
        with response as r:
            if urlparse(r.url).hostname not in (self.domain,'www.'+self.domain):raise ValueError('Cross-domain redirect refused')
            data=r.read(5_000_001)
            if len(data)>5_000_000:raise ValueError('Response too large')
            return data.decode(r.headers.get_content_charset() or 'utf-8',errors='replace')
    def get(self,url):
        if self.blocked:raise PermissionError('Retailer stopped for this run after HTTP 403/429; no retries or bypass')
        p=urlparse(url)
        if p.scheme!='https' or p.hostname not in (self.domain,'www.'+self.domain) or p.username:raise ValueError('URL outside retailer allowlist')
        if url in self.cache:return self.cache[url]
        if self.robot is None:
            self.robot=RobotFileParser();self.robot.parse(self._read('https://'+self.domain+'/robots.txt').splitlines())
            self.delay=max(self.delay,self.robot.crawl_delay(AGENT) or self.robot.crawl_delay('*') or 0)
        if not self.robot.can_fetch(AGENT,url):raise PermissionError('Disallowed by robots.txt: '+p.path)
        result=self._read(url);self.cache[url]=result;return result
