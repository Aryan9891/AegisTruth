// AegisTruth Sentinel Lightweight Offline Service Worker
const CACHE_NAME = "aegistruth-cache-v2.5";
const STATIC_ASSETS = [
  "./",
  "./index.html",
  "./css/style.css",
  "./favicon.svg",
  "./demo_thumbnail.jpg",
  "./manifest.json",
  "./js/client_engine.js?v=2.3",
  "./js/app.js?v=2.3",
  "./js/visual_lab.js?v=2.3",
  "./js/video_lab.js?v=2.3",
  "./js/audio_lab.js?v=2.3",
  "./js/text_lab.js?v=2.3",
  "./js/guard_lab.js?v=2.3",
  "./js/proxy_lab.js?v=2.3",
  "./js/report_export.js?v=2.3"
];

self.addEventListener("install", (e) => {
  e.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS).catch(() => {});
    })
  );
  self.skipWaiting();
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) return caches.delete(key);
        })
      );
    })
  );
  self.clients.claim();
});

self.addEventListener("fetch", (e) => {
  // Pass API requests directly to network, cache static assets
  if (e.request.url.includes("/api/")) {
    return;
  }
  e.respondWith(
    caches.match(e.request).then((cached) => {
      return cached || fetch(e.request).catch(() => cached);
    })
  );
});
