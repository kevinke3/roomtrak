const CACHE_NAME = 'roomtrack-tenant-v2';
const urlsToCache = [
    '/',
    '/static/css/style.css',
    '/static/manifest.json',
    '/tenant/dashboard',
    '/tenant/payments',
    '/tenant/maintenance'
];

self.addEventListener('install', function(event) {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(function(cache) {
                console.log('Opened cache');
                return cache.addAll(urlsToCache);
            })
    );
});

self.addEventListener('fetch', function(event) {
    event.respondWith(
        caches.match(event.request)
            .then(function(response) {
                // Return cached version or fetch from network
                if (response) {
                    return response;
                }
                return fetch(event.request);
            }
        )
    );
});

// Background sync for offline payments
self.addEventListener('sync', function(event) {
    if (event.tag === 'background-payment-sync') {
        event.waitUntil(doBackgroundSync());
    }
});

async function doBackgroundSync() {
    // Implement background sync for payments
    console.log('Background sync triggered');
}