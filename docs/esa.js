/**
 * 阿里云ESA边缘函数 - DDNS Release Proxy Script
 * Alibaba Cloud ESA Edge Function - DDNS Release Proxy
 * 
 * 功能说明 (Features):
 * - 统一格式代理: /releases/{version}/{binary_file}
 * - 版本可以是具体版本号(如 v4.1.3-beta1)、latest 或 beta
 * - 具体版本: 无限缓存 | latest: 12小时缓存 | beta: 转换为具体版本后无限缓存
 * - 流式传输: 直接返回响应流，先缓存后返回
 * 
 * Unified format: /releases/{version}/{binary_file}
 * - version can be specific version (e.g., v4.1.3-beta1), "latest", or "beta"
 * - Specific versions: infinite cache | latest: 12-hour cache | beta: infinite cache after conversion to specific version
 * - Streaming: Returns response stream directly, cache first then return
 * 
 * 使用方法 (Usage):
 * 1. 在阿里云ESA控制台创建边缘函数
 * 2. 复制此代码到函数编辑器
 * 3. 配置路由规则匹配 /releases/*
 * 4. 创建EdgeKV命名空间用于存储beta版本映射
 * 
 * 示例 (Examples):
 * - https://your-domain.com/releases/v4.1.3-beta1/ddns-windows-x64.exe
 * - https://your-domain.com/releases/latest/ddns-glibc-linux_amd64
 * - https://your-domain.com/releases/beta/ddns-glibc-linux_amd64
 */

const GITHUB_REPO = 'NewFuture/DDNS';
const edgeKv = new EdgeKV({ namespace: 'ddns-releases' });

/**
 * 获取最新beta版本 (Get latest beta version)
 * @returns {Promise<string>} beta版本号 (Beta version number)
 */
async function getLatestBetaVersion() {
  // 尝试从EdgeKV获取缓存的beta版本 (Try to get cached beta version from EdgeKV)
  const cacheKey = 'ddns-beta-version';
  try {
    const cachedVersion = await edgeKv.get(cacheKey);
    if (cachedVersion) {
      return cachedVersion;
    }
  } catch (err) {
    console.log('EdgeKV get error:', err);
  }

  // 从GitHub API获取最新的beta版本 (Fetch latest beta version from GitHub API)
  const apiUrl = `https://api.github.com/repos/${GITHUB_REPO}/releases`;
  const apiResponse = await fetch(apiUrl, {
    headers: {
      'Accept': 'application/vnd.github.v3+json',
      'User-Agent': 'ESA-Edge-Function'
    }
  });

  if (apiResponse.ok) {
    const releases = await apiResponse.json();
    // 查找第一个prerelease或tag_name包含beta的release (Find first prerelease or release with beta in tag_name)
    for (const release of releases) {
      if ((release.prerelease || (release.tag_name && release.tag_name.includes('beta'))) && release.tag_name) {
        // 缓存到EdgeKV，6小时过期 (Cache to EdgeKV, 6-hour expiration)
        try {
          await edgeKv.put(cacheKey, release.tag_name, { expiration_ttl: 21600 });
        } catch (err) {
          console.log('EdgeKV put error:', err);
        }
        return release.tag_name;
      }
    }
  }

  // 如果没找到beta版本，返回null (If no beta version found, return null)
  return null;
}

/**
 * 构建响应头 (Build response headers)
 * @param {Headers} originalHeaders - 原始响应头 (Original response headers)
 * @param {boolean} isDynamic - 是否为动态版本(latest/beta) (Whether it's a dynamic version)
 * @param {string} githubUrl - GitHub URL
 * @returns {Headers} 构建好的响应头 (Constructed response headers)
 */
function buildResponseHeaders(originalHeaders, isDynamic, githubUrl) {
  const headers = new Headers(originalHeaders);
  headers.set('X-GitHub-URL', githubUrl);
  
  // 动态版本12小时缓存，静态版本永久缓存 (Dynamic versions: 12h cache, static versions: permanent cache)
  if (isDynamic) {
    headers.set('Cache-Control', 'public, max-age=43200');
  } else {
    headers.set('Cache-Control', 'public, max-age=31536000, immutable');
  }
  
  return headers;
}

/**
 * 处理发布请求 (Handle release requests)
 * @param {string} version - 版本标签，可以是具体版本(如v4.1.3-beta1)、latest或beta (Version tag, can be specific version, "latest", or "beta")
 * @param {string} binaryFile - 二进制文件名 (Binary filename)
 * @returns {Promise<Response>} 响应 (The response)
 */
