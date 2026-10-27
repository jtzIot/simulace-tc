// Service Worker for Offline PWA Support
const CACHE_NAME = 'simulace-tc-20261027-v11';
const ASSETS = [
  './',
  './index.html',
  './tailwindcss.min.js',
  './manifest.json',
  './icon-192.png',
  './icon-512.png'
];

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS))
  );
  self.skipWaiting();
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k.startsWith('simulace-') && k !== CACHE_NAME).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', (e) => {
  // If requesting Open-Meteo online API, fetch network first
  if (e.request.url.includes('open-meteo.com')) {
    e.respondWith(
      fetch(e.request).catch(() => new Response(JSON.stringify({ error: 'offline' }), {
        headers: { 'Content-Type': 'application/json' }
      }))
    );
    return;
  }
  // All other app assets: Cache first
  e.respondWith(
    caches.match(e.request).then((res) => res || fetch(e.request))
  );
});
