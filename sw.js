const CACHE='pokepack-shell-v101';
const ASSETS=['./','./index.html','./manifest.webmanifest','./icons/icon-192.png','./icons/icon-512.png'];
self.addEventListener('install',e=>e.waitUntil(caches.open(CACHE).then(c=>c.addAll(ASSETS)).then(()=>self.skipWaiting())));
self.addEventListener('activate',e=>e.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim())));
self.addEventListener('fetch',e=>{
  const u=new URL(e.request.url);
  if(u.hostname==='cdn.jsdelivr.net' && u.pathname.includes('/PokemonTCG/pokemon-tcg-data@master/sets/en.json')){
    e.respondWith(fetch(new URL('./pokemon-data/sets/en.json',self.location.origin))); return;
  }
  if(u.hostname==='cdn.jsdelivr.net' && u.pathname.includes('/PokemonTCG/pokemon-tcg-data@master/cards/en/')){
    const file=u.pathname.split('/').pop();
    e.respondWith(fetch(new URL('./pokemon-data/cards/en/'+file,self.location.origin))); return;
  }
  if(u.origin===location.origin){e.respondWith(caches.match(e.request).then(r=>r||fetch(e.request)));}
});
