import json, time, urllib.request, re
from datetime import datetime, timezone
BASE='https://tcgcsv.com/tcgplayer/3'; OUT='prices.json'; USD_TO_GBP=0.74; UA='PokePackOpener-PriceUpdater/1.0 (GitHub Actions)'
def get_json(url):
    req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'application/json'})
    with urllib.request.urlopen(req,timeout=60) as r:return json.load(r)
def norm(s):
    s=str(s or '').lower().replace('&','and');s=re.sub(r'^[a-z]{1,5}\s*\d{1,3}\s*:\s*','',s);s=re.sub(r'[^a-z0-9]+',' ',s).strip();return re.sub(r'\s+',' ',s)
def card_number(n):
    s=str(n or '').strip().replace(' ','');m=re.match(r'^(\d+)\/(\d+)$',s);return f'{int(m.group(1))}/{int(m.group(2))}' if m else s.lower()
def field(product,name):
    for x in product.get('extendedData') or []:
        if str(x.get('name','')).lower()==name.lower():return x.get('value')
    return None
def main():
    print('Downloading TCGCSV groups...');groups=get_json(f'{BASE}/groups')
    if isinstance(groups,dict):groups=groups.get('results') or groups.get('groups') or []
    print(f'Found {len(groups)} groups');prices={};meta=[]
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
                usd=float(row['marketPrice']);key=norm(gname)+'|'+card_number(num)
                prices[key]={'gbp':round(usd*USD_TO_GBP,2),'usd':round(usd,2),'source':'TCGplayer market','updated':row.get('modifiedOn',''),'group':gname,'number':card_number(num),'productId':p.get('productId')};count+=1
            meta.append({'id':gid,'name':gname,'cardsPriced':count});print(f'[{i}/{len(groups)}] {gname}: {count}')
        except Exception as e:print(f'ERROR {gname} ({gid}): {e}')
        time.sleep(.10)
    payload={'generatedAt':datetime.now(timezone.utc).isoformat(),'source':'TCGCSV / TCGplayer market','usdToGbp':USD_TO_GBP,'cardCount':len(prices),'groups':meta,'prices':prices}
    with open(OUT,'w',encoding='utf-8') as f:json.dump(payload,f,separators=(',',':'))
    print(f'Wrote {OUT} with {len(prices)} priced cards')
if __name__=='__main__':main()
# Trigger the existing data-refresh workflow so the cache is regenerated after setup changes.
