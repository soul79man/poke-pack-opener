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
    # TCGCSV commonly stores numbers as 1/122, 001/122, TG01/TG30, etc.,
    # while the Pokémon TCG data used by the app normally stores just 1, 001,
    # or TG01. Store both the complete number and the part before '/' so the
    # cached price can match either representation.
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
def main():
    print('Downloading TCGCSV groups...');groups=get_json(f'{BASE}/groups')
    if isinstance(groups,dict):groups=groups.get('results') or groups.get('groups') or []
    # The cached card JSON uses set IDs (for example me4), while TCGCSV uses
    # human-readable group names (for example ME04: Chaos Rising). Build a
    # name -> official set ID map so prices can be looked up using either form.
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
            count=0
            for p in products or []:
                num=field(p,'Number')
                if not num:continue
                rows=[x for x in by_id.get(str(p.get('productId')),[]) if float(x.get('marketPrice') or 0)>0]
                if not rows:continue
                row=next((x for x in rows if 'holofoil' in str(x.get('subTypeName','')).lower()),None) or next((x for x in rows if str(x.get('subTypeName','')).lower()=='normal'),None) or rows[0]
                usd=float(row['marketPrice']);value={'gbp':round(usd*USD_TO_GBP,2),'usd':round(usd,2),'source':'TCGplayer market','updated':row.get('modifiedOn',''),'group':gname,'number':str(num),'productId':p.get('productId')}
                # TCGCSV often prefixes the official set name with a series label,
                # e.g. "ME04: Chaos Rising". The app uses the official set name,
                # so store both the full group key and the text after the final
                # colon to make the cached prices match reliably.
                names={norm(gname)}
                if ':' in str(gname):names.add(norm(str(gname).split(':')[-1]))
                # Also add the official Pokémon TCG set ID. The app's card
                # records do not contain a nested set.name, so it falls back
                # to selectedSetId (e.g. me4 for Chaos Rising).
                ids=set()
                for name in list(names):
                    if name in set_ids:ids.add(set_ids[name])
                names.update(ids)
                for name in names:
                    for number in card_numbers(num):
                        prices[f'{name}|{number}']=value
                count+=1
            meta.append({'id':gid,'name':gname,'cardsPriced':count});print(f'[{i}/{len(groups)}] {gname}: {count}')
        except Exception as e:print(f'ERROR {gname} ({gid}): {e}')
        time.sleep(.10)
    payload={'generatedAt':datetime.now(timezone.utc).isoformat(),'source':'TCGCSV / TCGplayer market','usdToGbp':USD_TO_GBP,'cardCount':len(prices),'groups':meta,'prices':prices}
    with open(OUT,'w',encoding='utf-8') as f:json.dump(payload,f,separators=(',',':'))
    print(f'Wrote {OUT} with {len(prices)} priced cards')
if __name__=='__main__':main()
