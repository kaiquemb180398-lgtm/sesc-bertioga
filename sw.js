const V='sesc-bertioga-v4';
const CORE=['./','./index.html','./manifest.webmanifest','./icon-192.png','./icon-512.png','./apple-touch-icon.png'];
self.addEventListener('install',e=>{e.waitUntil(caches.open(V).then(c=>c.addAll(CORE)).then(()=>self.skipWaiting()))});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==V).map(k=>caches.delete(k)))).then(()=>self.clients.claim()))});
function timeout(ms){return new Promise((_,rej)=>setTimeout(()=>rej('timeout'),ms))}
function put(req,res){const cp=res.clone();caches.open(V).then(c=>c.put(req,cp));return res}
self.addEventListener('fetch',e=>{
  const r=e.request; if(r.method!=='GET') return;
  const u=new URL(r.url);
  if(u.origin===location.origin){
    if(r.mode==='navigate'){
      e.respondWith(Promise.race([fetch(r).then(res=>{if(res.ok){const cp=res.clone();caches.open(V).then(c=>c.put('./index.html',cp))}return res}),timeout(3500)])
        .catch(()=>caches.match('./index.html')));
      return;
    }
    e.respondWith(caches.match(r,{ignoreSearch:true}).then(m=>m||fetch(r).then(res=>put(r,res))));
    return;
  }
  if(u.hostname==='fonts.googleapis.com'||u.hostname==='fonts.gstatic.com'){
    e.respondWith(caches.match(r).then(m=>m||fetch(r).then(res=>put(r,res)).catch(()=>m)));
  }
});
