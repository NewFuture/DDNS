/**
 * 阿里云ESA边缘函数 - DDNS Release Proxy Script
 * Alibaba Cloud ESA Edge Function - DDNS Release Proxy
 * 
 * 功能说明 (Features):
 * - 统一格式代理: /releases/{version}/{binary_file}
 * - 版本可以是具体版本号(如 v4.1.3-beta1)、latest 或 beta
 * - 具体版本: 无限缓存 | latest/beta: 12小时缓存
 * - 流式传输: 直接返回响应流，先缓存后返回
 * 
 * Unified format: /releases/{version}/{binary_file}
 * - version can be specific version (e.g., v4.1.3-beta1), "latest", or "beta"
 * - Specific versions: infinite cache | latest/beta: 12-hour cache
 * - Streaming: Returns response stream directly, cache first then return
 * 
 * 使用方法 (Usage):
 * 1. 在阿里云ESA控制台创建边缘函数
 * 2. 复制此代码到函数编辑器
 * 3. 配置路由规则匹配 /releases/*
 * 
 * 示例 (Examples):
 * - https://your-domain.com/releases/v4.1.3-beta1/ddns-windows-x64.exe
 * - https://your-domain.com/releases/latest/ddns-glibc-linux_amd64
 * - https://your-domain.com/releases/beta/ddns-glibc-linux_amd64
 */

const GITHUB_REPO = 'NewFuture/DDNS';

/**
 * 构建响应头 (Build response headers)
 * @param {Headers} originalHeaders - 原始响应头 (Original response headers)
 * @param {boolean} isDynamic - 是否为动态版本(latest/beta) (Whether it's a dynamic version like latest/beta)
 * @param {string} githubUrl - GitHub URL
 * @param {string} cacheStatus - 缓存状态 (Cache status: HIT or MISS)
 * @returns {Headers} 构建好的响应头 (Constructed response headers)
 */
function buildResponseHeaders(originalHeaders, isDynamic, githubUrl, cacheStatus) {
  const headers = new Headers(originalHeaders);
  headers.set('X-Cache', cacheStatus);
  headers.set('X-Cache-Type', isDynamic ? 'dynamic' : 'versioned');
  headers.set('X-GitHub-URL', githubUrl);
  
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
  // 判断是否为动态版本 (Check if it's a dynamic version)
  const isDynamic = version === 'latest' || version === 'beta';
  
  // 构建GitHub URL (Build GitHub URL)
  // latest: /releases/latest/download/{file}
  // beta: 获取最新带beta标签的release的文件
  // 版本号: /releases/download/{version}/{file}
  let githubUrl;
  if (version === 'latest') {
    githubUrl = `https://github.com/${GITHUB_REPO}/releases/latest/download/${binaryFile}`;
  } else if (version === 'beta') {
    // beta 使用 GitHub API 获取最新 prerelease
    // 暂时简化为直接重定向，由GitHub处理
    githubUrl = `https://github.com/${GITHUB_REPO}/releases/download/beta/${binaryFile}`;
  } else {
    githubUrl = `https://github.com/${GITHUB_REPO}/releases/download/${version}/${binaryFile}`;
  }
  
  const cacheKey = isDynamic ? `${version}:${binaryFile}` : githubUrl;
  
  // 尝试从缓存获取 (Try to get from cache first)
  // 阿里云ESA仅支持 cache.get() 和 cache.put() (Alibaba Cloud ESA only supports cache.get() and cache.put())
  let cachedResponse = await cache.get(cacheKey);
  
  // 有缓存直接返回，无需验证 (If cached, return directly without validation)
  if (cachedResponse) {
    const headers = new Headers(cachedResponse.headers);
    headers.set('X-Cache', 'HIT');
    return new Response(cachedResponse.body, {
      status: cachedResponse.status,
      statusText: cachedResponse.statusText,
      headers: headers
    });
  }

  // 从GitHub获取 (Fetch from GitHub)
  let response = await fetch(githubUrl, {
    redirect: 'follow'
  });

  if (!response.ok) {
    const status = response.status;
    const message = status === 404
      ? 'Release not found: ' + version + '/' + binaryFile
      : 'Error fetching release from GitHub (' + status + '): ' + version + '/' + binaryFile;
    return new Response(message, {
      status: status,
      headers: { 'Content-Type': 'text/plain' }
    });
  }

  // 构建响应头 (Build response headers)
  const headers = buildResponseHeaders(response.headers, isDynamic, githubUrl, 'MISS');
  
  // 创建最终响应 (Create final response)
  const finalResponse = new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers: headers
  });

  // 阿里云不支持event.waitUntil，先缓存再返回 (Aliyun doesn't support event.waitUntil, cache first then return)
  // 使用 .catch() 避免缓存失败影响响应 (Use .catch() to prevent cache failures from affecting response)
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

  // 解析请求路径 (Parse the request path)
  // 格式: /releases/{version}/{binary_file}
  // version 可以是 v4.1.3-beta1、latest 或 beta
  const match = path.match(/^\/releases\/([\w.-]+)\/([\w.-]+)$/);

  if (match) {
    const [, version, binaryFile] = match;
    return handleRelease(version, binaryFile);
  } else {
    return new Response('Not Found\n\nValid pattern:\n- /releases/{version}/{binary}\n  (version can be specific version, "latest", or "beta")', {
      status: 404,
      headers: { 'Content-Type': 'text/plain' }
    });
  }
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