async function handleRelease(version, binaryFile) {
  // 构建GitHub URL (Build GitHub URL)
  let githubUrl;
  let isDynamic = false;
  
  if (version === 'latest') {
    // latest使用GitHub的latest重定向，动态版本 (latest uses GitHub's latest redirect, dynamic version)
    githubUrl = `https://github.com/${GITHUB_REPO}/releases/latest/download/${binaryFile}`;
    isDynamic = true;
  } else if (version === 'beta') {
    // 获取最新beta版本号，转换为具体版本 (Get latest beta version number, convert to specific version)
    const betaVersion = await getLatestBetaVersion();
    if (!betaVersion) {
      return new Response('Beta release not found', { status: 404, headers: { 'Content-Type': 'text/plain' } });
    }
    // beta已转换为具体版本，按静态版本处理 (Beta converted to specific version, treat as static)
    githubUrl = `https://github.com/${GITHUB_REPO}/releases/download/${betaVersion}/${binaryFile}`;
  } else {
    // 具体版本号，静态版本 (Specific version, static)
    githubUrl = `https://github.com/${GITHUB_REPO}/releases/download/${version}/${binaryFile}`;
  }
  
  // 缓存key使用HTTP协议(ESA Cache引擎要求) (Cache key uses HTTP protocol, required by ESA Cache engine)
  const cacheKey = githubUrl.replace('https://', 'http://');
  
  // 尝试从缓存获取 (Try to get from cache first)
  const cachedResponse = await cache.get(cacheKey);
  if (cachedResponse) {
    return cachedResponse;
  }

  // 从GitHub获取 (Fetch from GitHub)
  const response = await fetch(githubUrl, { redirect: 'follow' });
  if (!response.ok) {
    return response;
  }

  // 构建响应头 (Build response headers)
  const headers = buildResponseHeaders(response.headers, isDynamic, githubUrl);
  
  // 创建最终响应 (Create final response)
  const finalResponse = new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers: headers
  });

  // 先缓存再返回 (Cache first then return)
  cache.put(cacheKey, finalResponse.clone()).catch(err => {
    console.error('Cache error:', err);
  });

  return finalResponse;
}

/**
 * 处理传入请求 (Handle incoming requests)
 * @param {Request} request - 传入的请求 (The incoming request)
 * @returns {Promise<Response>} 响应 (The response)
 */
async function handleRequest(request) {
  const url = new URL(request.url);
  const path = url.pathname;

  // Handle redirects for old /doc/ URLs
  // Redirect /index.en.html to /en/
  if (path === '/index.en.html') {
    return Response.redirect(url.origin + '/en/' + url.search + url.hash, 301);
  }
  
  // Redirect /doc/xxx.en.html to /en/xxx.html (must be before /doc/ redirect)
  const enHtmlMatch = path.match(/^\/doc\/(.+)\.en\.html$/);
  if (enHtmlMatch) {
    const pagePath = enHtmlMatch[1];
    return Response.redirect(url.origin + `/en/${pagePath}.html` + url.search + url.hash, 301);
  }
  
  // Redirect /doc/xxx to /xxx (301 permanent redirect)
  if (path.startsWith('/doc/')) {
    const newPath = path.replace('/doc/', '/');
    return Response.redirect(url.origin + newPath + url.search + url.hash, 301);
  }

  // 解析请求路径 (Parse the request path)
  // 格式: /releases/{version}/{binary_file}
  // version 可以是 v4.1.3-beta1、latest 或 beta
  const match = path.match(/^\/releases\/([\w.-]+)\/([\w.-]+)$/);

  if (match) {
    const [, version, binaryFile] = match;
    return handleRelease(version, binaryFile);
  }
  
  // No match found - return 404.html page (avoid infinite loop by not fetching if already requesting 404.html)
  // 未匹配任何URL模式 - 返回404.html页面（避免无限循环，如果已经在请求404.html则不再获取）
  if (path !== '/404.html') {
    // 缓存key使用HTTP协议 (Cache key uses HTTP protocol)
    const notFoundUrl = 'http://ddns.newfuture.cc/404.html';
    
    // 尝试从缓存获取 (Try to get from cache first)
    const cachedResponse = await cache.get(notFoundUrl);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    try {
      const notFoundResponse = await fetch(notFoundUrl, { redirect: 'follow' });
      
      if (notFoundResponse.ok) {
        // Return 404.html with 404 status code and appropriate headers
        const headers = new Headers();
        // Ensure correct content type for HTML 404 page
        headers.set('Content-Type', 'text/html; charset=utf-8');
        headers.set('Cache-Control', 'public, max-age=21600'); // Cache 404 page for 6 hours
        
        const finalResponse = new Response(notFoundResponse.body, {
          status: 404,
          statusText: 'Not Found',
          headers: headers
        });
        
        // 先缓存再返回 (Cache first then return)
        cache.put(notFoundUrl, finalResponse.clone()).catch(err => {
          console.log(`Failed to cache 404 response for ${notFoundUrl}:`, err);
        });
        
        return finalResponse;
      }
    } catch (err) {
      console.log('Failed to fetch 404.html:', err);
    }
  }
  
  // Fallback if 404.html is not available
  return new Response('Not Found', {
    status: 404,
    headers: { 'Content-Type': 'text/plain' }
  });
}

/**
 * ES模块导出格式 (ES Module export format)
 * 阿里云ESA要求导出包含fetch函数的对象 (Alibaba Cloud ESA requires exporting an object with a fetch function)
 */
export default {
  async fetch(request, env, ctx) {
    return handleRequest(request);
  }
};
