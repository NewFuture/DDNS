/**
 * DDNS Release Proxy Script for Edge Computing (Cloudflare Workers/ESA)
 * 
 * This script proxies GitHub release downloads with intelligent caching:
 * - Versioned releases: /releases/v4.1.3-beta1/ddns.exe -> GitHub release with infinite cache
 * - Latest releases: /latest/ddns.exe -> Latest GitHub release with 12-hour cache
 * 
 * Usage:
 * - Deploy to Cloudflare Workers or compatible edge platform
 * - Configure route patterns to match /releases/* and /latest/*
 * 
 * Example URLs:
 * - https://your-domain.com/releases/v4.1.3-beta1/ddns-windows-x64.exe
 * - https://your-domain.com/latest/ddns-glibc-linux_amd64
 */

const GITHUB_REPO = 'NewFuture/DDNS';
const CACHE_NAME = 'ddns-releases';

/**
 * Main request handler
 */
addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request, event));
});

/**
 * Handle incoming requests
 * @param {Request} request - The incoming request
 * @param {FetchEvent} event - The fetch event
 * @returns {Promise<Response>} The response
 */
async function handleRequest(request, event) {
  const url = new URL(request.url);
  const path = url.pathname;

  // Parse the request path
  // Pattern 1: /releases/{version}/{binary_file}
  const versionMatch = path.match(/^\/releases\/(v[\w.-]+)\/([\w.-]+)$/);
  
  // Pattern 2: /latest/{binary_file}
  const latestMatch = path.match(/^\/latest\/([\w.-]+)$/);

  if (versionMatch) {
    const [, version, binaryFile] = versionMatch;
    return handleVersionedRelease(request, version, binaryFile, event);
  } else if (latestMatch) {
    const [, binaryFile] = latestMatch;
    return handleLatestRelease(request, binaryFile, event);
  } else {
    return new Response('Not Found\n\nValid patterns:\n- /releases/{version}/{binary}\n- /latest/{binary}', {
      status: 404,
      headers: { 'Content-Type': 'text/plain' }
    });
  }
}

/**
 * Handle versioned release requests with infinite cache
 * @param {Request} request - The incoming request
 * @param {string} version - Version tag (e.g., v4.1.3-beta1)
 * @param {string} binaryFile - Binary filename
 * @param {FetchEvent} event - The fetch event
 * @returns {Promise<Response>} The response
 */
async function handleVersionedRelease(request, version, binaryFile, event) {
  const githubUrl = `https://github.com/${GITHUB_REPO}/releases/download/${version}/${binaryFile}`;
  const cacheKey = new Request(githubUrl, request);
  const cache = caches.default;

  // Try to get from cache first
  let response = await cache.match(cacheKey);
  
  if (response) {
    // Return cached response
    return new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers: new Headers({
        ...Object.fromEntries(response.headers),
        'X-Cache': 'HIT',
        'X-Cache-Type': 'versioned'
      })
    });
  }

  // Fetch from GitHub
  response = await fetch(githubUrl, {
    redirect: 'follow'
  });

  if (!response.ok) {
    return new Response(`Release not found: ${version}/${binaryFile}`, {
      status: 404,
      headers: { 'Content-Type': 'text/plain' }
    });
  }

  // Clone the response for caching
  const responseToCache = response.clone();
  
  // Create a new response with cache headers for infinite cache
  const cachedResponse = new Response(responseToCache.body, {
    status: responseToCache.status,
    statusText: responseToCache.statusText,
    headers: new Headers({
      ...Object.fromEntries(responseToCache.headers),
      'Cache-Control': 'public, max-age=31536000, immutable', // 1 year cache (effectively infinite)
      'X-Cache': 'MISS',
      'X-Cache-Type': 'versioned',
      'X-GitHub-URL': githubUrl
    })
  });

  // Store in cache (versioned releases are immutable)
  event.waitUntil(cache.put(cacheKey, cachedResponse.clone()));

  return cachedResponse;
}

/**
 * Handle latest release requests with 12-hour cache
 * @param {Request} request - The incoming request
 * @param {string} binaryFile - Binary filename
 * @param {FetchEvent} event - The fetch event
 * @returns {Promise<Response>} The response
 */
async function handleLatestRelease(request, binaryFile, event) {
  const githubUrl = `https://github.com/${GITHUB_REPO}/releases/latest/download/${binaryFile}`;
  const cacheKey = new Request(githubUrl, request);
  const cache = caches.default;

  // Try to get from cache first
  let response = await cache.match(cacheKey);
  
  if (response) {
    // Check if cache is still valid (12 hours)
    const cacheTime = response.headers.get('X-Cache-Time');
    if (cacheTime) {
      const cacheAge = Date.now() - parseInt(cacheTime);
      const maxAge = 12 * 60 * 60 * 1000; // 12 hours in milliseconds
      
      if (cacheAge < maxAge) {
        // Return cached response
        return new Response(response.body, {
          status: response.status,
          statusText: response.statusText,
          headers: new Headers({
            ...Object.fromEntries(response.headers),
            'X-Cache': 'HIT',
            'X-Cache-Type': 'latest',
            'Age': Math.floor(cacheAge / 1000).toString()
          })
        });
      }
    }
  }

  // Fetch from GitHub
  response = await fetch(githubUrl, {
    redirect: 'follow'
  });

  if (!response.ok) {
    return new Response(`Latest release not found: ${binaryFile}`, {
      status: 404,
      headers: { 'Content-Type': 'text/plain' }
    });
  }

  // Clone the response for caching
  const responseToCache = response.clone();
  
  // Create a new response with cache headers for 12-hour cache
  const cachedResponse = new Response(responseToCache.body, {
    status: responseToCache.status,
    statusText: responseToCache.statusText,
    headers: new Headers({
      ...Object.fromEntries(responseToCache.headers),
      'Cache-Control': 'public, max-age=43200', // 12 hours
      'X-Cache': 'MISS',
      'X-Cache-Type': 'latest',
      'X-Cache-Time': Date.now().toString(),
      'X-GitHub-URL': githubUrl
    })
  });

  // Store in cache
  event.waitUntil(cache.put(cacheKey, cachedResponse.clone()));

  return cachedResponse;
}
