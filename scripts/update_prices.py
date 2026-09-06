import json, time, urllib.request, re
from datetime import datetime, timezone
BASE='https://tcgcsv.com/tcgplayer/3'; OUT='prices.json'; USD_TO_GBP=0.74; UA='PokePackOpener-PriceUpdater/1.0 (GitHub Actions)'
def get_json(url):
    req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'application/json'})
    with urllib.request.urlopen(req,timeout=60) as r:return json.load(r)
def norm(s):
    s=str(s or '').lower().replace('&','and');s=re.sub(r'^[a-z]{1,5}\s*\d{1,3}\s*:\s*','',s);s=re.sub(r'[^a-z0-9]+',' ',s).strip();return re.sub(r'\s+',' ',s)
def card_numbers(n):
    s=str(n or '').strip().replace(' ','').lower()
    if not s:return []
    values=[]
    def add(v):
        if v and v not in values:values.append(v)
    m=re.match(r'^(\d+)\/(\d+)$',s)
    if m:
        add(f'{int(m.group(1))}/{int(m.group(2))}')
        add(str(int(m.group(1))))
        return values
    if '/' in s:
        add(s)
        add(s.split('/',1)[0])
        return values
    if s.isdigit():
        add(str(int(s)))
        return values
    add(s)
    return values
def field(product,name):
    for x in product.get('extendedData') or []:
        if str(x.get('name','')).lower()==name.lower():return x.get('value')
    return None
def number_from_name(name):
    s=str(name or '')
    m=re.search(r'(?:#\s*)?(\d{1,3})\s*/\s*(\d{2,3})\b',s)
    return m.group(1)+'/'+m.group(2) if m else None
def choose_price(rows):
    # Prefer TCGplayer market price. If market price is unavailable, use the
    # median listing price, then the lowest listing price. TCGCSV notes that
    # marketPrice can be null for cards with low sales volume, while midPrice
    # and lowPrice may still be available.
    usable=[x for x in rows if isinstance(x,dict)]
    for label,key in [('TCGplayer market','marketPrice'),('TCGplayer median','midPrice'),('TCGplayer low listing','lowPrice')]:
        candidates=[]
        for x in usable:
            try:
                v=float(x.get(key) or 0)
            except Exception:
                v=0
            if v>0:candidates.append((x,v))
        if candidates:
            # Prefer holofoil, then normal, then reverse holofoil, then any
            # other positive printing.
            preferred=next((z for z in candidates if 'holofoil' in str(z[0].get('subTypeName','')).lower() and 'reverse' not in str(z[0].get('subTypeName','')).lower()),None)
            preferred=preferred or next((z for z in candidates if str(z[0].get('subTypeName','')).lower()=='normal'),None)
            preferred=preferred or next((z for z in candidates if 'reverse holofoil' in str(z[0].get('subTypeName','')).lower()),None)
            return preferred[0],preferred[1],label
    return None,None,None
def main():
    print('Downloading TCGCSV groups...');groups=get_json(f'{BASE}/groups')
    if isinstance(groups,dict):groups=groups.get('results') or groups.get('groups') or []
    set_ids={}
    try:
        with open('pokemon-data/sets/en.json',encoding='utf-8') as f:
            for s in json.load(f):
                if s.get('name') and s.get('id'):set_ids[norm(s['name'])]=str(s['id']).lower()
    except Exception as e:
        print(f'WARNING could not load local set IDs: {e}')
    print(f'Found {len(groups)} groups; mapped {len(set_ids)} local set IDs')
    prices={};meta=[]
    for i,g in enumerate(groups,1):
        gid=g.get('groupId');gname=g.get('name','')
        if not gid or not gname:continue
        try:
            products=get_json(f'{BASE}/{gid}/products'); products=products.get('results') if isinstance(products,dict) else products
            prices_raw=get_json(f'{BASE}/{gid}/prices'); prices_raw=prices_raw.get('results') if isinstance(prices_raw,dict) else prices_raw
            by_id={}
            for x in prices_raw or []:by_id.setdefault(str(x.get('productId')),[]).append(x)
            count=0; market_count=0; fallback_count=0
            for p in products or []:
                num=field(p,'Number') or number_from_name(p.get('name'))
                if not num:continue
                row,usd,price_source=choose_price(by_id.get(str(p.get('productId')),[]))
                if not row:continue
                if price_source=='TCGplayer market':market_count+=1
                else:fallback_count+=1
                value={'gbp':round(usd*USD_TO_GBP,2),'usd':round(usd,2),'source':price_source,'updated':row.get('modifiedOn',''),'group':gname,'number':str(num),'productId':p.get('productId')}
                names={norm(gname)}
                if ':' in str(gname):names.add(norm(str(gname).split(':')[-1]))
                ids=set()
                for name in list(names):
                    if name in set_ids:ids.add(set_ids[name])
                names.update(ids)
                for name in names:
                    for number in card_numbers(num):prices[f'{name}|{number}']=value
                count+=1
            meta.append({'id':gid,'name':gname,'cardsPriced':count,'marketPrices':market_count,'fallbackPrices':fallback_count});print(f'[{i}/{len(groups)}] {gname}: {count} ({market_count} market, {fallback_count} fallback)')
        except Exception as e:print(f'ERROR {gname} ({gid}): {e}')
        time.sleep(.10)
    payload={'generatedAt':datetime.now(timezone.utc).isoformat(),'source':'TCGCSV / TCGplayer','usdToGbp':USD_TO_GBP,'cardCount':len(prices),'groups':meta,'prices':prices}
    with open(OUT,'w',encoding='utf-8') as f:json.dump(payload,f,separators=(',',':'))
    print(f'Wrote {OUT} with {len(prices)} priced cards')
if __name__=='__main__':main()
