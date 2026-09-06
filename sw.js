const CACHE='pokepack-shell-v101';
const ASSETS=['./','./index.html','./manifest.webmanifest','./icons/icon-192.png','./icons/icon-512.png'];
const UPSTREAM_PREFIX='/gh/PokemonTCG/pokemon-tcg-data@master/';

self.addEventListener('install',e=>e.waitUntil(caches.open(CACHE).then(c=>c.addAll(ASSETS)).then(()=>self.skipWaiting())));
self.addEventListener('activate',e=>e.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim())));

self.addEventListener('fetch',e=>{
  const u=new URL(e.request.url);

  // The app historically fetched card/set JSON from jsDelivr. Keep the
  // existing app code working, but serve those requests from our own
  // GitHub Pages copy instead. This removes the runtime dependency on
  // jsDelivr/PokemonTCG for the card database.
  if(u.hostname==='cdn.jsdelivr.net' && u.pathname.startsWith(UPSTREAM_PREFIX)){
    const localPath=u.pathname.slice(UPSTREAM_PREFIX.length);
    e.respondWith(fetch(new URL('./pokemon-data/'+localPath,self.location).href));
    return;
  }

  if(u.origin===location.origin){
    e.respondWith(caches.match(e.request).then(r=>r||fetch(e.request)));
  }
});
