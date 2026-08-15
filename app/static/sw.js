/* ============================================================
   MyPersonal Bible - Service Worker (Offline Reading)
   Strategy:
     - Navigations & API: network-first, fall back to cache
       (so previously-read chapters & pages work offline)
     - Static assets (CDN css/js/fonts): cache-first
   Bump CACHE_VERSION when deploying a new version.
   ============================================================ */
const CACHE_VERSION = 'mpb-v7';
const RUNTIME_CACHE = CACHE_VERSION + '-runtime';
const STATIC_CACHE = CACHE_VERSION + '-static';

self.addEventListener('install', (event) => {
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((keys) =>
            Promise.all(
                keys
                    .filter((k) => k.startsWith('mpb-') && k !== RUNTIME_CACHE && k !== STATIC_CACHE)
                    .map((k) => caches.delete(k))
            )
        ).then(() => self.clients.claim())
    );
});

function isStaticAsset(url) {
    return (
        url.pathname.startsWith('/static/') ||
        url.hostname.includes('cdn.jsdelivr.net') ||
        url.hostname.includes('cdnjs.cloudflare.com') ||
        url.hostname.includes('fonts.googleapis.com') ||
        url.hostname.includes('fonts.gstatic.com')
    );
}

self.addEventListener('fetch', (event) => {
    const req = event.request;
    if (req.method !== 'GET') return;

    const url = new URL(req.url);

    // Never cache API.Bible / VoiceRSS proxy calls that hit third parties directly
    if (url.hostname !== self.location.hostname) {
        if (isStaticAsset(url)) {
            // Cache-first for CDN static assets
            event.respondWith(
                caches.open(STATIC_CACHE).then((cache) =>
                    cache.match(req).then(
                        (cached) =>
                            cached ||
                            fetch(req).then((res) => {
                                if (res && res.status === 200) {
                                    cache.put(req, res.clone());
                                }
                                return res;
                            })
                    )
                )
            );
        }
        return; // other cross-origin: browser default
    }

    // Same-origin: network-first with cache fallback
    event.respondWith(
        fetch(req)
            .then((res) => {
                if (res && res.status === 200) {
                    const cacheName = url.pathname.startsWith('/api/') ? RUNTIME_CACHE : RUNTIME_CACHE;
                    const clone = res.clone();
                    caches.open(cacheName).then((cache) => cache.put(req, clone));
                }
                return res;
            })
            .catch(() =>
                caches.match(req).then(
                    (cached) =>
                        cached ||
                        (req.mode === 'navigate'
                            ? caches.match('/offline')
                            : new Response('{"error":"You are offline"}', {
                                  status: 503,
                                  headers: { 'Content-Type': 'application/json' },
                              }))
                )
            )
    );
});

/* ============================================================
   Web Push - Daily Verse Reminders
   The server sends a JSON payload {title, body, url}. This shows
   the notification and opens the app when the user taps it.
   ============================================================ */

self.addEventListener('push', (event) => {
    let payload = { title: 'MyPersonal Bible', body: 'Your daily verse is waiting for you.', url: '/' };
    try {
        if (event.data) {
            const data = event.data.json();
            if (data && typeof data === 'object') payload = Object.assign(payload, data);
        }
    } catch (e) { /* non-JSON payload - use defaults */ }

    event.waitUntil(
        self.registration.showNotification(payload.title, {
            body: payload.body,
            icon: '/static/img/app-icon.jpg',
            badge: '/static/img/app-icon.jpg',
            tag: 'daily-verse',   // replaces yesterday's notification instead of stacking
            renotify: true,
            data: { url: payload.url || '/' },
        })
    );
});

self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    const target = (event.notification.data && event.notification.data.url) || '/';
    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true }).then((windowClients) => {
            // Reuse an open tab if one exists
            for (const client of windowClients) {
                if ('focus' in client) {
                    if (client.navigate) {
                        return client.navigate(target).then((c) => c.focus());
                    }
                    return client.focus();
                }
            }
            return clients.openWindow(target);
        })
    );
});
