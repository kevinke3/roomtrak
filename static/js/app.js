// PWA Service Worker
const CACHE_NAME = 'roomtrack-v1';
const urlsToCache = [
    '/',
    '/static/css/style.css',
    '/static/js/app.js'
];

self.addEventListener('install', function(event) {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(function(cache) {
                return cache.addAll(urlsToCache);
            })
    );
});

self.addEventListener('fetch', function(event) {
    event.respondWith(
        caches.match(event.request)
            .then(function(response) {
                if (response) {
                    return response;
                }
                return fetch(event.request);
            }
        )
    );
});

// Notification System
function showNotification(title, message) {
    if ('Notification' in window && Notification.permission === 'granted') {
        new Notification(title, {
            body: message,
            icon: '/static/images/icon.png'
        });
    }
}

// Request notification permission
if ('Notification' in window) {
    Notification.requestPermission();
}