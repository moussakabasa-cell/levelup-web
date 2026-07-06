// Service worker minimal — cache les fichiers statiques pour un chargement
// plus rapide au retour, mais ne bypass jamais le réseau pour les pages
// dynamiques (dashboard, parcours, etc.) qui doivent rester à jour.

const CACHE_NAME = 'levelup-v1';
const STATIC_ASSETS = [
  '/static/favicon.svg',
  '/static/icon-192.svg',
  '/static/icon-512.svg',
  '/static/manifest.json',
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(STATIC_ASSETS))
  );
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(names =>
      Promise.all(names.filter(n => n !== CACHE_NAME).map(n => caches.delete(n)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);
  // Ne cache QUE les statiques — le reste passe direct par le réseau
  if (url.pathname.startsWith('/static/')) {
    event.respondWith(
      caches.match(event.request).then(cached => cached || fetch(event.request))
    );
  }
});
