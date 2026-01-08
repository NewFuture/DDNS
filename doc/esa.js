/**
 * 阿里云ESA边缘函数 - DDNS Release Proxy Script
 * Alibaba Cloud ESA Edge Function - DDNS Release Proxy
 * 
 * 功能说明 (Features):
 * - 统一格式代理: /releases/{version}/{binary_file}
 * - 版本可以是具体版本号(如 v4.1.3-beta1) 或 latest
 * - 具体版本: 无限缓存 | latest版本: 12小时缓存
 * - 流式传输: 直接返回响应流，无需等待完整下载（异步后台缓存）
 * 
 * Unified format: /releases/{version}/{binary_file}
 * - version can be specific version (e.g., v4.1.3-beta1) or "latest"
 * - Specific versions: infinite cache | latest: 12-hour cache
 * - Streaming: Returns response stream directly without buffering (async background caching)
 * 
 * 使用方法 (Usage):
 * 1. 在阿里云ESA控制台创建边缘函数
 * 2. 复制此代码到函数编辑器
 * 3. 配置路由规则匹配 /releases/*
 * 
 * 示例 (Examples):
 * - https://your-domain.com/releases/v4.1.3-beta1/ddns-windows-x64.exe
 * - https://your-domain.com/releases/latest/ddns-glibc-linux_amd64
 */

const GITHUB_REPO = 'NewFuture/DDNS';

/**
 * 主请求处理器 (Main request handler)
 */
addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request, event));
});

/**
 * 处理传入请求 (Handle incoming requests)
 * @param {Request} request - 传入的请求 (The incoming request)
 * @param {FetchEvent} event - 获取事件 (The fetch event)
 * @returns {Promise<Response>} 响应 (The response)
 */
async function handleRequest(request, event) {
  const url = new URL(request.url);
  const path = url.pathname;

  // 解析请求路径 (Parse the request path)
  // 格式: /releases/{version}/{binary_file}
  // version 可以是 v4.1.3-beta1 或 latest
  const match = path.match(/^\/releases\/([\w.-]+)\/([\w.-]+)$/);

  if (match) {
    const [, version, binaryFile] = match;
    return handleRelease(request, version, binaryFile, event);
  } else {
    return new Response('Not Found\n\nValid pattern:\n- /releases/{version}/{binary}\n  (version can be specific version or "latest")', {
      status: 404,
      headers: { 'Content-Type': 'text/plain' }
    });
  }
}

/**
 * 构建响应头 (Build response headers)
 * @param {Headers} originalHeaders - 原始响应头 (Original response headers)
 * @param {boolean} isLatest - 是否为latest版本 (Whether it's latest version)
 * @param {string} githubUrl - GitHub URL
 * @param {string} cacheStatus - 缓存状态 (Cache status: HIT or MISS)
 * @returns {Headers} 构建好的响应头 (Constructed response headers)
 */
function buildResponseHeaders(originalHeaders, isLatest, githubUrl, cacheStatus) {
  const headers = new Headers(originalHeaders);
  headers.set('X-Cache', cacheStatus);
  headers.set('X-Cache-Type', isLatest ? 'latest' : 'versioned');
  headers.set('X-GitHub-URL', githubUrl);
  
  if (isLatest) {
    headers.set('Cache-Control', 'public, max-age=43200');
    headers.set('X-Cache-Time', Date.now().toString());
  } else {
    headers.set('Cache-Control', 'public, max-age=31536000, immutable');
  }
  
  return headers;
}

/**
 * 处理发布请求 (Handle release requests)
 * @param {Request} request - 传入的请求 (The incoming request)
 * @param {string} version - 版本标签，可以是具体版本(如v4.1.3-beta1)或latest (Version tag, can be specific version or "latest")
 * @param {string} binaryFile - 二进制文件名 (Binary filename)
 * @param {FetchEvent} event - 获取事件 (The fetch event)
 * @returns {Promise<Response>} 响应 (The response)
 */
async function handleRelease(request, version, binaryFile, event) {
  const isLatest = version === 'latest';
  // 构建GitHub URL (Build GitHub URL)
  // 如果是latest: /releases/latest/download/{file}
  // 如果是版本号: /releases/download/{version}/{file}
  const githubUrl = isLatest 
    ? `https://github.com/${GITHUB_REPO}/releases/latest/download/${binaryFile}`
    : `https://github.com/${GITHUB_REPO}/releases/download/${version}/${binaryFile}`;
  const cacheKey = githubUrl;
  
  // 获取cache实例 (Get cache instance)
  const cache = caches.default;

  // 尝试从缓存获取 (Try to get from cache first)
  let response = await cache.match(cacheKey);
  
  if (response) {
    // 如果是latest版本，检查缓存是否仍然有效（12小时）
    // For latest version, check if cache is still valid (12 hours)
    if (isLatest) {
      const cacheTime = response.headers.get('X-Cache-Time');
      if (cacheTime) {
        const cacheAge = Date.now() - parseInt(cacheTime);
        const maxAge = 12 * 60 * 60 * 1000; // 12小时（毫秒）(12 hours in milliseconds)
        
        if (cacheAge >= maxAge) {
          // 缓存过期，重新获取 (Cache expired, refetch)
          response = null;
        }
      }
    }
    
    if (response) {
      // 返回缓存响应 (Return cached response)
      const headers = new Headers(response.headers);
      headers.set('X-Cache', 'HIT');
      headers.set('X-Cache-Type', isLatest ? 'latest' : 'versioned');
      
      // 如果是latest，添加Age头 (Add Age header for latest)
      if (isLatest) {
        const cacheTime = response.headers.get('X-Cache-Time');
        if (cacheTime) {
          const cacheAge = Date.now() - parseInt(cacheTime);
          headers.set('Age', Math.floor(cacheAge / 1000).toString());
        }
      }
      
      return new Response(response.body, {
        status: response.status,
        statusText: response.statusText,
        headers: headers
      });
    }
  }

  // 从GitHub获取 (Fetch from GitHub)
  response = await fetch(githubUrl, {
    redirect: 'follow'
  });

  if (!response.ok) {
    const status = response && typeof response.status === 'number' ? response.status : 502;
    const message = status === 404
      ? 'Release not found: ' + version + '/' + binaryFile
      : 'Error fetching release from GitHub (' + status + '): ' + version + '/' + binaryFile;
    return new Response(message, {
      status: status,
      headers: { 'Content-Type': 'text/plain' }
    });
  }

  // 克隆响应用于缓存（避免重复请求）(Clone response for caching to avoid duplicate requests)
  const responseToCache = response.clone();
  
  // 构建响应头 (Build response headers)
  const headers = buildResponseHeaders(response.headers, isLatest, githubUrl, 'MISS');
  
  // 直接返回响应流 (Return response stream directly)
  const streamResponse = new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers: headers
  });

  // 异步缓存响应（不阻塞流式传输）(Cache response asynchronously without blocking streaming)
  event.waitUntil(
    (async () => {
      try {
        const cacheHeaders = buildResponseHeaders(responseToCache.headers, isLatest, githubUrl, 'MISS');
        const responseToPut = new Response(responseToCache.body, {
          status: responseToCache.status,
          statusText: responseToCache.statusText,
          headers: cacheHeaders
        });
        await cache.put(cacheKey, responseToPut);
      } catch (err) {
        console.error('Cache error:', err);
      }
    })()
  );

  return streamResponse;
}
