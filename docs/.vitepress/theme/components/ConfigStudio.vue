<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useData, withBase } from 'vitepress'

type AuthMode = 'none' | 'token' | 'id-token' | 'flexible' | 'callback'
type Severity = 'error' | 'warning'
type SectionKey = 'provider' | 'records' | 'network' | 'runtime'
type InspectorTab = 'preview' | 'validate'
type CacheMode = 'inherit' | 'true' | 'false' | 'path'
type SslMode = 'inherit' | 'auto' | 'true' | 'false' | 'custom'
type LogLevel = string | number
type JsonValue = string | number | boolean | null | JsonObject | JsonValue[]

interface JsonObject {
  [key: string]: JsonValue
}

interface Diagnostic {
  path: string
  message: string
  recovery?: string
  severity: Severity
}

interface ProviderMeta {
  value: string
  name: string
  docs: string
  auth: AuthMode
  testOnly?: boolean
  descriptionZh: string
  descriptionEn: string
  idLabelZh: string
  idLabelEn: string
  tokenLabelZh: string
  tokenLabelEn: string
}

interface ProviderState {
  uid: number
  provider: string
  id: string
  idPresent: boolean
  idNull: boolean
  token: string
  tokenPresent: boolean
  endpoint: string
  endpointPresent: boolean
  endpointNull: boolean
  ipv4Text: string
  ipv4Present: boolean
  ipv6Text: string
  ipv6Present: boolean
  index4Text: string
  index6Text: string
  ttl: string
  ttlNull: boolean
  line: string
  linePresent: boolean
  lineNull: boolean
  proxyText: string
  proxyPresent: boolean
  sslMode: SslMode
  sslPath: string
  cacheMode: CacheMode
  cachePath: string
  cacheMaxAge: string
  logLevel: LogLevel
  extraText: string
  revealToken: boolean
}

interface GlobalState {
  proxyText: string
  proxyPresent: boolean
  sslMode: SslMode
  sslPath: string
  cacheMode: CacheMode
  cachePath: string
  cacheMaxAge: string
  logLevel: LogLevel
  logFile: string
  logFilePresent: boolean
  logFileNull: boolean
  logFormat: string
  logFormatPresent: boolean
  logFormatNull: boolean
  logDatefmt: string
  logDatefmtPresent: boolean
  logDatefmtNull: boolean
  extraText: string
}

type RuntimeEditorState = Pick<
  GlobalState,
  'cacheMaxAge' | 'cacheMode' | 'cachePath' | 'extraText' | 'sslMode' | 'sslPath'
>

interface ParsedConfiguration {
  value: unknown | null
  diagnostics: Diagnostic[]
}

interface IssueSummary {
  errors: number
  warnings: number
}

interface RemovedProvider {
  index: number
  provider: ProviderState
}

const SCHEMA_URL = 'https://ddns.newfuture.cc/schema/v4.1.json'
const SCHEMA_VALUES = [
  SCHEMA_URL,
  'http://ddns.newfuture.cc/schema/v4.1.json',
  './schema/v4.1.json',
]
const DOMAIN_PATTERN = /^(?:\*\.)?(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,18}$/
const PROXY_PATTERN = /^(https?:\/\/[a-zA-Z0-9\-_:.]+|[a-zA-Z0-9\-_:.]+:[0-9]+|DIRECT|SYSTEM|DEFAULT)$/
const LOG_LEVELS = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
const ADDRESS_SOURCE_NAMES = new Set(['default', 'local', 'public'])
const ADDRESS_SOURCE_PREFIXES = ['url:', 'regex:', 'cmd:', 'shell:'] as const
const DEFAULT_INDEX_TEXT = 'public\ndefault'
const LEGACY_PROVIDER_KEYS = ['dns', 'id', 'token', 'ipv4', 'ipv6', 'endpoint']
const FLAT_LOG_KEYS = ['log_level', 'log_file', 'log_format', 'log_datefmt']
const RESERVED_EXTRA_KEYS = new Set(['domain', 'value', 'record_type', 'ttl', 'line'])
const COMMON_CONFIG_KEYS = [
  '$schema',
  'dns',
  'id',
  'token',
  'endpoint',
  'ipv4',
  'ipv6',
  'index4',
  'index6',
  'ttl',
  'line',
  'proxy',
  'cache',
  'cache_max_age',
  'ssl',
  'log',
  ...FLAT_LOG_KEYS,
  'extra',
  'debug',
  'config',
  'command',
] as const
const ROOT_KNOWN_KEYS = new Set<string>([...COMMON_CONFIG_KEYS, 'providers'])
const PROVIDER_KNOWN_KEYS = new Set<string>([...COMMON_CONFIG_KEYS, 'provider'])

const { lang } = useData()
const isEnglish = computed(() => lang.value.toLowerCase().startsWith('en'))

const copy = {
  zh: {
    title: '配置生成与校验',
    import: '导入 JSON',
    reset: '新建配置',
    localOnly: '仅在浏览器中处理 · 默认不导出凭据 · 不会请求服务商 API',
    providerSingular: '个服务商',
    providerCount: '个服务商',
    recordSingular: '条 DNS 记录',
    recordCount: '条 DNS 记录',
    schemaState: 'Schema',
    deploymentState: '部署检查',
    schemaValid: 'Schema 有效',
    errorToFixSingular: '项错误待修复',
    errorToFixPlural: '项错误待修复',
    checkToReviewSingular: '项需确认',
    checkToReviewPlural: '项需确认',
    deploymentBlocked: '需先修复配置',
    deploymentConfigured: '没有待确认项',
    testOnlyMode: '使用测试服务商',
    providers: '服务商',
    addProvider: '添加服务商',
    removeProvider: '移除服务商',
    duplicateProvider: '复制当前服务商',
    commonProviders: '常用服务商',
    testingProviders: '测试工具',
    otherProviders: '其他服务商',
    providerSettings: '服务商与凭据',
    records: '域名与 IP 获取',
    network: '网络与 SSL',
    runtime: '缓存、日志与扩展字段',
    configurationSections: '配置分区',
    provider: 'DNS 服务商',
    chooseProvider: '选择 DNS 服务商',
    providerSearch: '搜索服务商',
    providerSearchPlaceholder: '按名称、标识或认证方式搜索',
    noProviderResults: '未找到匹配的服务商。请尝试搜索名称或服务商标识。',
    selectedProvider: '当前选择',
    testOnly: '仅供测试',
    authNone: '无需凭据',
    authToken: 'Token',
    authIdToken: 'ID + Token',
    authFlexible: '多种认证方式',
    authCallback: 'Webhook',
    providerHelp: '查看服务商文档',
    credentialTitle: '认证信息',
    credentialHint: '凭据只保留在当前页面，默认不会写入导出的配置；部署时可通过环境变量提供。',
    noCredential: '此服务商不需要认证信息。',
    optional: '可选',
    advanced: '可选设置',
    configured: '已配置',
    endpointSettings: '自定义 API 端点',
    endpoint: '自定义 API 端点',
    endpointPlaceholder: '留空则使用服务商默认端点',
    reveal: '显示凭据',
    conceal: '隐藏凭据',
    recordsTitle: '要同步的域名',
    recordsHint: '可用逗号或换行分隔；支持 *.home.example.com 这样的通配符域名。',
    sourceSettings: 'IP 获取方式、TTL 与解析线路',
    ipv4Domains: 'IPv4 域名',
    ipv6Domains: 'IPv6 域名',
    addressSources: 'IP 获取顺序',
    sourceHint: '每行填写一种 IP 获取方式，DDNS 会按顺序依次尝试。支持 public、default、网卡序号，以及 url:、regex:、cmd: 或 shell:。',
    ttl: 'TTL（秒）',
    line: '解析线路',
    inheritProvider: '沿用服务商默认值',
    inheritEnvironment: '由运行时提供',
    networkTitle: '配置代理与 SSL 验证',
    providerProxy: '当前服务商代理',
    globalProxy: '全局代理',
    proxyHint: '每行填写一个代理；支持 http(s)://、host:port、DIRECT、SYSTEM 或 DEFAULT。',
    sslSettings: 'SSL 验证与自定义 CA',
    ssl: 'SSL 验证',
    inheritGlobal: '继承全局设置',
    sslAuto: '自动降级（auto）',
    sslStrict: '强制验证（true）',
    sslOff: '关闭验证（false）',
    sslCustom: '自定义 CA 文件',
    caPath: 'CA 证书路径',
    runtimeTitle: '配置缓存、日志与扩展字段',
    runtimeHint: '先设置全局缓存与日志；如有需要，再为当前服务商覆盖对应设置。',
    cache: '缓存策略',
    cacheOn: '启用默认缓存',
    cacheOff: '禁用缓存',
    cachePath: '指定缓存文件',
    cacheFile: '缓存文件路径',
    cacheAge: '缓存最长有效期（秒）',
    logLevel: '日志级别',
    logging: '日志设置',
    logFile: '日志文件',
    logFormat: '日志格式',
    dateFormat: '日期格式',
    providerOverrides: '当前服务商设置',
    providerOverridesHint: '只填写当前服务商与全局配置不同的值；其他设置会继承全局配置。',
    runtimeAdvanced: '当前服务商设置与扩展字段',
    extraGlobal: '全局扩展字段（JSON 对象）',
    extraProvider: '当前服务商扩展字段（JSON 对象）',
    inspectorPreview: '配置预览',
    inspectorValidate: '粘贴并校验',
    includeCredentials: '导出时包含凭据',
    credentialsExcluded: '凭据不会出现在预览、剪贴板或下载文件中。',
    credentialsIncluded: '已填写的凭据将写入预览、剪贴板和 config.json，请妥善保管。',
    validatorLabel: '待校验的 JSON 或 JSONC 配置',
    copy: '复制',
    download: '下载 config.json',
    apply: '载入编辑器',
    validatorPlaceholder: '在这里粘贴 JSON 或 JSONC 配置…',
    validatorHint: '可使用 DDNS 支持的 // 和 # 单行注释；页面会按 schema/v4.1.json 校验，并检查运行时要求。',
    diagnostics: '校验结果',
    noIssues: '静态检查未发现问题。此页面不会验证真实凭据、网络连接或服务商 API。',
    error: '错误',
    errors: '错误',
    warning: '提醒',
    warnings: '提醒',
    lineCount: '行',
    copied: '已复制配置',
    copyFailed: '无法访问剪贴板，请手动复制',
    downloaded: '已下载 config.json',
    imported: '已载入文件并更新校验结果',
    importFailed: '无法读取所选文件',
    applied: '已将配置载入编辑器',
    resetDone: '已新建配置',
    confirmReset: '新建配置并清除当前内容？凭据和尚未导出的更改将丢失。',
    providerAdded: '已添加服务商',
    providerRemoved: '已移除服务商',
    providerRestored: '已恢复服务商',
    providerDuplicated: '已复制服务商设置，凭据未复制',
    providerChanged: '已切换服务商，并清除原有凭据、端点和扩展字段',
    undo: '撤销',
    goToField: '定位字段',
    reviewConfig: '查看配置',
    closeReview: '关闭配置预览',
    empty: '暂无内容',
    outputReady: '可导出',
    outputWarning: '可导出 · 部署前需确认',
    outputBlocked: '修复错误后再导出',
    generatedConfigLabel: '生成的 DDNS 配置',
    ipv4DomainList: 'IPv4 域名列表',
    ipv6DomainList: 'IPv6 域名列表',
  },
  en: {
    title: 'Configuration builder & validator',
    import: 'Import JSON',
    reset: 'New config',
    localOnly: 'Processed in this browser · credentials excluded by default · no provider API requests',
    providerSingular: 'provider',
    providerCount: 'providers',
    recordSingular: 'DNS record',
    recordCount: 'DNS records',
    schemaState: 'Schema',
    deploymentState: 'Deployment checks',
    schemaValid: 'Schema valid',
    errorToFixSingular: 'error to fix',
    errorToFixPlural: 'errors to fix',
    checkToReviewSingular: 'item to review',
    checkToReviewPlural: 'items to review',
    deploymentBlocked: 'Fix configuration errors first',
    deploymentConfigured: 'Nothing to review',
    testOnlyMode: 'Uses a test-only provider',
    providers: 'Providers',
    addProvider: 'Add provider',
    removeProvider: 'Remove provider',
    duplicateProvider: 'Duplicate current provider',
    commonProviders: 'Common providers',
    testingProviders: 'Testing tools',
    otherProviders: 'Other providers',
    providerSettings: 'Provider & credentials',
    records: 'Domains & IP detection',
    network: 'Network & SSL',
    runtime: 'Cache, logs & custom fields',
    configurationSections: 'Configuration sections',
    provider: 'DNS provider',
    chooseProvider: 'Choose a DNS provider',
    providerSearch: 'Search providers',
    providerSearchPlaceholder: 'Search by name, identifier, or authentication',
    noProviderResults: 'No matching provider. Try searching by name or provider identifier.',
    selectedProvider: 'Selected',
    testOnly: 'Test only',
    authNone: 'No credentials',
    authToken: 'Token',
    authIdToken: 'ID + Token',
    authFlexible: 'Multiple auth options',
    authCallback: 'Webhook',
    providerHelp: 'Open provider documentation',
    credentialTitle: 'Credentials',
    credentialHint: 'Credentials stay on this page. They are excluded from exports by default and can be supplied through environment variables at runtime.',
    noCredential: 'This provider does not require credentials.',
    optional: 'Optional',
    advanced: 'Optional settings',
    configured: 'Configured',
    endpointSettings: 'Custom API endpoint',
    endpoint: 'Custom API endpoint',
    endpointPlaceholder: 'Leave blank to use the provider default endpoint',
    reveal: 'Reveal credential',
    conceal: 'Conceal credential',
    recordsTitle: 'Domains to keep in sync',
    recordsHint: 'Separate domains with commas or line breaks. Wildcards such as *.home.example.com are supported.',
    sourceSettings: 'IP detection, TTL & DNS line',
    ipv4Domains: 'IPv4 domains',
    ipv6Domains: 'IPv6 domains',
    addressSources: 'IP detection order',
    sourceHint: 'Enter one IP detection method per line. DDNS tries them in order. Use public, default, an interface index, url:, regex:, cmd:, or shell:.',
    ttl: 'TTL (seconds)',
    line: 'DNS line',
    inheritProvider: 'Provider default',
    inheritEnvironment: 'Set at runtime',
    networkTitle: 'Configure proxies & SSL verification',
    providerProxy: 'Provider-specific proxy',
    globalProxy: 'Global proxy',
    proxyHint: 'Enter one proxy per line: http(s)://, host:port, DIRECT, SYSTEM, or DEFAULT.',
    sslSettings: 'SSL verification & custom CA',
    ssl: 'SSL verification',
    inheritGlobal: 'Inherit global setting',
    sslAuto: 'Automatic fallback (auto)',
    sslStrict: 'Require verification (true)',
    sslOff: 'Disable verification (false)',
    sslCustom: 'Custom CA file',
    caPath: 'CA certificate path',
    runtimeTitle: 'Configure cache, logs & custom fields',
    runtimeHint: 'Set global cache and logging behavior, then add provider-specific overrides if needed.',
    cache: 'Cache policy',
    cacheOn: 'Enable default cache',
    cacheOff: 'Disable cache',
    cachePath: 'Use a specific cache file',
    cacheFile: 'Cache file path',
    cacheAge: 'Maximum cache age (seconds)',
    logLevel: 'Log level',
    logging: 'Logging',
    logFile: 'Log file',
    logFormat: 'Log format',
    dateFormat: 'Date format',
    providerOverrides: 'Provider-specific settings',
    providerOverridesHint: 'Only set values that should differ for this provider. Other values inherit the global configuration.',
    runtimeAdvanced: 'Provider-specific settings & custom fields',
    extraGlobal: 'Global custom fields (JSON object)',
    extraProvider: 'Provider-specific custom fields (JSON object)',
    inspectorPreview: 'Generated config',
    inspectorValidate: 'Paste & validate',
    includeCredentials: 'Include credentials in exports',
    credentialsExcluded: 'Credentials are excluded from the preview, clipboard, and downloaded file.',
    credentialsIncluded: 'Any credentials you enter will be included in the preview, clipboard, and config.json. Store them securely.',
    validatorLabel: 'JSON or JSONC configuration to check',
    copy: 'Copy',
    download: 'Download config.json',
    apply: 'Load into builder',
    validatorPlaceholder: 'Paste a JSON or JSONC configuration here…',
    validatorHint: 'Supports the // and # single-line comments accepted by DDNS. Checks against schema/v4.1.json and reviews runtime requirements.',
    diagnostics: 'Validation results',
    noIssues: 'Static checks found no issues. This page does not verify live credentials, network access, or provider APIs.',
    error: 'Error',
    errors: 'Errors',
    warning: 'Warning',
    warnings: 'Warnings',
    lineCount: 'lines',
    copied: 'Copied configuration',
    copyFailed: 'Clipboard access failed; copy the text manually',
    downloaded: 'Downloaded config.json',
    imported: 'Loaded file for validation',
    importFailed: 'The selected file could not be read',
    applied: 'Loaded configuration into the builder',
    resetDone: 'Created a new configuration',
    confirmReset: 'Start a new configuration and clear the current one? Credentials and changes not yet exported will be lost.',
    providerAdded: 'Provider added',
    providerRemoved: 'Provider removed',
    providerRestored: 'Provider restored',
    providerDuplicated: 'Provider settings duplicated without credentials',
    providerChanged: 'Changed provider and cleared the previous credentials, endpoint, and custom fields',
    undo: 'Undo',
    goToField: 'Go to field',
    reviewConfig: 'Review config',
    closeReview: 'Close config review',
    empty: 'No content',
    outputReady: 'Export available',
    outputWarning: 'Export available · review before deployment',
    outputBlocked: 'Fix errors before exporting',
    generatedConfigLabel: 'Generated DDNS configuration',
    ipv4DomainList: 'IPv4 domain list',
    ipv6DomainList: 'IPv6 domain list',
  },
} as const

const c = computed(() => (isEnglish.value ? copy.en : copy.zh))

const providerCatalog: ProviderMeta[] = [
  {
    value: '51dns',
    name: '51DNS',
    docs: '51dns',
    auth: 'id-token',
    descriptionZh: '使用 DNS.COM / 51DNS API Key 与 Secret',
    descriptionEn: 'Uses a DNS.COM / 51DNS API key and secret',
    idLabelZh: 'API Key',
    idLabelEn: 'API key',
    tokenLabelZh: 'API Secret',
    tokenLabelEn: 'API secret',
  },
  {
    value: 'alidns',
    name: 'AliDNS',
    docs: 'alidns',
    auth: 'id-token',
    descriptionZh: '使用阿里云 AccessKey 认证',
    descriptionEn: 'Uses Alibaba Cloud AccessKey credentials',
    idLabelZh: 'AccessKey ID',
    idLabelEn: 'AccessKey ID',
    tokenLabelZh: 'AccessKey Secret',
    tokenLabelEn: 'AccessKey secret',
  },
  {
    value: 'aliesa',
    name: 'Ali ESA',
    docs: 'aliesa',
    auth: 'id-token',
    descriptionZh: '使用阿里云 ESA AccessKey 认证',
    descriptionEn: 'Uses Alibaba Cloud ESA AccessKey credentials',
    idLabelZh: 'AccessKey ID',
    idLabelEn: 'AccessKey ID',
    tokenLabelZh: 'AccessKey Secret',
    tokenLabelEn: 'AccessKey secret',
  },
  {
    value: 'callback',
    name: 'Callback',
    docs: 'callback',
    auth: 'callback',
    descriptionZh: '将 DNS 更新转发到自定义 HTTP API 或 Webhook',
    descriptionEn: 'Forwards DNS updates to a custom HTTP API or webhook',
    idLabelZh: '完整回调 URL',
    idLabelEn: 'Full callback URL',
    tokenLabelZh: 'POST 请求体（留空则使用 GET）',
    tokenLabelEn: 'POST body (leave blank for GET)',
  },
  {
    value: 'cloudflare',
    name: 'Cloudflare',
    docs: 'cloudflare',
    auth: 'flexible',
    descriptionZh: '建议使用 API Token；Global API Key 还需填写账户邮箱',
    descriptionEn: 'Use an API Token when possible. A Global API Key also requires your account email.',
    idLabelZh: '账户邮箱',
    idLabelEn: 'Account email',
    tokenLabelZh: 'API Token / Global API Key',
    tokenLabelEn: 'API Token / Global API Key',
  },
  {
    value: 'cloudns',
    name: 'ClouDNS',
    docs: 'cloudns',
    auth: 'id-token',
    descriptionZh: '使用 ClouDNS Auth ID 与密码',
    descriptionEn: 'Uses a ClouDNS auth ID and password',
    idLabelZh: 'Auth ID',
    idLabelEn: 'Auth ID',
    tokenLabelZh: 'Auth Password',
    tokenLabelEn: 'Auth password',
  },
  {
    value: 'debug',
    name: 'Debug',
    docs: 'debug',
    auth: 'none',
    testOnly: true,
    descriptionZh: '只打印更新结果，不修改实际 DNS 记录',
    descriptionEn: 'Prints update results without changing live DNS records',
    idLabelZh: 'ID',
    idLabelEn: 'ID',
    tokenLabelZh: 'Token',
    tokenLabelEn: 'Token',
  },
  {
    value: 'dnscom',
    name: 'DNS.COM',
    docs: '51dns',
    auth: 'id-token',
    descriptionZh: 'DNS.COM / 51DNS API 的兼容别名',
    descriptionEn: 'Alias for the DNS.COM / 51DNS API',
    idLabelZh: 'API Key',
    idLabelEn: 'API key',
    tokenLabelZh: 'API Secret',
    tokenLabelEn: 'API secret',
  },
  {
    value: 'dnspod_com',
    name: 'DNSPod Global',
    docs: 'dnspod_com',
    auth: 'id-token',
    descriptionZh: '使用 DNSPod 国际版 API 凭据',
    descriptionEn: 'Uses DNSPod Global API credentials',
    idLabelZh: 'API ID',
    idLabelEn: 'API ID',
    tokenLabelZh: 'API Token',
    tokenLabelEn: 'API token',
  },
  {
    value: 'dnspod',
    name: 'DNSPod',
    docs: 'dnspod',
    auth: 'id-token',
    descriptionZh: '使用 DNSPod 中国版 Login Token',
    descriptionEn: 'Uses a DNSPod China login token',
    idLabelZh: 'Token ID',
    idLabelEn: 'Token ID',
    tokenLabelZh: 'Token',
    tokenLabelEn: 'Token',
  },
  {
    value: 'edgeone',
    name: 'EdgeOne',
    docs: 'edgeone',
    auth: 'id-token',
    descriptionZh: '管理腾讯云 EdgeOne 加速域名',
    descriptionEn: 'Manages Tencent Cloud EdgeOne accelerated domains',
    idLabelZh: 'Secret ID',
    idLabelEn: 'Secret ID',
    tokenLabelZh: 'Secret Key',
    tokenLabelEn: 'Secret key',
  },
  {
    value: 'edgeone_dns',
    name: 'EdgeOne DNS',
    docs: 'edgeone_dns',
    auth: 'id-token',
    descriptionZh: '管理腾讯云 EdgeOne 非加速 DNS 记录',
    descriptionEn: 'Manages Tencent Cloud EdgeOne non-accelerated DNS records',
    idLabelZh: 'Secret ID',
    idLabelEn: 'Secret ID',
    tokenLabelZh: 'Secret Key',
    tokenLabelEn: 'Secret key',
  },
  {
    value: 'he',
    name: 'HE.net',
    docs: 'he',
    auth: 'token',
    descriptionZh: '使用 HE.net DDNS 密码',
    descriptionEn: 'Uses a Hurricane Electric DDNS password',
    idLabelZh: 'ID',
    idLabelEn: 'ID',
    tokenLabelZh: 'DDNS Password',
    tokenLabelEn: 'DDNS password',
  },
  {
    value: 'huaweidns',
    name: 'Huawei Cloud DNS',
    docs: 'huaweidns',
    auth: 'id-token',
    descriptionZh: '使用华为云 IAM 访问密钥',
    descriptionEn: 'Uses Huawei Cloud IAM access keys',
    idLabelZh: 'Access Key ID',
    idLabelEn: 'Access Key ID',
    tokenLabelZh: 'Secret Access Key',
    tokenLabelEn: 'Secret access key',
  },
  {
    value: 'namesilo',
    name: 'NameSilo',
    docs: 'namesilo',
    auth: 'token',
    descriptionZh: '仅需 NameSilo API Key',
    descriptionEn: 'Requires only a NameSilo API key',
    idLabelZh: 'ID',
    idLabelEn: 'ID',
    tokenLabelZh: 'API Key',
    tokenLabelEn: 'API key',
  },
  {
    value: 'noip',
    name: 'No-IP',
    docs: 'noip',
    auth: 'id-token',
    descriptionZh: '使用 No-IP 用户名与密码',
    descriptionEn: 'Uses a No-IP username and password',
    idLabelZh: '用户名',
    idLabelEn: 'Username',
    tokenLabelZh: 'Password',
    tokenLabelEn: 'Password',
  },
  {
    value: 'tencentcloud',
    name: 'Tencent Cloud DNS',
    docs: 'tencentcloud',
    auth: 'id-token',
    descriptionZh: '使用腾讯云 SecretId 与 SecretKey',
    descriptionEn: 'Uses Tencent Cloud SecretId and SecretKey',
    idLabelZh: 'Secret ID',
    idLabelEn: 'Secret ID',
    tokenLabelZh: 'Secret Key',
    tokenLabelEn: 'Secret key',
  },
  {
    value: 'west',
    name: 'West.cn',
    docs: 'west',
    auth: 'flexible',
    descriptionZh: '支持西部数码账户认证或域名独立密码',
    descriptionEn: 'Supports West.cn account credentials or a per-domain key',
    idLabelZh: '用户名',
    idLabelEn: 'Username',
    tokenLabelZh: 'API Key / Domain Key',
    tokenLabelEn: 'API key / domain key',
  },
]

const providerMap = new Map<string, ProviderMeta>(
  providerCatalog.map((provider) => [provider.value, provider] as [string, ProviderMeta]),
)
const commonProviderValues = new Set(['cloudflare', 'dnspod', 'alidns', 'tencentcloud'])
const commonProviderCatalog = providerCatalog.filter((provider) => commonProviderValues.has(provider.value))
const testingProviderCatalog = providerCatalog.filter((provider) => provider.testOnly)
const otherProviderCatalog = providerCatalog.filter(
  (provider) => !commonProviderValues.has(provider.value) && !provider.testOnly,
)
let nextProviderUid = 1

function makeProvider(provider = 'debug'): ProviderState {
  return {
    uid: nextProviderUid++,
    provider,
    id: '',
    idPresent: false,
    idNull: false,
    token: '',
    tokenPresent: false,
    endpoint: '',
    endpointPresent: false,
    endpointNull: false,
    ipv4Text: 'home.example.com',
    ipv4Present: true,
    ipv6Text: '',
    ipv6Present: false,
    index4Text: DEFAULT_INDEX_TEXT,
    index6Text: DEFAULT_INDEX_TEXT,
    ttl: '',
    ttlNull: false,
    line: '',
    linePresent: false,
    lineNull: false,
    proxyText: '',
    proxyPresent: false,
    sslMode: 'inherit',
    sslPath: '',
    cacheMode: 'inherit',
    cachePath: '',
    cacheMaxAge: '',
    logLevel: '',
    extraText: '',
    revealToken: false,
  }
}

function makeGlobalState(): GlobalState {
  return {
    proxyText: '',
    proxyPresent: false,
    sslMode: 'auto',
    sslPath: '',
    cacheMode: 'true',
    cachePath: '',
    cacheMaxAge: '259200',
    logLevel: 'INFO',
    logFile: '',
    logFilePresent: false,
    logFileNull: false,
    logFormat: '',
    logFormatPresent: false,
    logFormatNull: false,
    logDatefmt: '',
    logDatefmtPresent: false,
    logDatefmtNull: false,
    extraText: '',
  }
}

const providers = ref<ProviderState[]>([makeProvider()])
const selectedUid = ref(providers.value[0].uid)
const activeSection = ref<SectionKey>('provider')
const inspectorTab = ref<InspectorTab>('preview')
const includeCredentials = ref(false)
const providerAdvancedOpen = ref(false)
const sourceAdvancedOpen = ref(false)
const networkAdvancedOpen = ref(false)
const runtimeAdvancedOpen = ref(false)
const mobileReviewOpen = ref(false)
const providerPickerOpen = ref(false)
const providerQuery = ref('')
const validationInput = ref('')
const validatorTouched = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)
const providerPickerTrigger = ref<HTMLButtonElement | null>(null)
const providerSearchInput = ref<HTMLInputElement | null>(null)
const mobileReviewButton = ref<HTMLButtonElement | null>(null)
const mobileReviewCloseButton = ref<HTMLButtonElement | null>(null)
const mobileReviewPanel = ref<HTMLElement | null>(null)
const toastMessage = ref('')
const toastTone = ref<'success' | 'error'>('success')
const toastVisible = ref(false)
const lastRemovedProvider = ref<RemovedProvider | null>(null)
let toastTimer: ReturnType<typeof setTimeout> | undefined

const globalState = reactive<GlobalState>(makeGlobalState())

const sections = computed(() => [
  { key: 'provider' as const, label: c.value.providerSettings },
  { key: 'records' as const, label: c.value.records },
  { key: 'network' as const, label: c.value.network },
  { key: 'runtime' as const, label: c.value.runtime },
])

const selectedProvider = computed(() => {
  return providers.value.find((provider) => provider.uid === selectedUid.value) || providers.value[0]!
})
const selectedProviderIndex = computed(() =>
  Math.max(
    0,
    providers.value.findIndex((provider) => provider.uid === selectedUid.value),
  ),
)
const selectedMeta = computed(() => providerMap.get(selectedProvider.value.provider) || providerCatalog[0]!)
const providerPickerPanelId = computed(() => `studio-provider-picker-${selectedProvider.value.uid}`)
const normalizedProviderQuery = computed(() => providerQuery.value.trim().toLowerCase())
const filteredProviderGroups = computed(() => {
  const query = normalizedProviderQuery.value
  const matches = (provider: ProviderMeta) => {
    if (!query) return true
    return [
      provider.name,
      provider.value,
      provider.descriptionZh,
      provider.descriptionEn,
      providerAuthLabel(provider),
    ]
      .join(' ')
      .toLowerCase()
      .includes(query)
  }
  return [
    {
      key: 'common',
      label: c.value.commonProviders,
      providers: commonProviderCatalog.filter(matches),
    },
    {
      key: 'testing',
      label: c.value.testingProviders,
      providers: testingProviderCatalog.filter(matches),
    },
    {
      key: 'other',
      label: c.value.otherProviders,
      providers: otherProviderCatalog.filter(matches),
    },
  ].filter((group) => group.providers.length)
})
const hasProviderSearchResults = computed(() => filteredProviderGroups.value.length > 0)
const selectedIpv4 = computed(() => splitSimpleList(selectedProvider.value.ipv4Text))
const selectedIpv6 = computed(() => splitSimpleList(selectedProvider.value.ipv6Text))
const recordCount = computed(() => {
  return providers.value.reduce((total, provider) => {
    return total + splitSimpleList(provider.ipv4Text).length + splitSimpleList(provider.ipv6Text).length
  }, 0)
})
const credentialProviderIndexes = computed(() => {
  return providers.value.reduce<number[]>((indexes, provider, index) => {
    const auth = providerMap.get(provider.provider)?.auth
    if (auth && auth !== 'none') indexes.push(index)
    return indexes
  }, [])
})
const hasCredentialProviders = computed(() => credentialProviderIndexes.value.length > 0)
const hasSensitiveEndpoints = computed(() =>
  providers.value.some((provider) => hasHttpUrlCredentials(provider.endpoint)),
)
const hasSensitiveAddressSources = computed(() =>
  providers.value.some((provider) =>
    [provider.index4Text, provider.index6Text].some((value) =>
      splitIndexList(value).some(hasAddressSourceCredentials),
    ),
  ),
)
const hasSensitiveValues = computed(
  () =>
    hasCredentialProviders.value ||
    hasSensitiveEndpoints.value ||
    hasSensitiveAddressSources.value,
)
const testProviderCount = computed(
  () => providers.value.filter((provider) => providerMap.get(provider.provider)?.testOnly).length,
)
const hasTestOnlyProviders = computed(() => testProviderCount.value > 0)
const providerDocsLink = computed(() => {
  const prefix = isEnglish.value ? '/en/providers/' : '/providers/'
  return withBase(`${prefix}${selectedMeta.value.docs}`)
})
const hasEndpointSettings = computed(() =>
  Boolean(
    selectedProvider.value.endpoint.trim() ||
      selectedProvider.value.endpointPresent ||
      selectedProvider.value.endpointNull,
  ),
)
const hasSourceSettings = computed(() => {
  const provider = selectedProvider.value
  return (
    provider.index4Text.trim() !== DEFAULT_INDEX_TEXT ||
    provider.index6Text.trim() !== DEFAULT_INDEX_TEXT ||
    Boolean(
      provider.ttl.trim() ||
        provider.ttlNull ||
        provider.line.trim() ||
        provider.linePresent ||
        provider.lineNull,
    )
  )
})
const hasNetworkAdvancedSettings = computed(() => {
  return (
    globalState.sslMode !== 'auto' ||
    selectedProvider.value.sslMode !== 'inherit' ||
    Boolean(globalState.sslPath.trim() || selectedProvider.value.sslPath.trim())
  )
})
const hasRuntimeAdvancedSettings = computed(() => {
  const provider = selectedProvider.value
  return (
    provider.cacheMode !== 'inherit' ||
    Boolean(
      provider.cacheMaxAge.trim() ||
      provider.cachePath.trim() ||
      provider.logLevel !== '' ||
      provider.extraText.trim(),
    ) ||
    Boolean(globalState.extraText.trim())
  )
})

function providerAuthLabel(provider: ProviderMeta): string {
  const labels: Record<AuthMode, string> = {
    none: c.value.authNone,
    token: c.value.authToken,
    'id-token': c.value.authIdToken,
    flexible: c.value.authFlexible,
    callback: c.value.authCallback,
  }
  return labels[provider.auth]
}

function showToast(
  message: string,
  tone: 'success' | 'error' = 'success',
  duration = 2600,
  keepUndo = false,
) {
  if (!keepUndo) lastRemovedProvider.value = null
  toastMessage.value = message
  toastTone.value = tone
  toastVisible.value = true
  if (toastTimer) clearTimeout(toastTimer)
  toastTimer = setTimeout(() => {
    toastVisible.value = false
    lastRemovedProvider.value = null
    toastTimer = undefined
  }, duration)
}

function splitSimpleList(value: string): string[] {
  return value
    .split(/[\n,;]+/)
    .map((item) => item.trim())
    .filter(Boolean)
}

function providerCountUnit(count: number): string {
  return isEnglish.value && count === 1 ? c.value.providerSingular : c.value.providerCount
}

function recordCountUnit(count: number): string {
  return isEnglish.value && count === 1 ? c.value.recordSingular : c.value.recordCount
}

function errorCountUnit(count: number): string {
  return isEnglish.value && count !== 1 ? c.value.errors : c.value.error
}

function warningCountUnit(count: number): string {
  return isEnglish.value && count !== 1 ? c.value.warnings : c.value.warning
}

function errorToFixUnit(count: number): string {
  return isEnglish.value && count === 1 ? c.value.errorToFixSingular : c.value.errorToFixPlural
}

function checkToReviewUnit(count: number): string {
  return isEnglish.value && count === 1 ? c.value.checkToReviewSingular : c.value.checkToReviewPlural
}

function providerRecordCount(provider: ProviderState): number {
  return splitSimpleList(provider.ipv4Text).length + splitSimpleList(provider.ipv6Text).length
}

function splitLineList(value: string): string[] {
  return value
    .split(/\r?\n/)
    .map((item) => item.trim())
    .filter(Boolean)
}

function addressSourcePrefix(value: string): (typeof ADDRESS_SOURCE_PREFIXES)[number] | undefined {
  return ADDRESS_SOURCE_PREFIXES.find((prefix) => value.startsWith(prefix))
}

function normalizeAddressSource(value: string): string {
  const source = value.trim()
  const prefix = addressSourcePrefix(source)
  return prefix ? `${prefix}${source.slice(prefix.length).trim()}` : source
}

function addressSourceSeparator(value: string): ',' | ';' | '' {
  let firstSpecialSource = value.length
  ADDRESS_SOURCE_PREFIXES.forEach((prefix) => {
    let index = value.indexOf(prefix)
    while (index >= 0) {
      const preceding = value.slice(0, index).trimEnd()
      if (!preceding || /[,;]$/.test(preceding)) {
        firstSpecialSource = Math.min(firstSpecialSource, index)
        break
      }
      index = value.indexOf(prefix, index + prefix.length)
    }
  })
  const delimiterScope = value.slice(0, firstSpecialSource)
  if (delimiterScope.includes(',')) return ','
  if (delimiterScope.includes(';')) return ';'
  return ''
}

function splitIndexList(value: string): string[] {
  const result: string[] = []
  splitLineList(value).forEach((line) => {
    const separator = addressSourceSeparator(line)
    if (!separator) {
      result.push(normalizeAddressSource(line))
      return
    }

    const parts = line.split(separator)
    for (let index = 0; index < parts.length; index += 1) {
      const part = parts[index].trim()
      if (!part) continue
      if (addressSourcePrefix(part)) {
        result.push(normalizeAddressSource(parts.slice(index).join(separator)))
        break
      }
      result.push(part)
    }
  })
  return result
}

function hasAddressSourceCredentials(value: string): boolean {
  const source = normalizeAddressSource(value)
  const prefix = addressSourcePrefix(source)
  return prefix === 'url:' && hasHttpUrlCredentials(source.slice(prefix.length))
}

function stripSensitiveAddressSources(value: string): string {
  const sources = splitIndexList(value)
  if (!sources.some(hasAddressSourceCredentials)) return value
  return sources.filter((source) => !hasAddressSourceCredentials(source)).join('\n')
}

function parseIndexValue(value: string, includeSensitiveValues = true): JsonValue | undefined {
  const trimmed = value.trim()
  if (['false', 'none'].includes(trimmed.toLowerCase())) return false
  if (trimmed.toLowerCase() === 'true') return true
  const parts = splitIndexList(trimmed).filter(
    (part) => includeSensitiveValues || !hasAddressSourceCredentials(part),
  )
  if (!parts.length) return undefined
  return parts.map((part) => (/^\d+$/.test(part) ? Number(part) : part))
}

function parseProxyValue(value: string): string[] {
  return splitSimpleList(value)
}

function stripJsonComments(source: string): string {
  let result = ''
  let inString = false
  let escaped = false
  let inComment = false

  for (let index = 0; index < source.length; index += 1) {
    const character = source[index]
    const next = source[index + 1]

    if (inComment) {
      if (character === '\n' || character === '\r') {
        inComment = false
        result += character
      } else {
        result += ' '
      }
      continue
    }

    if (inString) {
      result += character
      if (escaped) {
        escaped = false
      } else if (character === '\\') {
        escaped = true
      } else if (character === '"') {
        inString = false
      }
      continue
    }

    if (character === '"') {
      inString = true
      result += character
    } else if (character === '#' || (character === '/' && next === '/')) {
      inComment = true
      result += ' '
      if (character === '/') {
        result += ' '
        index += 1
      }
    } else {
      result += character
    }
  }

  return result
}

function isPlainObject(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function parseObjectText(text: string): JsonObject | null {
  if (!text.trim()) return null
  try {
    const parsed: unknown = JSON.parse(stripJsonComments(text))
    return isPlainObject(parsed) ? (parsed as JsonObject) : null
  } catch {
    return null
  }
}

function cacheValue(mode: CacheMode, path: string): JsonValue | undefined {
  if (mode === 'inherit') return undefined
  if (mode === 'true') return true
  if (mode === 'false') return false
  return path.trim()
}

function sslValue(mode: SslMode, path: string): JsonValue | undefined {
  if (mode === 'inherit') return undefined
  if (mode === 'auto') return 'auto'
  if (mode === 'true') return true
  if (mode === 'false') return false
  return path.trim()
}

function buildProvider(
  provider: ProviderState,
  includeSensitiveValues = true,
): JsonObject {
  const output: JsonObject = { provider: provider.provider }
  const meta = providerMap.get(provider.provider)

  if (provider.idNull) {
    output.id = null
  } else if (provider.idPresent && !provider.id.trim()) {
    output.id = ''
  } else if (
    includeSensitiveValues &&
    meta?.auth !== 'none' &&
    meta?.auth !== 'token' &&
    meta?.auth !== 'callback' &&
    provider.id.trim()
  ) {
    output.id = provider.id.trim()
  }
  if (meta?.auth === 'callback') {
    if (includeSensitiveValues && provider.id.trim()) output.id = provider.id.trim()
    if (includeSensitiveValues && (provider.token || provider.tokenPresent)) {
      output.token = provider.token
    } else if (provider.tokenPresent && !provider.token) {
      output.token = ''
    }
  } else if (
    includeSensitiveValues &&
    meta?.auth !== 'none' &&
    (provider.token || provider.tokenPresent)
  ) {
    output.token = provider.token
  }
  const endpoint = provider.endpoint.trim()
  if (provider.endpointNull) {
    output.endpoint = null
  } else if (endpoint) {
    if (includeSensitiveValues || !hasHttpUrlCredentials(endpoint)) output.endpoint = endpoint
  } else if (provider.endpointPresent) {
    output.endpoint = ''
  }

  const ipv4 = splitSimpleList(provider.ipv4Text)
  const ipv6 = splitSimpleList(provider.ipv6Text)
  if (ipv4.length || provider.ipv4Present) output.ipv4 = ipv4
  if (ipv6.length || provider.ipv6Present) output.ipv6 = ipv6
  const index4 = parseIndexValue(provider.index4Text, includeSensitiveValues)
  const index6 = parseIndexValue(provider.index6Text, includeSensitiveValues)
  if (index4 !== undefined) output.index4 = index4
  if (index6 !== undefined) output.index6 = index6
  if (provider.ttlNull) output.ttl = null
  else if (provider.ttl.trim() && Number.isFinite(Number(provider.ttl))) {
    output.ttl = Number(provider.ttl)
  }
  if (provider.lineNull) output.line = null
  else if (provider.line.trim()) output.line = provider.line.trim()
  else if (provider.linePresent) output.line = ''

  const proxies = parseProxyValue(provider.proxyText)
  if (proxies.length || provider.proxyPresent) output.proxy = proxies
  const providerSsl = sslValue(provider.sslMode, provider.sslPath)
  if (providerSsl !== undefined) output.ssl = providerSsl
  const providerCache = cacheValue(provider.cacheMode, provider.cachePath)
  if (providerCache !== undefined) output.cache = providerCache
  if (provider.cacheMaxAge.trim() && Number.isInteger(Number(provider.cacheMaxAge))) {
    output.cache_max_age = Number(provider.cacheMaxAge)
  }
  if (typeof provider.logLevel === 'number') output.log_level = provider.logLevel
  else if (provider.logLevel) output.log = { level: provider.logLevel }

  const extra = parseObjectText(provider.extraText)
  if (extra && Object.keys(extra).length) output.extra = extra
  return output
}

function buildConfiguration(includeSensitiveValues: boolean): JsonObject {
  const globalExtra = parseObjectText(globalState.extraText) || {}
  const output: JsonObject = {
    $schema: SCHEMA_URL,
    providers: providers.value.map((provider) => buildProvider(provider, includeSensitiveValues)),
  }

  const globalSsl = sslValue(globalState.sslMode, globalState.sslPath)
  if (globalSsl !== undefined) output.ssl = globalSsl
  const globalCache = cacheValue(globalState.cacheMode, globalState.cachePath)
  if (globalCache !== undefined) output.cache = globalCache
  if (globalState.cacheMaxAge.trim() && Number.isInteger(Number(globalState.cacheMaxAge))) {
    output.cache_max_age = Number(globalState.cacheMaxAge)
  }
  const proxies = parseProxyValue(globalState.proxyText)
  if (proxies.length || globalState.proxyPresent) output.proxy = proxies

  const log: JsonObject = {}
  if (typeof globalState.logLevel === 'number') output.log_level = globalState.logLevel
  else if (globalState.logLevel) log.level = globalState.logLevel
  if (globalState.logFilePresent) {
    log.file = globalState.logFileNull ? null : globalState.logFile
  }
  if (globalState.logFormatPresent) {
    log.format = globalState.logFormatNull ? null : globalState.logFormat
  }
  if (globalState.logDatefmtPresent) {
    log.datefmt = globalState.logDatefmtNull ? null : globalState.logDatefmt
  }
  if (Object.keys(log).length) output.log = log

  if (Object.keys(globalExtra).length) output.extra = globalExtra
  return output
}

const exportConfig = computed<JsonObject>(() => buildConfiguration(includeCredentials.value))

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

function highlightJsonLine(line: string): string {
  const pattern =
    /"(?:\\.|[^"\\])*"(?=\s*:)|"(?:\\.|[^"\\])*"|-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?|\b(?:true|false|null)\b|[{}[\],:]/g
  let cursor = 0
  let output = ''

  for (const match of line.matchAll(pattern)) {
    const index = match.index || 0
    const token = match[0]
    output += escapeHtml(line.slice(cursor, index))

    let className = 'json-punctuation'
    if (token.startsWith('"')) {
      className = /^\s*:/.test(line.slice(index + token.length)) ? 'json-key' : 'json-string'
    } else if (/^-?\d/.test(token)) {
      className = 'json-number'
    } else if (token === 'true' || token === 'false') {
      className = 'json-boolean'
    } else if (token === 'null') {
      className = 'json-null'
    }

    output += `<span class="${className}">${escapeHtml(token)}</span>`
    cursor = index + token.length
  }

  return output + escapeHtml(line.slice(cursor))
}

const generatedJson = computed(() => JSON.stringify(exportConfig.value, null, 2))
const generatedLines = computed(() =>
  generatedJson.value.split('\n').map((line) => highlightJsonLine(line) || '&nbsp;'),
)

function localized(zh: string, en: string): string {
  return isEnglish.value ? en : zh
}

function makeDiagnostic(
  path: string,
  severity: Severity,
  zh: string,
  en: string,
  recoveryZh?: string,
  recoveryEn?: string,
): Diagnostic {
  return {
    path,
    severity,
    message: localized(zh, en),
    recovery: recoveryZh && recoveryEn ? localized(recoveryZh, recoveryEn) : undefined,
  }
}

function childPath(base: string, key: string): string {
  return base === '$' ? `$.${key}` : `${base}.${key}`
}

function hasDuplicates(values: unknown[]): boolean {
  const normalized = values.map((value) => JSON.stringify(value))
  return new Set(normalized).size !== normalized.length
}

function validateDomainArray(value: unknown, path: string, diagnostics: Diagnostic[]) {
  if (!Array.isArray(value)) {
    diagnostics.push(
      makeDiagnostic(path, 'error', '必须是域名字符串数组。', 'Must be an array of domain strings.', '改用 [\"home.example.com\"]。', 'Use [\"home.example.com\"].'),
    )
    return
  }
  if (hasDuplicates(value)) {
    diagnostics.push(
      makeDiagnostic(path, 'error', '包含重复域名。', 'Contains duplicate domains.', '删除重复项后重试。', 'Remove duplicate entries.'),
    )
  }
  value.forEach((domain, index) => {
    if (typeof domain !== 'string' || !DOMAIN_PATTERN.test(domain)) {
      diagnostics.push(
        makeDiagnostic(
          `${path}[${index}]`,
          'error',
          '域名格式无效。',
          'Domain name is invalid.',
          '请输入完整域名，也可以使用 *. 通配符前缀。',
          'Enter a fully qualified domain, optionally prefixed with *.',
        ),
      )
    }
  })
}

function validateAddressSource(value: unknown, path: string, diagnostics: Diagnostic[]) {
  if (typeof value === 'number' && Number.isInteger(value) && value >= 0) return
  if (typeof value !== 'string') {
    diagnostics.push(
      makeDiagnostic(
        path,
        'error',
        'IP 获取方式必须是字符串或非负网卡序号。',
        'IP detection method must be a string or non-negative interface index.',
      ),
    )
    return
  }

  const source = normalizeAddressSource(value)
  if (/^\d+$/.test(source) || ADDRESS_SOURCE_NAMES.has(source)) return
  const prefix = addressSourcePrefix(source)
  if (!prefix) {
    diagnostics.push(
      makeDiagnostic(
        path,
        'error',
        '不支持此 IP 获取方式。',
        'IP detection method is not supported.',
        '使用 public、default、local、非负网卡序号，或 url:、regex:、cmd:、shell: 前缀。',
        'Use public, default, local, a non-negative interface index, or a url:, regex:, cmd:, or shell: prefix.',
      ),
    )
    return
  }

  const payload = source.slice(prefix.length).trim()
  if (!payload) {
    diagnostics.push(
      makeDiagnostic(
        path,
        'error',
        `${prefix} 后必须提供内容。`,
        `${prefix} must be followed by a value.`,
      ),
    )
  } else if (prefix === 'url:' && !isValidHttpUrl(payload)) {
    diagnostics.push(
      makeDiagnostic(
        path,
        'error',
        'url: 后必须是包含主机名的 HTTP(S) URL。',
        'A url: method must contain an HTTP(S) URL with a hostname.',
      ),
    )
  }
}

function validateIndexValue(value: unknown, path: string, diagnostics: Diagnostic[]) {
  if (value === false) return
  if (value === true) {
    diagnostics.push(
      makeDiagnostic(
        path,
        'error',
        'true 不能作为 IP 获取方式；如需禁用此地址族，请使用 false。',
        'true cannot be used as an IP detection method. Use false to disable this address family.',
      ),
    )
    return
  }
  if (typeof value === 'number') {
    validateAddressSource(value, path, diagnostics)
    return
  }
  if (typeof value === 'string') {
    if (['false', 'none'].includes(value.trim().toLowerCase())) return
    const sources = splitIndexList(value)
    if (!sources.length) {
      diagnostics.push(
        makeDiagnostic(path, 'error', 'IP 获取方式不能为空。', 'IP detection method cannot be empty.'),
      )
      return
    }
    sources.forEach((source, index) =>
      validateAddressSource(source, sources.length === 1 ? path : `${path}[${index}]`, diagnostics),
    )
    return
  }
  if (!Array.isArray(value)) {
    diagnostics.push(
      makeDiagnostic(path, 'error', 'IP 获取方式的类型无效。', 'IP detection method type is invalid.', '使用字符串、非负网卡序号、布尔值或数组。', 'Use a string, non-negative interface index, boolean, or array.'),
    )
    return
  }
  if (!value.length) {
    diagnostics.push(
      makeDiagnostic(path, 'error', 'IP 获取方式列表不能为空。', 'IP detection method list cannot be empty.', '至少添加一种 IP 获取方式。', 'Add at least one IP detection method.'),
    )
  }
  if (hasDuplicates(value)) {
    diagnostics.push(
      makeDiagnostic(path, 'error', 'IP 获取方式存在重复项。', 'IP detection methods contain duplicates.', '删除重复项。', 'Remove duplicate entries.'),
    )
  }
  value.forEach((source, index) => validateAddressSource(source, `${path}[${index}]`, diagnostics))
}

function validateProxyValue(value: unknown, path: string, diagnostics: Diagnostic[]) {
  if (value === null) return
  const validateProxy = (proxy: unknown, itemPath: string) => {
    if (typeof proxy !== 'string' || !PROXY_PATTERN.test(proxy)) {
      diagnostics.push(
        makeDiagnostic(
          itemPath,
          'error',
          '代理格式无效。',
          'Proxy format is invalid.',
          '使用 http(s)://host:port、host:port、DIRECT、SYSTEM 或 DEFAULT。',
          'Use http(s)://host:port, host:port, DIRECT, SYSTEM, or DEFAULT.',
        ),
      )
    }
  }
  if (typeof value === 'string') {
    value.split(';').forEach((proxy, index) => validateProxy(proxy, `${path}[${index}]`))
    return
  }
  if (!Array.isArray(value)) {
    diagnostics.push(
      makeDiagnostic(path, 'error', '代理必须是字符串、数组或 null。', 'Proxy must be a string, array, or null.'),
    )
    return
  }
  if (hasDuplicates(value)) {
    diagnostics.push(
      makeDiagnostic(path, 'error', '代理列表包含重复项。', 'Proxy list contains duplicates.', '删除重复代理。', 'Remove duplicate proxies.'),
    )
  }
  value.forEach((proxy, index) => validateProxy(proxy, `${path}[${index}]`))
}

function validateLog(value: unknown, path: string, diagnostics: Diagnostic[], providerScoped: boolean) {
  if (!isPlainObject(value)) {
    diagnostics.push(makeDiagnostic(path, 'error', '日志配置必须是对象。', 'Log configuration must be an object.'))
    return
  }
  const allowed = providerScoped ? new Set(['level']) : new Set(['level', 'file', 'format', 'datefmt'])
  Object.keys(value).forEach((key) => {
    if (!allowed.has(key)) {
      diagnostics.push(
        makeDiagnostic(
          childPath(path, key),
          'error',
          '此日志字段不在 Schema v4.1 中。',
          'This log field is not part of Schema v4.1.',
          providerScoped ? '服务商级日志设置仅支持 level。' : '使用 level、file、format 或 datefmt。',
          providerScoped ? 'Provider-level log settings only support level.' : 'Use level, file, format, or datefmt.',
        ),
      )
    }
  })
  if ('level' in value && (typeof value.level !== 'string' || !LOG_LEVELS.includes(value.level))) {
    diagnostics.push(
      makeDiagnostic(
        childPath(path, 'level'),
        'error',
        '日志级别无效。',
        'Log level is invalid.',
        '使用 DEBUG、INFO、WARNING、ERROR 或 CRITICAL。',
        'Use DEBUG, INFO, WARNING, ERROR, or CRITICAL.',
      ),
    )
  }
  ;['file', 'format', 'datefmt'].forEach((key) => {
    if (key in value && value[key] !== null && typeof value[key] !== 'string') {
      diagnostics.push(
        makeDiagnostic(childPath(path, key), 'error', '必须是字符串或 null。', 'Must be a string or null.'),
      )
    }
  })
}

function validateReservedExtras(
  value: Record<string, unknown>,
  path: string,
  diagnostics: Diagnostic[],
) {
  Object.keys(value).forEach((key) => {
    if (!RESERVED_EXTRA_KEYS.has(key)) return
    diagnostics.push(
      makeDiagnostic(
        childPath(path, key),
        'error',
        `扩展字段 ${key} 与 DDNS 运行时参数冲突。`,
        `Custom field ${key} conflicts with a DDNS runtime argument.`,
        '移除此扩展字段，改用对应的配置项。',
        'Remove this custom field and use the corresponding configuration field.',
      ),
    )
  })
}

function validateReservedExtraAliases(
  value: Record<string, unknown>,
  path: string,
  diagnostics: Diagnostic[],
) {
  Object.keys(value).forEach((key) => {
    const extraKey = key.startsWith('extra_')
      ? key.slice(6)
      : key === 'domain' || key === 'value' || key === 'record_type'
        ? key
        : ''
    if (!extraKey || !RESERVED_EXTRA_KEYS.has(extraKey)) return
    validateReservedExtras({ [extraKey]: value[key] }, childPath(path, 'extra'), diagnostics)
  })
}

function parseHttpUrl(value: string): URL | undefined {
  try {
    return new URL(value.trim())
  } catch {
    return undefined
  }
}

function isValidHttpUrl(value: string): boolean {
  const url = parseHttpUrl(value)
  return Boolean(
    url && (url.protocol === 'http:' || url.protocol === 'https:') && url.hostname,
  )
}

function hasHttpUrlCredentials(value: string): boolean {
  const url = parseHttpUrl(value)
  return Boolean(url?.username || url?.password)
}

function validateCommonFields(
  value: Record<string, unknown>,
  path: string,
  diagnostics: Diagnostic[],
  providerScoped: boolean,
) {
  ;['id', 'endpoint', 'line'].forEach((key) => {
    if (key in value && value[key] !== null && typeof value[key] !== 'string') {
      diagnostics.push(
        makeDiagnostic(childPath(path, key), 'error', '必须是字符串或 null。', 'Must be a string or null.'),
      )
    }
  })
  if ('token' in value && typeof value.token !== 'string') {
    diagnostics.push(
      makeDiagnostic(childPath(path, 'token'), 'error', '必须是字符串。', 'Must be a string.'),
    )
  }
  if ('ipv4' in value) validateDomainArray(value.ipv4, childPath(path, 'ipv4'), diagnostics)
  if ('ipv6' in value) validateDomainArray(value.ipv6, childPath(path, 'ipv6'), diagnostics)
  if ('index4' in value) validateIndexValue(value.index4, childPath(path, 'index4'), diagnostics)
  if ('index6' in value) validateIndexValue(value.index6, childPath(path, 'index6'), diagnostics)
  if ('ttl' in value && value.ttl !== null && (typeof value.ttl !== 'number' || !Number.isFinite(value.ttl))) {
    diagnostics.push(
      makeDiagnostic(childPath(path, 'ttl'), 'error', 'TTL 必须是数字或 null。', 'TTL must be a number or null.'),
    )
  } else if (typeof value.ttl === 'number' && value.ttl < 0) {
    diagnostics.push(
      makeDiagnostic(childPath(path, 'ttl'), 'error', 'TTL 不能为负数。', 'TTL cannot be negative.'),
    )
  }
  if ('proxy' in value) validateProxyValue(value.proxy, childPath(path, 'proxy'), diagnostics)
  if ('cache' in value && typeof value.cache !== 'string' && typeof value.cache !== 'boolean') {
    diagnostics.push(
      makeDiagnostic(childPath(path, 'cache'), 'error', '缓存必须是布尔值或文件路径。', 'Cache must be a boolean or file path.'),
    )
  }
  if (
    'cache_max_age' in value &&
    (typeof value.cache_max_age !== 'number' ||
      !Number.isInteger(value.cache_max_age) ||
      value.cache_max_age < 0)
  ) {
    diagnostics.push(
      makeDiagnostic(
        childPath(path, 'cache_max_age'),
        'error',
        '缓存最长有效期必须是非负整数。',
        'Maximum cache age must be a non-negative integer.',
      ),
    )
  }
  if ('ssl' in value && typeof value.ssl !== 'string' && typeof value.ssl !== 'boolean') {
    diagnostics.push(
      makeDiagnostic(childPath(path, 'ssl'), 'error', 'SSL 设置必须是字符串或布尔值。', 'SSL setting must be a string or boolean.'),
    )
  }
  if ('log' in value) validateLog(value.log, childPath(path, 'log'), diagnostics, providerScoped)
  if (
    'log_level' in value &&
    !(
      (typeof value.log_level === 'string' && LOG_LEVELS.includes(value.log_level)) ||
      (typeof value.log_level === 'number' && Number.isInteger(value.log_level))
    )
  ) {
    diagnostics.push(
      makeDiagnostic(
        childPath(path, 'log_level'),
        'error',
        '日志级别无效。',
        'Log level is invalid.',
        '使用 DEBUG、INFO、WARNING、ERROR、CRITICAL 或整数级别。',
        'Use DEBUG, INFO, WARNING, ERROR, CRITICAL, or an integer level.',
      ),
    )
  }
  if (!providerScoped) {
    ;['log_file', 'log_format', 'log_datefmt'].forEach((key) => {
      if (key in value && value[key] !== null && typeof value[key] !== 'string') {
        diagnostics.push(
          makeDiagnostic(childPath(path, key), 'error', '必须是字符串或 null。', 'Must be a string or null.'),
        )
      }
    })
  }
  if (isPlainObject(value.log)) {
    const aliases: Record<string, string> = {
      level: 'log_level',
      file: 'log_file',
      format: 'log_format',
      datefmt: 'log_datefmt',
    }
    Object.keys(aliases).forEach((key) => {
      const alias = aliases[key]
      if (!(key in value.log) || !(alias in value)) return
      diagnostics.push(
        makeDiagnostic(
          childPath(path, alias),
          'error',
          '同一日志设置不能同时使用嵌套字段和扁平别名。',
          'The same log setting cannot use both a nested field and a flat alias.',
          `移除 ${alias} 或 log.${key} 其中一个。`,
          `Remove either ${alias} or log.${key}.`,
        ),
      )
    })
  }
  if (providerScoped) {
    ;['log_file', 'log_format', 'log_datefmt'].forEach((key) => {
      if (!(key in value)) return
      diagnostics.push(
        makeDiagnostic(
          childPath(path, key),
          'error',
          '日志文件和格式只能在全局配置中设置。',
          'Log file and format settings can only be configured globally.',
          '请在全局配置中设置对应的 log.file、log.format 或 log.datefmt。',
          'Set the corresponding log.file, log.format, or log.datefmt value in the global configuration.',
        ),
      )
    })
  }
  if ('extra' in value) {
    if (!isPlainObject(value.extra)) {
      diagnostics.push(
        makeDiagnostic(childPath(path, 'extra'), 'error', '扩展字段必须是 JSON 对象。', 'Custom fields must be a JSON object.'),
      )
    } else {
      validateReservedExtras(value.extra, childPath(path, 'extra'), diagnostics)
    }
  }
  validateReservedExtraAliases(value, path, diagnostics)
  if (
    typeof value.endpoint === 'string' &&
    value.endpoint &&
    !isValidHttpUrl(value.endpoint)
  ) {
    diagnostics.push(
      makeDiagnostic(
        childPath(path, 'endpoint'),
        'error',
        '端点必须是包含主机名的 HTTP(S) URL。',
        'Endpoint must be an HTTP(S) URL with a hostname.',
        '使用类似 https://api.example.com 的完整地址。',
        'Use a complete address such as https://api.example.com.',
      ),
    )
  }
}

function validateProviderRuntime(
  provider: Record<string, unknown>,
  path: string,
  diagnostics: Diagnostic[],
) {
  const providerName = typeof provider.provider === 'string' ? provider.provider : ''
  const meta = providerMap.get(providerName)
  if (!meta) return
  const rawId = typeof provider.id === 'string' ? provider.id : ''
  const id = rawId.trim()
  const token = typeof provider.token === 'string' ? provider.token : ''
  const endpoint = typeof provider.endpoint === 'string' ? provider.endpoint.trim() : ''
  const idBlocksEnvironment = 'id' in provider && !id
  const tokenBlocksEnvironment = 'token' in provider && !token

  if (meta.testOnly) {
    diagnostics.push(
      makeDiagnostic(
        childPath(path, 'provider'),
        'warning',
        'Debug 仅打印更新结果，不会修改实际 DNS 记录。',
        'Debug only prints update results and does not change live DNS records.',
        '测试完成后，请在部署前选择实际使用的 DNS 服务商。',
        'After testing, select the DNS provider you intend to use before deployment.',
      ),
    )
  }

  if (meta.auth === 'id-token') {
    if (!id) {
      diagnostics.push(
        makeDiagnostic(
          childPath(path, 'id'),
          idBlocksEnvironment ? 'error' : 'warning',
          idBlocksEnvironment
            ? 'ID 为空字符串，因此运行时不会读取 DDNS_ID。'
            : '导出的配置中不包含 ID；部署时需通过 DDNS_ID 提供。',
          idBlocksEnvironment
            ? 'ID is an empty string, so DDNS_ID will not be used at runtime.'
            : 'ID is not included in the exported configuration. Provide it through DDNS_ID at runtime.',
          idBlocksEnvironment ? '删除 id 字段以使用环境变量，或填写 ID。' : '填写 ID，或确认部署环境已设置 DDNS_ID。',
          idBlocksEnvironment
            ? 'Remove the id field to use DDNS_ID, or enter an ID.'
            : 'Enter an ID, or confirm that DDNS_ID is set in the deployment environment.',
        ),
      )
    }
    if (!token) {
      diagnostics.push(
        makeDiagnostic(
          childPath(path, 'token'),
          tokenBlocksEnvironment ? 'error' : 'warning',
          tokenBlocksEnvironment
            ? 'Token 为空字符串，因此运行时不会读取 DDNS_TOKEN。'
            : '导出的配置中不包含 Token；部署时需通过 DDNS_TOKEN 提供。',
          tokenBlocksEnvironment
            ? 'Token is an empty string, so DDNS_TOKEN will not be used at runtime.'
            : 'Token is not included in the exported configuration. Provide it through DDNS_TOKEN at runtime.',
          tokenBlocksEnvironment
            ? '删除 token 字段以使用环境变量，或填写 Token。'
            : '填写 Token，或确认部署环境已设置 DDNS_TOKEN。',
          tokenBlocksEnvironment
            ? 'Remove the token field to use DDNS_TOKEN, or enter a token.'
            : 'Enter a token, or confirm that DDNS_TOKEN is set in the deployment environment.',
        ),
      )
    }
  } else if ((meta.auth === 'token' || meta.auth === 'flexible') && !token) {
    diagnostics.push(
      makeDiagnostic(
        childPath(path, 'token'),
        tokenBlocksEnvironment ? 'error' : 'warning',
        tokenBlocksEnvironment
          ? 'Token 为空字符串，因此运行时不会读取 DDNS_TOKEN。'
          : '导出的配置中不包含 Token；部署时需通过 DDNS_TOKEN 提供。',
        tokenBlocksEnvironment
          ? 'Token is an empty string, so DDNS_TOKEN will not be used at runtime.'
          : 'Token is not included in the exported configuration. Provide it through DDNS_TOKEN at runtime.',
        tokenBlocksEnvironment
          ? '删除 token 字段以使用环境变量，或填写 Token。'
          : '填写 Token，或确认部署环境已设置 DDNS_TOKEN。',
        tokenBlocksEnvironment
          ? 'Remove the token field to use DDNS_TOKEN, or enter a token.'
          : 'Enter a token, or confirm that DDNS_TOKEN is set in the deployment environment.',
      ),
    )
  }

  if (providerName === 'he' && rawId.length > 0) {
    diagnostics.push(
      makeDiagnostic(
        childPath(path, 'id'),
        'error',
        'HE.net 不使用 ID。',
        'HE.net does not use an ID.',
        '删除 ID，仅在 Token 中填写 DDNS Key。',
        'Remove the ID and enter the DDNS key in Token.',
      ),
    )
  }
  if (providerName === 'cloudflare' && id && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(id)) {
    diagnostics.push(
      makeDiagnostic(
        childPath(path, 'id'),
        'error',
        'Cloudflare ID 必须为空或有效邮箱。',
        'Cloudflare ID must be empty or a valid email address.',
        'API Token 模式请留空；Global API Key 模式请填写账户邮箱。',
        'Leave it empty for API Token, or enter the account email for Global API Key.',
      ),
    )
  }
  if (meta.auth === 'callback') {
    const idIsUrl = isValidHttpUrl(id)
    if (!id) {
      diagnostics.push(
        makeDiagnostic(
          childPath(path, 'id'),
          idBlocksEnvironment ? 'error' : 'warning',
          idBlocksEnvironment
            ? 'Callback URL 为空字符串，因此运行时不会读取 DDNS_ID。'
            : '导出的配置中不包含 Callback URL；部署时需通过 DDNS_ID 提供。',
          idBlocksEnvironment
            ? 'Callback URL is an empty string, so DDNS_ID will not be used at runtime.'
            : 'Callback URL is not included in the exported configuration. Provide it through DDNS_ID at runtime.',
          idBlocksEnvironment
            ? '删除 id 字段以使用环境变量，或填写 Callback URL。'
            : '确认部署环境已设置 DDNS_ID，或开启“导出时包含凭据”。',
          idBlocksEnvironment
            ? 'Remove the id field to use DDNS_ID, or enter a Callback URL.'
            : 'Confirm that DDNS_ID is set in the deployment environment, or enable “Include credentials in exports.”',
        ),
      )
    } else if (!idIsUrl) {
      diagnostics.push(
        makeDiagnostic(
          childPath(path, 'id'),
          'error',
          'Callback 的 ID 必须是包含主机名的 HTTP(S) URL。',
          'Callback ID must be an HTTP(S) URL with a hostname.',
          '例如 https://api.example.com/update。',
          'For example, https://api.example.com/update.',
        ),
      )
    }
    if (endpoint) {
      diagnostics.push(
        makeDiagnostic(
          childPath(path, 'endpoint'),
          'error',
          'Callback 不支持 endpoint 字段。',
          'Callback does not support the endpoint field.',
          '清空 endpoint，并将完整 URL 填入 ID。',
          'Clear endpoint and enter the complete URL in ID.',
        ),
      )
    }
    if (token) {
      try {
        const body: unknown = JSON.parse(token)
        if (!isPlainObject(body)) {
          diagnostics.push(
            makeDiagnostic(
              childPath(path, 'token'),
              'error',
              'Callback 的 POST 请求体必须是 JSON 对象字符串。',
              'Callback POST body must be a JSON object encoded as a string.',
              '例如 {\"api_key\":\"secret\"}；如需使用 GET，请留空。',
              'For example, {\"api_key\":\"secret\"}. Leave it blank to use GET.',
            ),
          )
        }
      } catch {
        diagnostics.push(
          makeDiagnostic(
            childPath(path, 'token'),
            'error',
            'Callback POST 请求体不是有效 JSON。',
            'Callback POST body is not valid JSON.',
            '填写 JSON 对象字符串，或留空改用 GET。',
            'Enter a JSON object string, or leave it empty to use GET.',
          ),
        )
      }
    }
  }

  const recordTotal =
    (Array.isArray(provider.ipv4) ? provider.ipv4.length : 0) +
    (Array.isArray(provider.ipv6) ? provider.ipv6.length : 0)
  if (recordTotal === 0) {
    diagnostics.push(
      makeDiagnostic(
        path,
        'warning',
        '没有配置要更新的 IPv4 或 IPv6 域名。',
        'No IPv4 or IPv6 domains are configured.',
        '至少添加一条域名记录，除非只想测试地址检测。',
        'Add at least one domain unless you only intend to test address detection.',
      ),
    )
  }
}

function missingEmbeddedCredential(provider: ProviderState): 'id' | 'token' | undefined {
  const auth = providerMap.get(provider.provider)?.auth
  if (auth === 'id-token') {
    if (!provider.id.trim()) return 'id'
    if (!provider.token) return 'token'
  } else if (auth === 'token' || auth === 'flexible') {
    if (!provider.token) return 'token'
  } else if (auth === 'callback' && !provider.id.trim()) {
    return 'id'
  }
  return undefined
}

function validateConfig(value: unknown): Diagnostic[] {
  const diagnostics: Diagnostic[] = []
  if (!isPlainObject(value)) {
    return [
      makeDiagnostic(
        '$',
        'error',
        '配置顶层必须是 JSON 对象。',
        'The top-level configuration must be a JSON object.',
        '使用 { ... } 包裹配置字段。',
        'Wrap configuration fields in { ... }.',
      ),
    ]
  }

  if ('$schema' in value && (typeof value.$schema !== 'string' || !SCHEMA_VALUES.includes(value.$schema))) {
    diagnostics.push(
      makeDiagnostic(
        '$.$schema',
        'error',
        'Schema URL 不是受支持的 v4.1 地址。',
        'Schema URL is not recognized for v4.1.',
        `使用 ${SCHEMA_URL}。`,
        `Use ${SCHEMA_URL}.`,
      ),
    )
  }

  const hasProviders = 'providers' in value
  const conflictingKeys = LEGACY_PROVIDER_KEYS.filter((key) => key in value)
  if (hasProviders && conflictingKeys.length) {
    diagnostics.push(
      makeDiagnostic(
        '$',
        'error',
        `providers 不能与 ${conflictingKeys.join(', ')} 同时使用。`,
        `providers cannot be combined with ${conflictingKeys.join(', ')}.`,
        '把服务商字段移入 providers 数组。',
        'Move provider-specific fields into the providers array.',
      ),
    )
  }

  if (hasProviders) {
    if (!Array.isArray(value.providers)) {
      diagnostics.push(
        makeDiagnostic('$.providers', 'error', 'providers 必须是数组。', 'providers must be an array.'),
      )
    } else {
      if (!value.providers.length) {
        diagnostics.push(
          makeDiagnostic(
            '$.providers',
            'warning',
            '服务商列表为空。',
            'Provider list is empty.',
            '至少添加一个服务商。',
            'Add at least one provider.',
          ),
        )
      }
      value.providers.forEach((provider, index) => {
        const path = `$.providers[${index}]`
        if (!isPlainObject(provider)) {
          diagnostics.push(
            makeDiagnostic(path, 'error', '服务商配置必须是对象。', 'Provider configuration must be an object.'),
          )
          return
        }
        if ('dns' in provider) {
          diagnostics.push(
            makeDiagnostic(
              childPath(path, 'dns'),
              'error',
              'providers 数组中的服务商必须使用 provider 字段，不能使用 dns。',
              'Use provider, not dns, for entries in the providers array.',
              '将 dns 改为 provider。',
              'Replace dns with provider.',
            ),
          )
        }
        if (typeof provider.provider !== 'string' || !providerMap.has(provider.provider)) {
          diagnostics.push(
            makeDiagnostic(
              childPath(path, 'provider'),
              'error',
              '缺少或不支持此服务商标识。',
              'Provider identifier is missing or unsupported.',
              '从受支持的服务商列表中选择。',
              'Choose a supported provider.',
            ),
          )
        }
        validateCommonFields(provider, path, diagnostics, true)
        validateProviderRuntime(provider, path, diagnostics)
      })
    }
  } else {
    if (!('token' in value)) {
      diagnostics.push(
        makeDiagnostic(
          '$.token',
          'error',
          '单服务商格式必须包含 token；也可以改用 providers 数组。',
          'The single-provider format must include token. You can also use a providers array.',
        ),
      )
    }
    if (!('dns' in value)) {
      diagnostics.push(
        makeDiagnostic(
          '$.dns',
          'warning',
          '未指定 DNS 服务商；运行时必须通过命令行或环境变量提供。',
          'DNS provider is missing and must be supplied by CLI or environment at runtime.',
          '添加 dns 字段后，才能将此配置载入可视化编辑器。',
          'Add a dns field before loading this configuration into the visual editor.',
        ),
      )
    } else if (typeof value.dns !== 'string' || !providerMap.has(value.dns)) {
      diagnostics.push(
        makeDiagnostic('$.dns', 'error', 'DNS 服务商标识无效。', 'DNS provider identifier is invalid.'),
      )
    }
    const legacyProvider: Record<string, unknown> = { ...value, provider: value.dns }
    validateProviderRuntime(legacyProvider, '$', diagnostics)
  }

  validateCommonFields(value, '$', diagnostics, false)
  return diagnostics
}

function validateObjectEditor(text: string, path: string): Diagnostic[] {
  if (!text.trim()) return []
  try {
    const parsed: unknown = JSON.parse(stripJsonComments(text))
    if (!isPlainObject(parsed)) {
      return [
        makeDiagnostic(path, 'error', '请输入 JSON 对象。', 'Enter a JSON object.', '使用 { \"key\": \"value\" }。', 'Use { \"key\": \"value\" }.'),
      ]
    }
    const diagnostics: Diagnostic[] = []
    validateReservedExtras(parsed, path, diagnostics)
    return diagnostics
  } catch {
    return [
      makeDiagnostic(
        path,
        'error',
        'JSON 对象语法无效。',
        'JSON object syntax is invalid.',
        '检查引号、逗号与括号。',
        'Check quotes, commas, and braces.',
      ),
    ]
  }
}

function validateRuntimeEditorState(
  state: RuntimeEditorState,
  path: string,
  diagnostics: Diagnostic[],
) {
  diagnostics.push(...validateObjectEditor(state.extraText, childPath(path, 'extra')))
  const cacheMaxAge = state.cacheMaxAge.trim()
  if (cacheMaxAge && !Number.isInteger(Number(cacheMaxAge))) {
    diagnostics.push(
      makeDiagnostic(
        childPath(path, 'cache_max_age'),
        'error',
        '缓存最长有效期必须是非负整数。',
        'Maximum cache age must be a non-negative integer.',
      ),
    )
  }
  if (state.cacheMode === 'path' && !state.cachePath.trim()) {
    diagnostics.push(
      makeDiagnostic(
        childPath(path, 'cache'),
        'error',
        '指定缓存文件时路径不能为空。',
        'Cache path cannot be empty when file mode is selected.',
      ),
    )
  }
  if (state.sslMode === 'custom' && !state.sslPath.trim()) {
    diagnostics.push(
      makeDiagnostic(
        childPath(path, 'ssl'),
        'error',
        '自定义 CA 文件路径不能为空。',
        'Custom CA file path cannot be empty.',
      ),
    )
  }
}

function validateFormState(): Diagnostic[] {
  const diagnostics: Diagnostic[] = []
  validateRuntimeEditorState(globalState, '$', diagnostics)

  providers.value.forEach((provider, index) => {
    const path = `$.providers[${index}]`
    validateRuntimeEditorState(provider, path, diagnostics)
    if (provider.ttl.trim() && !Number.isFinite(Number(provider.ttl))) {
      diagnostics.push(
        makeDiagnostic(`${path}.ttl`, 'error', 'TTL 必须是非负数字。', 'TTL must be a non-negative number.'),
      )
    }
  })
  return diagnostics
}

function dedupeDiagnostics(items: Diagnostic[]): Diagnostic[] {
  const seen = new Set<string>()
  return items
    .filter((item) => {
      const key = `${item.severity}:${item.path}:${item.message}`
      if (seen.has(key)) return false
      seen.add(key)
      return true
    })
    .sort((left, right) => {
      if (left.severity !== right.severity) return left.severity === 'error' ? -1 : 1
      return left.path.localeCompare(right.path)
    })
}

const previewDiagnostics = computed(() => {
  const diagnostics = [...validateConfig(exportConfig.value), ...validateFormState()]
  let runtimeCredentialIndex: number | undefined
  let runtimeCredentialField = 'provider'
  if (credentialProviderIndexes.value.length > 1) {
    if (!includeCredentials.value) {
      runtimeCredentialIndex = credentialProviderIndexes.value[1]
    } else {
      runtimeCredentialIndex = credentialProviderIndexes.value.find((index) => {
        return Boolean(missingEmbeddedCredential(providers.value[index]!))
      })
      if (runtimeCredentialIndex !== undefined) {
        runtimeCredentialField = missingEmbeddedCredential(providers.value[runtimeCredentialIndex]!) || 'provider'
      }
    }
  }
  if (runtimeCredentialIndex !== undefined) {
    diagnostics.push(
      makeDiagnostic(
        `$.providers[${runtimeCredentialIndex}].${runtimeCredentialField}`,
        'warning',
        includeCredentials.value
          ? '部分服务商的凭据不完整。'
          : '多个需认证的服务商将读取同一组运行时凭据。',
        includeCredentials.value
          ? 'Some providers have incomplete credentials.'
          : 'Multiple authenticated providers will read the same runtime credentials.',
        includeCredentials.value
          ? '请逐项检查并补全各服务商的凭据。'
          : '确认这些服务商有意共用同一账户；否则开启“导出时包含凭据”并分别填写。',
        includeCredentials.value
          ? 'Review and complete the credentials for each provider.'
          : 'Confirm these providers intentionally share one account. Otherwise, enable “Include credentials in exports” and enter credentials for each provider.',
      ),
    )
  }
  return dedupeDiagnostics(diagnostics)
})
const previewErrors = computed(() => previewDiagnostics.value.filter((item) => item.severity === 'error'))
const previewWarnings = computed(() => previewDiagnostics.value.filter((item) => item.severity === 'warning'))
const canExport = computed(() => previewErrors.value.length === 0)
const schemaStatusLabel = computed(() => {
  if (previewErrors.value.length) {
    return `${previewErrors.value.length} ${errorToFixUnit(previewErrors.value.length)}`
  }
  return c.value.schemaValid
})
const deploymentStatusLabel = computed(() => {
  if (previewErrors.value.length) return c.value.deploymentBlocked
  const remainingWarnings = Math.max(0, previewWarnings.value.length - testProviderCount.value)
  if (hasTestOnlyProviders.value) {
    if (remainingWarnings) {
      return `${c.value.testOnlyMode} · ${remainingWarnings} ${checkToReviewUnit(remainingWarnings)}`
    }
    return c.value.testOnlyMode
  }
  if (previewWarnings.value.length) {
    return `${previewWarnings.value.length} ${checkToReviewUnit(previewWarnings.value.length)}`
  }
  return c.value.deploymentConfigured
})
const assuranceStateKey = computed(
  () =>
    `${previewErrors.value.length}-${previewWarnings.value.length}-${testProviderCount.value}-${providers.value.length}`,
)
const exportStatusLabel = computed(() => {
  if (previewErrors.value.length) return c.value.outputBlocked
  if (previewWarnings.value.length) return c.value.outputWarning
  return c.value.outputReady
})

function providerFieldPath(key: string): string {
  return `$.providers[${selectedProviderIndex.value}].${key}`
}

function providerFieldId(key: string): string {
  return `studio-provider-${selectedProvider.value.uid}-${key}`
}

function globalFieldPath(key: string): string {
  return `$.${key}`
}

function globalFieldId(key: string): string {
  return `studio-global-${key}`
}

const fieldDiagnosticMap = computed(() => {
  const diagnostics = new Map<string, Diagnostic>()
  previewDiagnostics.value.forEach((diagnostic) => {
    let path = diagnostic.path
    while (path && path !== '$') {
      if (!diagnostics.has(path)) diagnostics.set(path, diagnostic)
      const parent = path.replace(/(?:\[[^\]]+\]|\.[^.[\]]+)$/, '')
      if (parent === path) break
      path = parent
    }
  })
  return diagnostics
})

function fieldDiagnostic(path: string): Diagnostic | undefined {
  return fieldDiagnosticMap.value.get(path)
}

function fieldFeedbackId(path: string): string {
  return `studio-feedback-${path.replace(/[^a-zA-Z0-9]+/g, '-').replace(/^-|-$/g, '')}`
}

function fieldInvalid(path: string): 'true' | undefined {
  return fieldDiagnostic(path)?.severity === 'error' ? 'true' : undefined
}

function fieldDescription(path: string): string | undefined {
  return fieldDiagnostic(path) ? fieldFeedbackId(path) : undefined
}

function diagnosticFieldKey(path: string): string {
  const providerMatch = path.match(/^\$\.providers\[\d+\](?:\.([a-zA-Z0-9_]+))?/)
  const rootMatch = path.match(/^\$\.([a-zA-Z0-9_]+)/)
  const key = providerMatch?.[1] || rootMatch?.[1] || 'provider'
  const aliases: Record<string, string> = {
    cache_max_age: 'cache-age',
    log: 'log-level',
    log_level: 'log-level',
  }
  return aliases[key] || key
}

function diagnosticTargetId(path: string): string | undefined {
  const providerMatch = path.match(/^\$\.providers\[(\d+)\]/)
  if (providerMatch) {
    const provider = providers.value[Number(providerMatch[1])]
    if (!provider) return undefined
    return `studio-provider-${provider.uid}-${diagnosticFieldKey(path)}`
  }
  if (/^\$\.[a-zA-Z0-9_]+/.test(path)) {
    return globalFieldId(diagnosticFieldKey(path))
  }
  return undefined
}

function openAdvancedForPath(path: string) {
  if (/\.endpoint(?:$|[.[\]])/.test(path)) providerAdvancedOpen.value = true
  if (/\.(?:index4|index6|ttl|line)(?:$|[.[\]])/.test(path)) sourceAdvancedOpen.value = true
  if (/\.ssl(?:$|[.[\]])/.test(path)) networkAdvancedOpen.value = true
  if (/\.(?:cache|cache_max_age|log|extra)(?:$|[.[\]])/.test(path)) {
    runtimeAdvancedOpen.value = true
  }
}

async function focusDiagnostic(diagnostic: Diagnostic) {
  const providerMatch = diagnostic.path.match(/^\$\.providers\[(\d+)\]/)
  if (providerMatch) {
    const provider = providers.value[Number(providerMatch[1])]
    if (provider) selectedUid.value = provider.uid
  }
  activeSection.value = sectionForPath(diagnostic.path)
  openAdvancedForPath(diagnostic.path)
  if (mobileReviewOpen.value) mobileReviewOpen.value = false
  await nextTick()
  const targetId = diagnosticTargetId(diagnostic.path)
  if (targetId) document.getElementById(targetId)?.focus()
}

function emptyIssueSummary(): IssueSummary {
  return { errors: 0, warnings: 0 }
}

function sectionForPath(path: string): SectionKey {
  if (/\.(?:ipv4|ipv6|index4|index6|ttl|line)(?:$|[.[\]])/.test(path)) return 'records'
  if (/\.(?:proxy|ssl)(?:$|[.[\]])/.test(path)) return 'network'
  if (/\.(?:cache|cache_max_age|log|extra)(?:$|[.[\]])/.test(path)) return 'runtime'
  return 'provider'
}

const providerIssueMap = computed(() => {
  const summaries = new Map<number, IssueSummary>()
  providers.value.forEach((provider) => summaries.set(provider.uid, emptyIssueSummary()))

  previewDiagnostics.value.forEach((diagnostic) => {
    const match = diagnostic.path.match(/^\$\.providers\[(\d+)\]/)
    if (!match) return
    const provider = providers.value[Number(match[1])]
    if (!provider) return
    const summary = summaries.get(provider.uid)
    if (!summary) return
    if (diagnostic.severity === 'error') summary.errors += 1
    else summary.warnings += 1
  })
  return summaries
})

const selectedSectionIssues = computed<Record<SectionKey, IssueSummary>>(() => {
  const summaries: Record<SectionKey, IssueSummary> = {
    provider: emptyIssueSummary(),
    records: emptyIssueSummary(),
    network: emptyIssueSummary(),
    runtime: emptyIssueSummary(),
  }
  const selectedIndex = providers.value.findIndex((provider) => provider.uid === selectedUid.value)

  previewDiagnostics.value.forEach((diagnostic) => {
    const providerMatch = diagnostic.path.match(/^\$\.providers\[(\d+)\]/)
    if (providerMatch && Number(providerMatch[1]) !== selectedIndex) return
    const summary = summaries[sectionForPath(diagnostic.path)]
    if (diagnostic.severity === 'error') summary.errors += 1
    else summary.warnings += 1
  })
  return summaries
})

function providerIssueClass(uid: number): Record<string, boolean> {
  const summary = providerIssueMap.value.get(uid) || emptyIssueSummary()
  return {
    'has-errors': summary.errors > 0,
    'has-warnings': summary.errors === 0 && summary.warnings > 0,
  }
}

function providerIssueLabel(uid: number): string {
  const summary = providerIssueMap.value.get(uid) || emptyIssueSummary()
  if (summary.errors) return `${summary.errors} ${errorCountUnit(summary.errors)}`
  if (summary.warnings) return `${summary.warnings} ${warningCountUnit(summary.warnings)}`
  return ''
}

function sectionIssueTotal(section: SectionKey): number {
  const summary = selectedSectionIssues.value[section]
  return summary.errors + summary.warnings
}

function sectionIssueTone(section: SectionKey): string {
  return selectedSectionIssues.value[section].errors ? 'is-error' : 'is-warning'
}

function parseConfiguration(source: string): ParsedConfiguration {
  const cleaned = stripJsonComments(source)
  try {
    const value: unknown = JSON.parse(cleaned)
    return { value, diagnostics: validateConfig(value) }
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error)
    const positionMatch = message.match(/position\s+(\d+)/i)
    let location = ''
    if (positionMatch) {
      const position = Number(positionMatch[1])
      const before = cleaned.slice(0, position)
      const lineNumber = before.split(/\r?\n/).length
      const column = position - Math.max(before.lastIndexOf('\n'), before.lastIndexOf('\r'))
      location = localized(`（第 ${lineNumber} 行，第 ${column} 列）`, ` (line ${lineNumber}, column ${column})`)
    }
    return {
      value: null,
      diagnostics: [
        makeDiagnostic(
          '$',
          'error',
          `JSON 语法错误${location}。`,
          `JSON syntax error${location}.`,
          '检查引号、逗号与括号；仅支持 // 与 # 单行注释。',
          'Check quotes, commas, and braces; only // and # single-line comments are supported.',
        ),
      ],
    }
  }
}

const parsedValidation = computed(() => parseConfiguration(validationInput.value))
const validationDiagnostics = computed(() => dedupeDiagnostics(parsedValidation.value.diagnostics))
const validationErrors = computed(() => validationDiagnostics.value.filter((item) => item.severity === 'error'))
const validationWarnings = computed(() => validationDiagnostics.value.filter((item) => item.severity === 'warning'))
const validationLineCount = computed(() => validationInput.value.split(/\r?\n/).length)
const validationCanApply = computed(() => {
  const value = parsedValidation.value.value
  if (validationErrors.value.length || !isPlainObject(value)) return false
  if (Array.isArray(value.providers)) {
    return (
      value.providers.length > 0 &&
      value.providers.every(
        (provider) =>
          isPlainObject(provider) &&
          typeof provider.provider === 'string' &&
          providerMap.has(provider.provider),
      )
    )
  }
  return typeof value.dns === 'string' && providerMap.has(value.dns)
})

watch(selectedUid, () => {
  providerPickerOpen.value = false
  providerQuery.value = ''
})

watch(activeSection, (section) => {
  if (section !== 'provider') {
    providerPickerOpen.value = false
    providerQuery.value = ''
  }
})

async function toggleProviderPicker() {
  if (providerPickerOpen.value) {
    providerPickerOpen.value = false
    providerQuery.value = ''
    return
  }
  providerPickerOpen.value = true
  providerQuery.value = ''
  await nextTick()
  providerSearchInput.value?.focus()
}

async function closeProviderPicker(restoreFocus = true) {
  providerPickerOpen.value = false
  providerQuery.value = ''
  if (!restoreFocus) return
  await nextTick()
  providerPickerTrigger.value?.focus()
}

function handleProviderPickerKeydown(event: KeyboardEvent) {
  if (event.key !== 'Escape') return
  event.preventDefault()
  closeProviderPicker()
}

async function selectInspectorTab(tab: InspectorTab, focusTab = false) {
  if (tab === 'validate' && !validatorTouched.value) {
    validationInput.value = generatedJson.value
  }
  inspectorTab.value = tab
  if (!focusTab) return
  await nextTick()
  document.getElementById(`studio-tab-${tab}`)?.focus()
}

function handleInspectorTabKeydown(event: KeyboardEvent) {
  const tabs: InspectorTab[] = ['preview', 'validate']
  const currentIndex = tabs.indexOf(inspectorTab.value)
  let nextIndex = currentIndex
  if (event.key === 'ArrowRight') nextIndex = (currentIndex + 1) % tabs.length
  else if (event.key === 'ArrowLeft') nextIndex = (currentIndex - 1 + tabs.length) % tabs.length
  else if (event.key === 'Home') nextIndex = 0
  else if (event.key === 'End') nextIndex = tabs.length - 1
  else return
  event.preventDefault()
  selectInspectorTab(tabs[nextIndex], true)
}

async function openMobileReview() {
  inspectorTab.value = 'preview'
  mobileReviewOpen.value = true
  await nextTick()
  mobileReviewCloseButton.value?.focus()
}

async function closeMobileReview(restoreFocus = true) {
  mobileReviewOpen.value = false
  if (!restoreFocus) return
  await nextTick()
  mobileReviewButton.value?.focus()
}

function handleMobileReviewKeydown(event: KeyboardEvent) {
  if (!mobileReviewOpen.value) return
  if (event.key === 'Escape') {
    event.preventDefault()
    closeMobileReview()
    return
  }
  if (event.key !== 'Tab' || !mobileReviewPanel.value) return

  const focusable = Array.from(
    mobileReviewPanel.value.querySelectorAll<HTMLElement>(
      'a[href], button:not(:disabled), input:not(:disabled), textarea:not(:disabled), select:not(:disabled), [tabindex]:not([tabindex="-1"])',
    ),
  ).filter((element) => element.offsetParent !== null)
  if (!focusable.length) return

  const first = focusable[0]
  const last = focusable[focusable.length - 1]
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault()
    last.focus()
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault()
    first.focus()
  }
}

watch(mobileReviewOpen, (isOpen) => {
  if (typeof document === 'undefined') return
  document.body.classList.toggle('config-studio-review-open', isOpen)
})

function handleMobileReviewResize() {
  if (window.innerWidth > 840 && mobileReviewOpen.value) closeMobileReview(false)
}

onMounted(() => {
  window.addEventListener('resize', handleMobileReviewResize)
})

onBeforeUnmount(() => {
  if (toastTimer) clearTimeout(toastTimer)
  window.removeEventListener('resize', handleMobileReviewResize)
  if (typeof document !== 'undefined') {
    document.body.classList.remove('config-studio-review-open')
  }
})

function addProvider() {
  const provider = makeProvider('dnspod')
  provider.ipv4Text = ''
  providers.value.push(provider)
  selectedUid.value = provider.uid
  activeSection.value = 'provider'
  showToast(c.value.providerAdded)
}

function removeProvider(uid: number) {
  if (providers.value.length === 1) return
  const index = providers.value.findIndex((provider) => provider.uid === uid)
  const removed = providers.value[index]
  if (!removed) return
  lastRemovedProvider.value = {
    index,
    provider: { ...removed, revealToken: false },
  }
  providers.value = providers.value.filter((provider) => provider.uid !== uid)
  const focusProvider = providers.value[Math.min(index, providers.value.length - 1)]
  if (selectedUid.value === uid) {
    selectedUid.value = focusProvider.uid
  }
  showToast(c.value.providerRemoved, 'success', 6000, true)
  nextTick(() => {
    document
      .querySelector<HTMLButtonElement>(
        `.provider-select-button[data-provider-uid="${focusProvider.uid}"]`,
      )
      ?.focus()
  })
}

function restoreRemovedProvider() {
  if (!lastRemovedProvider.value) return
  const { index, provider } = lastRemovedProvider.value
  providers.value.splice(Math.min(index, providers.value.length), 0, provider)
  selectedUid.value = provider.uid
  lastRemovedProvider.value = null
  showToast(c.value.providerRestored)
  nextTick(() => {
    document
      .querySelector<HTMLButtonElement>(
        `.provider-select-button[data-provider-uid="${provider.uid}"]`,
      )
      ?.focus()
  })
}

function duplicateProvider() {
  const source = selectedProvider.value
  const hasSensitiveEndpoint = hasHttpUrlCredentials(source.endpoint)
  const duplicate: ProviderState = {
    ...source,
    uid: nextProviderUid++,
    id: '',
    idPresent: false,
    idNull: false,
    token: '',
    tokenPresent: false,
    endpoint: hasSensitiveEndpoint ? '' : source.endpoint,
    endpointPresent: hasSensitiveEndpoint ? false : source.endpointPresent,
    endpointNull: hasSensitiveEndpoint ? false : source.endpointNull,
    index4Text: stripSensitiveAddressSources(source.index4Text),
    index6Text: stripSensitiveAddressSources(source.index6Text),
    revealToken: false,
  }
  const index = providers.value.findIndex((provider) => provider.uid === source.uid)
  providers.value.splice(index + 1, 0, duplicate)
  selectedUid.value = duplicate.uid
  showToast(c.value.providerDuplicated)
}

async function chooseProvider(provider: string) {
  if (provider === selectedProvider.value.provider) {
    await closeProviderPicker()
    return
  }
  selectedProvider.value.provider = provider
  selectedProvider.value.id = ''
  selectedProvider.value.idPresent = false
  selectedProvider.value.idNull = false
  selectedProvider.value.token = ''
  selectedProvider.value.tokenPresent = false
  selectedProvider.value.endpoint = ''
  selectedProvider.value.endpointPresent = false
  selectedProvider.value.endpointNull = false
  selectedProvider.value.extraText = ''
  selectedProvider.value.revealToken = false
  showToast(c.value.providerChanged)
  await closeProviderPicker()
}

function resetBuilder() {
  if (typeof window !== 'undefined' && !window.confirm(c.value.confirmReset)) return
  const provider = makeProvider()
  providers.value = [provider]
  selectedUid.value = provider.uid
  activeSection.value = 'provider'
  inspectorTab.value = 'preview'
  includeCredentials.value = false
  providerAdvancedOpen.value = false
  sourceAdvancedOpen.value = false
  networkAdvancedOpen.value = false
  runtimeAdvancedOpen.value = false
  mobileReviewOpen.value = false
  providerPickerOpen.value = false
  providerQuery.value = ''
  validationInput.value = ''
  validatorTouched.value = false
  Object.assign(globalState, makeGlobalState())
  showToast(c.value.resetDone)
}

async function copyConfiguration() {
  try {
    if (navigator.clipboard) {
      await navigator.clipboard.writeText(generatedJson.value)
    } else {
      const input = document.createElement('textarea')
      input.value = generatedJson.value
      input.style.position = 'fixed'
      input.style.opacity = '0'
      document.body.appendChild(input)
      input.select()
      const copied = document.execCommand('copy')
      input.remove()
      if (!copied) throw new Error('Copy command failed')
    }
    showToast(c.value.copied)
  } catch {
    showToast(c.value.copyFailed, 'error')
  }
}

function downloadConfiguration() {
  if (!canExport.value || typeof document === 'undefined') return
  const blob = new Blob([`${generatedJson.value}\n`], { type: 'application/json;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = 'config.json'
  anchor.click()
  URL.revokeObjectURL(url)
  showToast(c.value.downloaded)
}

function triggerImport() {
  fileInput.value?.click()
}

async function importFile(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  try {
    validationInput.value = await file.text()
    validatorTouched.value = true
    inspectorTab.value = 'validate'
    showToast(c.value.imported)
  } catch {
    showToast(c.value.importFailed, 'error')
  } finally {
    input.value = ''
  }
}

function inputToText(value: unknown): string {
  if (Array.isArray(value)) return value.map((item) => String(item)).join('\n')
  if (value === undefined || value === null) return ''
  return String(value)
}

function cacheFromValue(value: unknown, fallback: CacheMode): { mode: CacheMode; path: string } {
  if (value === true) return { mode: 'true', path: '' }
  if (value === false) return { mode: 'false', path: '' }
  if (typeof value === 'string') return { mode: 'path', path: value }
  return { mode: fallback, path: '' }
}

function sslFromValue(value: unknown, fallback: SslMode): { mode: SslMode; path: string } {
  if (value === 'auto') return { mode: 'auto', path: '' }
  if (value === true) return { mode: 'true', path: '' }
  if (value === false) return { mode: 'false', path: '' }
  if (typeof value === 'string') return { mode: 'custom', path: value }
  return { mode: fallback, path: '' }
}

function collectExtra(value: Record<string, unknown>, known: Set<string>): JsonObject {
  const extra: JsonObject = isPlainObject(value.extra) ? { ...(value.extra as JsonObject) } : {}
  Object.keys(value).forEach((key) => {
    if (known.has(key)) return
    const nested = value[key]
    if (key.startsWith('extra_')) {
      extra[key.slice(6)] = nested as JsonValue
    } else if (isPlainObject(nested)) {
      Object.keys(nested).forEach((nestedKey) => {
        extra[`${key}_${nestedKey}`] = nested[nestedKey] as JsonValue
      })
    } else {
      extra[key] = nested as JsonValue
    }
  })
  return extra
}

function logLevelFromObject(value: Record<string, unknown>): LogLevel {
  const log = isPlainObject(value.log) ? value.log : {}
  const resolved = 'level' in log ? log.level : value.log_level
  return typeof resolved === 'string' || typeof resolved === 'number' ? resolved : ''
}

function logFieldState(
  value: Record<string, unknown>,
  key: 'level' | 'file' | 'format' | 'datefmt',
): { value: string; present: boolean; isNull: boolean } {
  const log = isPlainObject(value.log) ? value.log : {}
  const flat = value[`log_${key}`]
  const present = key in log || `log_${key}` in value
  const resolved = key in log ? log[key] : flat
  return {
    value: typeof resolved === 'string' ? resolved : '',
    present,
    isNull: resolved === null,
  }
}

function providerStateFromObject(value: Record<string, unknown>): ProviderState {
  const providerName =
    typeof value.provider === 'string'
      ? value.provider
      : typeof value.dns === 'string'
        ? value.dns
        : ''
  const cache = cacheFromValue(value.cache, 'inherit')
  const ssl = sslFromValue(value.ssl, 'inherit')
  const extra = collectExtra(value, PROVIDER_KNOWN_KEYS)
  return {
    uid: nextProviderUid++,
    provider: providerName,
    id: typeof value.id === 'string' ? value.id : '',
    idPresent: 'id' in value,
    idNull: value.id === null,
    token: typeof value.token === 'string' ? value.token : '',
    tokenPresent: 'token' in value,
    endpoint: typeof value.endpoint === 'string' ? value.endpoint : '',
    endpointPresent: 'endpoint' in value,
    endpointNull: value.endpoint === null,
    ipv4Text: inputToText(value.ipv4),
    ipv4Present: 'ipv4' in value,
    ipv6Text: inputToText(value.ipv6),
    ipv6Present: 'ipv6' in value,
    index4Text: inputToText(value.index4),
    index6Text: inputToText(value.index6),
    ttl: typeof value.ttl === 'number' ? String(value.ttl) : '',
    ttlNull: value.ttl === null,
    line: typeof value.line === 'string' ? value.line : '',
    linePresent: 'line' in value,
    lineNull: value.line === null,
    proxyText: inputToText(value.proxy),
    proxyPresent: 'proxy' in value,
    sslMode: ssl.mode,
    sslPath: ssl.path,
    cacheMode: cache.mode,
    cachePath: cache.path,
    cacheMaxAge: typeof value.cache_max_age === 'number' ? String(value.cache_max_age) : '',
    logLevel: logLevelFromObject(value),
    extraText: Object.keys(extra).length ? JSON.stringify(extra, null, 2) : '',
    revealToken: false,
  }
}

function applyToBuilder() {
  const parsedValue = parsedValidation.value.value
  if (!validationCanApply.value || !isPlainObject(parsedValue)) return
  const value = parsedValue
  const importedProviders: ProviderState[] = []
  let importedGlobalExtra: JsonObject = {}

  if (Array.isArray(value.providers)) {
    importedGlobalExtra = collectExtra(value, ROOT_KNOWN_KEYS)
    const inherited: Record<string, unknown> = {}
    ;['ipv4', 'ipv6', 'index4', 'index6', 'ttl', 'line'].forEach((key) => {
      if (key in value) inherited[key] = value[key]
    })
    value.providers.forEach((provider) => {
      if (isPlainObject(provider)) {
        importedProviders.push(
          providerStateFromObject({
            ...inherited,
            ...provider,
          }),
        )
      }
    })
  } else {
    const providerObject: Record<string, unknown> = {}
    ;['dns', 'id', 'token', 'endpoint', 'ipv4', 'ipv6', 'index4', 'index6', 'ttl', 'line'].forEach((key) => {
      if (key in value) providerObject[key] = value[key]
    })
    providerObject.extra = collectExtra(value, ROOT_KNOWN_KEYS)
    importedProviders.push(providerStateFromObject(providerObject))
  }

  if (!importedProviders.length) return
  providers.value = importedProviders
  selectedUid.value = providers.value[0].uid
  includeCredentials.value = false

  const cache = cacheFromValue(value.cache, 'inherit')
  const ssl = sslFromValue(value.ssl, 'inherit')
  const logFile = logFieldState(value, 'file')
  const logFormat = logFieldState(value, 'format')
  const logDatefmt = logFieldState(value, 'datefmt')
  Object.assign(globalState, {
    proxyText: inputToText(value.proxy),
    proxyPresent: 'proxy' in value,
    sslMode: ssl.mode,
    sslPath: ssl.path,
    cacheMode: cache.mode,
    cachePath: cache.path,
    cacheMaxAge: typeof value.cache_max_age === 'number' ? String(value.cache_max_age) : '',
    logLevel: logLevelFromObject(value),
    logFile: logFile.value,
    logFilePresent: logFile.present,
    logFileNull: logFile.isNull,
    logFormat: logFormat.value,
    logFormatPresent: logFormat.present,
    logFormatNull: logFormat.isNull,
    logDatefmt: logDatefmt.value,
    logDatefmtPresent: logDatefmt.present,
    logDatefmtNull: logDatefmt.isNull,
    extraText: Object.keys(importedGlobalExtra).length
      ? JSON.stringify(importedGlobalExtra, null, 2)
      : '',
  })
  activeSection.value = 'provider'
  inspectorTab.value = 'preview'
  providerAdvancedOpen.value = hasEndpointSettings.value
  sourceAdvancedOpen.value = hasSourceSettings.value
  networkAdvancedOpen.value = hasNetworkAdvancedSettings.value
  runtimeAdvancedOpen.value = hasRuntimeAdvancedSettings.value
  nextTick(() => showToast(c.value.applied))
}
</script>

<template>
  <div class="config-studio">
    <header class="studio-intro">
      <div class="studio-intro-copy">
        <h1>{{ c.title }}</h1>
      </div>
      <div class="studio-actions">
        <input
          ref="fileInput"
          hidden
          type="file"
          accept=".json,.jsonc,application/json,text/plain"
          @change="importFile"
        />
        <button class="studio-button studio-button-secondary" type="button" @click="triggerImport">
          <svg aria-hidden="true" viewBox="0 0 24 24">
            <path d="M12 3v11m0 0 4-4m-4 4-4-4M5 14v5h14v-5" />
          </svg>
          {{ c.import }}
        </button>
        <button class="studio-button studio-button-quiet" type="button" @click="resetBuilder">
          <svg aria-hidden="true" viewBox="0 0 24 24">
            <path d="M4 7h16M9 7V4h6v3m3 0-1 13H7L6 7m4 4v5m4-5v5" />
          </svg>
          {{ c.reset }}
        </button>
      </div>
    </header>

    <div class="studio-assurance" aria-live="polite">
      <span
        :key="`schema-${assuranceStateKey}`"
        class="studio-status"
        :class="{ 'is-error': previewErrors.length }"
      >
        <span class="studio-status-dot" aria-hidden="true"></span>
        <span class="studio-status-copy">
          <small>{{ c.schemaState }}</small>
          <strong>{{ schemaStatusLabel }}</strong>
        </span>
      </span>
      <span
        :key="`deployment-${assuranceStateKey}`"
        class="studio-status"
        :class="{
          'is-error': previewErrors.length,
          'is-warning': !previewErrors.length && (previewWarnings.length || hasTestOnlyProviders),
        }"
      >
        <span class="studio-status-dot" aria-hidden="true"></span>
        <span class="studio-status-copy">
          <small>{{ c.deploymentState }}</small>
          <strong>{{ deploymentStatusLabel }}</strong>
        </span>
      </span>
      <span class="studio-assurance-stat">
        <strong>{{ providers.length }}</strong> {{ providerCountUnit(providers.length) }}
      </span>
      <span class="studio-assurance-stat">
        <strong>{{ recordCount }}</strong> {{ recordCountUnit(recordCount) }}
      </span>
      <span class="studio-local-note">
        <svg aria-hidden="true" viewBox="0 0 24 24">
          <path d="M12 3 5 6v5c0 4.7 2.8 8.1 7 10 4.2-1.9 7-5.3 7-10V6l-7-3Z" />
          <path d="m9.5 12 1.7 1.7 3.7-4" />
        </svg>
        {{ c.localOnly }}
      </span>
    </div>

    <div class="studio-shell">
      <aside class="provider-rail" :aria-label="c.providers">
        <div class="rail-heading">
          <h2>{{ c.providers }}</h2>
          <button class="icon-button" type="button" :aria-label="c.addProvider" :title="c.addProvider" @click="addProvider">
            <svg aria-hidden="true" viewBox="0 0 24 24"><path d="M12 5v14M5 12h14" /></svg>
          </button>
        </div>

        <div class="provider-list">
          <div
            v-for="(provider, index) in providers"
            :key="provider.uid"
            class="provider-list-row"
            :class="[providerIssueClass(provider.uid), { 'is-selected': provider.uid === selectedUid }]"
          >
            <button
              class="provider-select-button"
              type="button"
              :data-provider-uid="provider.uid"
              :aria-pressed="provider.uid === selectedUid"
              @click="selectedUid = provider.uid"
            >
              <span class="provider-monogram" aria-hidden="true">
                {{ (providerMap.get(provider.provider)?.name || provider.provider).slice(0, 2) }}
              </span>
              <span>
                <strong>{{ providerMap.get(provider.provider)?.name || provider.provider }}</strong>
                <small>
                  {{ providerRecordCount(provider) }} {{ recordCountUnit(providerRecordCount(provider)) }}
                  <template v-if="providerIssueLabel(provider.uid)"> · {{ providerIssueLabel(provider.uid) }}</template>
                </small>
              </span>
            </button>
            <button
              class="provider-remove-button"
              type="button"
              :disabled="providers.length === 1"
              :aria-label="`${c.removeProvider} ${index + 1}`"
              :title="c.removeProvider"
              @click="removeProvider(provider.uid)"
            >
              <svg aria-hidden="true" viewBox="0 0 24 24"><path d="M6 12h12" /></svg>
            </button>
          </div>
        </div>

        <button class="rail-add-button" type="button" @click="addProvider">
          <svg aria-hidden="true" viewBox="0 0 24 24"><path d="M12 5v14M5 12h14" /></svg>
          {{ c.addProvider }}
        </button>

        <div class="section-nav-wrap">
          <nav class="section-nav" :aria-label="c.configurationSections">
            <button
              v-for="section in sections"
              :key="section.key"
              type="button"
              :aria-current="activeSection === section.key ? 'step' : undefined"
              :class="{ 'is-active': activeSection === section.key }"
              @click="activeSection = section.key"
            >
              <span class="section-marker" aria-hidden="true"></span>
              <span class="section-label">{{ section.label }}</span>
              <small
                v-if="sectionIssueTotal(section.key)"
                class="section-issue"
                :class="sectionIssueTone(section.key)"
              >
                {{ sectionIssueTotal(section.key) }}
              </small>
            </button>
            <button
              ref="mobileReviewButton"
              class="mobile-review-launcher"
              :class="{
                'is-error': previewErrors.length,
                'is-warning': !previewErrors.length && previewWarnings.length,
              }"
              type="button"
              @click="openMobileReview"
            >
              <span class="mobile-review-status" aria-hidden="true"></span>
              <span>
                <strong>{{ c.reviewConfig }}</strong>
                <small>{{ exportStatusLabel }}</small>
              </span>
              <b v-if="previewErrors.length">{{ previewErrors.length }}</b>
              <b v-else-if="previewWarnings.length">{{ previewWarnings.length }}</b>
              <b v-else aria-hidden="true">✓</b>
            </button>
          </nav>
        </div>
      </aside>

      <main class="configuration-editor">
        <div class="editor-heading">
          <div>
            <span class="editor-provider-name">{{ selectedMeta.name }}</span>
            <p>{{ isEnglish ? selectedMeta.descriptionEn : selectedMeta.descriptionZh }}</p>
          </div>
          <div class="editor-heading-actions">
            <a class="text-action" :href="providerDocsLink" target="_blank" rel="noopener noreferrer">
              {{ c.providerHelp }}
              <svg aria-hidden="true" viewBox="0 0 24 24"><path d="m9 18 6-6-6-6" /></svg>
            </a>
            <button class="icon-button" type="button" :aria-label="c.duplicateProvider" :title="c.duplicateProvider" @click="duplicateProvider">
              <svg aria-hidden="true" viewBox="0 0 24 24">
                <rect x="8" y="8" width="11" height="11" rx="2" />
                <path d="M16 8V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h2" />
              </svg>
            </button>
          </div>
        </div>

        <section v-show="activeSection === 'provider'" class="editor-section">
          <div class="section-heading">
            <h2>{{ c.providerSettings }}</h2>
          </div>

          <div class="field field-wide provider-picker-field">
            <span>{{ c.provider }}</span>
            <div class="provider-picker">
              <button
                ref="providerPickerTrigger"
                class="provider-picker-trigger"
                type="button"
                :id="providerFieldId('provider')"
                :aria-label="`${c.chooseProvider}: ${selectedMeta.name}`"
                :aria-expanded="providerPickerOpen"
                :aria-controls="providerPickerPanelId"
                :aria-invalid="fieldInvalid(providerFieldPath('provider'))"
                :aria-describedby="fieldDescription(providerFieldPath('provider'))"
                @click="toggleProviderPicker"
              >
                <span class="provider-picker-monogram" aria-hidden="true">{{ selectedMeta.name.slice(0, 2) }}</span>
                <span class="provider-picker-summary">
                  <span>
                    <strong>{{ selectedMeta.name }}</strong>
                    <code>{{ selectedMeta.value }}</code>
                  </span>
                  <small>{{ isEnglish ? selectedMeta.descriptionEn : selectedMeta.descriptionZh }}</small>
                </span>
                <span class="provider-picker-tags">
                  <small>{{ providerAuthLabel(selectedMeta) }}</small>
                  <small v-if="selectedMeta.testOnly" class="is-test">{{ c.testOnly }}</small>
                </span>
                <svg class="provider-picker-chevron" aria-hidden="true" viewBox="0 0 24 24">
                  <path d="m7 9 5 5 5-5" />
                </svg>
              </button>

              <div
                v-if="providerPickerOpen"
                :id="providerPickerPanelId"
                class="provider-picker-panel"
                role="region"
                :aria-label="c.chooseProvider"
                @keydown="handleProviderPickerKeydown"
              >
                <label class="provider-picker-search">
                  <span class="visually-hidden">{{ c.providerSearch }}</span>
                  <svg aria-hidden="true" viewBox="0 0 24 24">
                    <circle cx="11" cy="11" r="6" />
                    <path d="m16 16 4 4" />
                  </svg>
                  <input
                    ref="providerSearchInput"
                    v-model="providerQuery"
                    type="search"
                    autocomplete="off"
                    :placeholder="c.providerSearchPlaceholder"
                  />
                </label>

                <div v-if="hasProviderSearchResults" class="provider-picker-groups">
                  <section v-for="group in filteredProviderGroups" :key="group.key">
                    <h3>{{ group.label }}</h3>
                    <ul>
                      <li v-for="provider in group.providers" :key="provider.value">
                        <button
                          class="provider-picker-option"
                          :class="{ 'is-selected': provider.value === selectedProvider.provider }"
                          type="button"
                          :aria-pressed="provider.value === selectedProvider.provider"
                          @click="chooseProvider(provider.value)"
                        >
                          <span class="provider-picker-monogram" aria-hidden="true">{{ provider.name.slice(0, 2) }}</span>
                          <span class="provider-picker-option-copy">
                            <span>
                              <strong>{{ provider.name }}</strong>
                              <code>{{ provider.value }}</code>
                            </span>
                            <small>{{ isEnglish ? provider.descriptionEn : provider.descriptionZh }}</small>
                            <span class="provider-picker-option-tags">
                              <small>{{ providerAuthLabel(provider) }}</small>
                              <small v-if="provider.testOnly" class="is-test">{{ c.testOnly }}</small>
                            </span>
                          </span>
                          <svg
                            v-if="provider.value === selectedProvider.provider"
                            class="provider-picker-check"
                            aria-hidden="true"
                            viewBox="0 0 24 24"
                          >
                            <path d="m5 12 4 4L19 6" />
                          </svg>
                        </button>
                      </li>
                    </ul>
                  </section>
                </div>
                <p v-else class="provider-picker-empty">{{ c.noProviderResults }}</p>
              </div>
            </div>
            <small
              v-if="fieldDiagnostic(providerFieldPath('provider'))"
              :id="fieldFeedbackId(providerFieldPath('provider'))"
              class="field-feedback"
              :class="`is-${fieldDiagnostic(providerFieldPath('provider'))?.severity}`"
            >
              {{ fieldDiagnostic(providerFieldPath('provider'))?.message }}
              <span v-if="fieldDiagnostic(providerFieldPath('provider'))?.recovery">
                {{ fieldDiagnostic(providerFieldPath('provider'))?.recovery }}
              </span>
            </small>
          </div>

          <div class="subsection-heading">
            <h3>{{ c.credentialTitle }}</h3>
            <p v-if="selectedMeta.auth !== 'none'">{{ c.credentialHint }}</p>
            <p v-else>{{ c.noCredential }}</p>
          </div>

          <div v-if="selectedMeta.auth !== 'none'" class="field-grid">
            <label v-if="selectedMeta.auth !== 'token'" class="field">
              <span>
                {{ isEnglish ? selectedMeta.idLabelEn : selectedMeta.idLabelZh }}
                <em v-if="selectedMeta.auth === 'flexible' || selectedMeta.auth === 'callback'">{{ c.optional }}</em>
              </span>
              <input
                :id="providerFieldId('id')"
                v-model="selectedProvider.id"
                type="text"
                autocomplete="off"
                spellcheck="false"
                :placeholder="selectedMeta.auth === 'callback' ? 'https://api.example.com/update?domain=__DOMAIN__' : ''"
                :aria-invalid="fieldInvalid(providerFieldPath('id'))"
                :aria-describedby="fieldDescription(providerFieldPath('id'))"
                @input="
                  selectedProvider.idPresent = true;
                  selectedProvider.idNull = false
                "
              />
              <small
                v-if="fieldDiagnostic(providerFieldPath('id'))"
                :id="fieldFeedbackId(providerFieldPath('id'))"
                class="field-feedback"
                :class="`is-${fieldDiagnostic(providerFieldPath('id'))?.severity}`"
              >
                {{ fieldDiagnostic(providerFieldPath('id'))?.message }}
                <span v-if="fieldDiagnostic(providerFieldPath('id'))?.recovery">
                  {{ fieldDiagnostic(providerFieldPath('id'))?.recovery }}
                </span>
              </small>
            </label>

            <label class="field" :class="{ 'field-wide': selectedMeta.auth === 'token' }">
              <span>
                {{ isEnglish ? selectedMeta.tokenLabelEn : selectedMeta.tokenLabelZh }}
                <em v-if="selectedMeta.auth === 'callback'">{{ c.optional }}</em>
              </span>
              <span class="secret-input">
                <input
                  :id="providerFieldId('token')"
                  v-model="selectedProvider.token"
                  :type="selectedProvider.revealToken ? 'text' : 'password'"
                  autocomplete="new-password"
                  spellcheck="false"
                  :aria-invalid="fieldInvalid(providerFieldPath('token'))"
                  :aria-describedby="fieldDescription(providerFieldPath('token'))"
                  @input="selectedProvider.tokenPresent = true"
                />
                <button
                  type="button"
                  :aria-label="selectedProvider.revealToken ? c.conceal : c.reveal"
                  :title="selectedProvider.revealToken ? c.conceal : c.reveal"
                  @click="selectedProvider.revealToken = !selectedProvider.revealToken"
                >
                  <svg v-if="selectedProvider.revealToken" aria-hidden="true" viewBox="0 0 24 24">
                    <path d="M3 3l18 18M10.6 10.7a2 2 0 0 0 2.7 2.7M9.9 4.2A10.7 10.7 0 0 1 12 4c5.5 0 9 8 9 8a15.7 15.7 0 0 1-2.1 3.2M6.6 6.6C4.2 8.2 3 12 3 12s3.5 8 9 8c1.2 0 2.3-.4 3.3-1" />
                  </svg>
                  <svg v-else aria-hidden="true" viewBox="0 0 24 24">
                    <path d="M3 12s3.5-8 9-8 9 8 9 8-3.5 8-9 8-9-8-9-8Z" />
                    <circle cx="12" cy="12" r="2.5" />
                  </svg>
                </button>
              </span>
              <small
                v-if="fieldDiagnostic(providerFieldPath('token'))"
                :id="fieldFeedbackId(providerFieldPath('token'))"
                class="field-feedback"
                :class="`is-${fieldDiagnostic(providerFieldPath('token'))?.severity}`"
              >
                {{ fieldDiagnostic(providerFieldPath('token'))?.message }}
                <span v-if="fieldDiagnostic(providerFieldPath('token'))?.recovery">
                  {{ fieldDiagnostic(providerFieldPath('token'))?.recovery }}
                </span>
              </small>
            </label>
          </div>

          <button
            class="advanced-toggle"
            type="button"
            :aria-expanded="providerAdvancedOpen"
            :aria-controls="`studio-provider-advanced-${selectedProvider.uid}`"
            @click="providerAdvancedOpen = !providerAdvancedOpen"
          >
            <span>
              <strong>{{ c.endpointSettings }}</strong>
              <small>{{ c.advanced }}</small>
            </span>
            <span v-if="hasEndpointSettings" class="advanced-state">{{ c.configured }}</span>
            <svg aria-hidden="true" viewBox="0 0 24 24"><path d="m8 10 4 4 4-4" /></svg>
          </button>
          <div
            v-show="providerAdvancedOpen"
            :id="`studio-provider-advanced-${selectedProvider.uid}`"
            class="advanced-content"
          >
            <label class="field field-wide">
              <span>{{ c.endpoint }} <em>{{ c.optional }}</em></span>
              <input
                :id="providerFieldId('endpoint')"
                v-model="selectedProvider.endpoint"
                type="url"
                autocomplete="off"
                spellcheck="false"
                :placeholder="c.endpointPlaceholder"
                :aria-invalid="fieldInvalid(providerFieldPath('endpoint'))"
                :aria-describedby="fieldDescription(providerFieldPath('endpoint'))"
                @input="
                  selectedProvider.endpointPresent = true;
                  selectedProvider.endpointNull = false
                "
              />
              <small
                v-if="fieldDiagnostic(providerFieldPath('endpoint'))"
                :id="fieldFeedbackId(providerFieldPath('endpoint'))"
                class="field-feedback"
                :class="`is-${fieldDiagnostic(providerFieldPath('endpoint'))?.severity}`"
              >
                {{ fieldDiagnostic(providerFieldPath('endpoint'))?.message }}
                <span v-if="fieldDiagnostic(providerFieldPath('endpoint'))?.recovery">
                  {{ fieldDiagnostic(providerFieldPath('endpoint'))?.recovery }}
                </span>
              </small>
            </label>
          </div>
        </section>

        <section v-show="activeSection === 'records'" class="editor-section">
          <div class="section-heading">
            <h2>{{ c.recordsTitle }}</h2>
            <p>{{ c.recordsHint }}</p>
          </div>

          <div class="record-lane">
            <div class="record-lane-marker">A</div>
            <div class="record-lane-content">
              <label class="field field-wide">
                <span>{{ c.ipv4Domains }}</span>
                <textarea
                  :id="providerFieldId('ipv4')"
                  v-model="selectedProvider.ipv4Text"
                  rows="3"
                  spellcheck="false"
                  placeholder="home.example.com, nas.example.com"
                  :aria-invalid="fieldInvalid(providerFieldPath('ipv4'))"
                  :aria-describedby="fieldDescription(providerFieldPath('ipv4'))"
                  @input="selectedProvider.ipv4Present = true"
                ></textarea>
                <small
                  v-if="fieldDiagnostic(providerFieldPath('ipv4'))"
                  :id="fieldFeedbackId(providerFieldPath('ipv4'))"
                  class="field-feedback"
                  :class="`is-${fieldDiagnostic(providerFieldPath('ipv4'))?.severity}`"
                >
                  {{ fieldDiagnostic(providerFieldPath('ipv4'))?.message }}
                  <span v-if="fieldDiagnostic(providerFieldPath('ipv4'))?.recovery">
                    {{ fieldDiagnostic(providerFieldPath('ipv4'))?.recovery }}
                  </span>
                </small>
              </label>
              <div v-if="selectedIpv4.length" class="value-chips" :aria-label="c.ipv4DomainList">
                <span v-for="domain in selectedIpv4" :key="domain">{{ domain }}</span>
              </div>
            </div>
          </div>

          <div class="record-lane">
            <div class="record-lane-marker">AAAA</div>
            <div class="record-lane-content">
              <label class="field field-wide">
                <span>{{ c.ipv6Domains }}</span>
                <textarea
                  :id="providerFieldId('ipv6')"
                  v-model="selectedProvider.ipv6Text"
                  rows="3"
                  spellcheck="false"
                  placeholder="ipv6.example.com"
                  :aria-invalid="fieldInvalid(providerFieldPath('ipv6'))"
                  :aria-describedby="fieldDescription(providerFieldPath('ipv6'))"
                  @input="selectedProvider.ipv6Present = true"
                ></textarea>
                <small
                  v-if="fieldDiagnostic(providerFieldPath('ipv6'))"
                  :id="fieldFeedbackId(providerFieldPath('ipv6'))"
                  class="field-feedback"
                  :class="`is-${fieldDiagnostic(providerFieldPath('ipv6'))?.severity}`"
                >
                  {{ fieldDiagnostic(providerFieldPath('ipv6'))?.message }}
                  <span v-if="fieldDiagnostic(providerFieldPath('ipv6'))?.recovery">
                    {{ fieldDiagnostic(providerFieldPath('ipv6'))?.recovery }}
                  </span>
                </small>
              </label>
              <div v-if="selectedIpv6.length" class="value-chips" :aria-label="c.ipv6DomainList">
                <span v-for="domain in selectedIpv6" :key="domain">{{ domain }}</span>
              </div>
            </div>
          </div>

          <button
            class="advanced-toggle"
            type="button"
            :aria-expanded="sourceAdvancedOpen"
            :aria-controls="`studio-source-advanced-${selectedProvider.uid}`"
            @click="sourceAdvancedOpen = !sourceAdvancedOpen"
          >
            <span>
              <strong>{{ c.sourceSettings }}</strong>
              <small>{{ c.advanced }}</small>
            </span>
            <span v-if="hasSourceSettings" class="advanced-state">{{ c.configured }}</span>
            <svg aria-hidden="true" viewBox="0 0 24 24"><path d="m8 10 4 4 4-4" /></svg>
          </button>

          <div
            v-show="sourceAdvancedOpen"
            :id="`studio-source-advanced-${selectedProvider.uid}`"
            class="advanced-content"
          >
            <div class="field-grid">
              <label class="field">
                <span>IPv4 · {{ c.addressSources }}</span>
                <textarea
                  :id="providerFieldId('index4')"
                  v-model="selectedProvider.index4Text"
                  rows="3"
                  spellcheck="false"
                  placeholder="public&#10;default"
                  :aria-invalid="fieldInvalid(providerFieldPath('index4'))"
                  :aria-describedby="fieldDescription(providerFieldPath('index4'))"
                ></textarea>
                <small>{{ c.sourceHint }}</small>
                <small
                  v-if="fieldDiagnostic(providerFieldPath('index4'))"
                  :id="fieldFeedbackId(providerFieldPath('index4'))"
                  class="field-feedback"
                  :class="`is-${fieldDiagnostic(providerFieldPath('index4'))?.severity}`"
                >
                  {{ fieldDiagnostic(providerFieldPath('index4'))?.message }}
                  <span v-if="fieldDiagnostic(providerFieldPath('index4'))?.recovery">
                    {{ fieldDiagnostic(providerFieldPath('index4'))?.recovery }}
                  </span>
                </small>
              </label>
              <label class="field">
                <span>IPv6 · {{ c.addressSources }}</span>
                <textarea
                  :id="providerFieldId('index6')"
                  v-model="selectedProvider.index6Text"
                  rows="3"
                  spellcheck="false"
                  placeholder="public&#10;default"
                  :aria-invalid="fieldInvalid(providerFieldPath('index6'))"
                  :aria-describedby="fieldDescription(providerFieldPath('index6'))"
                ></textarea>
                <small>{{ c.sourceHint }}</small>
                <small
                  v-if="fieldDiagnostic(providerFieldPath('index6'))"
                  :id="fieldFeedbackId(providerFieldPath('index6'))"
                  class="field-feedback"
                  :class="`is-${fieldDiagnostic(providerFieldPath('index6'))?.severity}`"
                >
                  {{ fieldDiagnostic(providerFieldPath('index6'))?.message }}
                  <span v-if="fieldDiagnostic(providerFieldPath('index6'))?.recovery">
                    {{ fieldDiagnostic(providerFieldPath('index6'))?.recovery }}
                  </span>
                </small>
              </label>
              <label class="field">
                <span>{{ c.ttl }}</span>
                <input
                  :id="providerFieldId('ttl')"
                  v-model="selectedProvider.ttl"
                  type="text"
                  inputmode="decimal"
                  :placeholder="c.inheritProvider"
                  :aria-invalid="fieldInvalid(providerFieldPath('ttl'))"
                  :aria-describedby="fieldDescription(providerFieldPath('ttl'))"
                  @input="selectedProvider.ttlNull = false"
                />
                <small
                  v-if="fieldDiagnostic(providerFieldPath('ttl'))"
                  :id="fieldFeedbackId(providerFieldPath('ttl'))"
                  class="field-feedback"
                  :class="`is-${fieldDiagnostic(providerFieldPath('ttl'))?.severity}`"
                >
                  {{ fieldDiagnostic(providerFieldPath('ttl'))?.message }}
                </small>
              </label>
              <label class="field">
                <span>{{ c.line }}</span>
                <input
                  :id="providerFieldId('line')"
                  v-model="selectedProvider.line"
                  type="text"
                  autocomplete="off"
                  :placeholder="c.inheritProvider"
                  :aria-invalid="fieldInvalid(providerFieldPath('line'))"
                  :aria-describedby="fieldDescription(providerFieldPath('line'))"
                  @input="
                    selectedProvider.linePresent = true;
                    selectedProvider.lineNull = false
                  "
                />
                <small
                  v-if="fieldDiagnostic(providerFieldPath('line'))"
                  :id="fieldFeedbackId(providerFieldPath('line'))"
                  class="field-feedback"
                  :class="`is-${fieldDiagnostic(providerFieldPath('line'))?.severity}`"
                >
                  {{ fieldDiagnostic(providerFieldPath('line'))?.message }}
                </small>
              </label>
            </div>
          </div>
        </section>

        <section v-show="activeSection === 'network'" class="editor-section">
          <div class="section-heading">
            <h2>{{ c.networkTitle }}</h2>
            <p>{{ c.proxyHint }}</p>
          </div>

          <div class="field-grid">
            <label class="field">
              <span>{{ c.providerProxy }}</span>
              <textarea
                :id="providerFieldId('proxy')"
                v-model="selectedProvider.proxyText"
                rows="4"
                spellcheck="false"
                placeholder="http://127.0.0.1:1080&#10;DIRECT"
                :aria-invalid="fieldInvalid(providerFieldPath('proxy'))"
                :aria-describedby="fieldDescription(providerFieldPath('proxy'))"
                @input="selectedProvider.proxyPresent = true"
              ></textarea>
              <small
                v-if="fieldDiagnostic(providerFieldPath('proxy'))"
                :id="fieldFeedbackId(providerFieldPath('proxy'))"
                class="field-feedback"
                :class="`is-${fieldDiagnostic(providerFieldPath('proxy'))?.severity}`"
              >
                {{ fieldDiagnostic(providerFieldPath('proxy'))?.message }}
                <span v-if="fieldDiagnostic(providerFieldPath('proxy'))?.recovery">
                  {{ fieldDiagnostic(providerFieldPath('proxy'))?.recovery }}
                </span>
              </small>
            </label>
            <label class="field">
              <span>{{ c.globalProxy }}</span>
              <textarea
                :id="globalFieldId('proxy')"
                v-model="globalState.proxyText"
                rows="4"
                spellcheck="false"
                placeholder="SYSTEM&#10;DIRECT"
                :aria-invalid="fieldInvalid(globalFieldPath('proxy'))"
                :aria-describedby="fieldDescription(globalFieldPath('proxy'))"
                @input="globalState.proxyPresent = true"
              ></textarea>
              <small
                v-if="fieldDiagnostic(globalFieldPath('proxy'))"
                :id="fieldFeedbackId(globalFieldPath('proxy'))"
                class="field-feedback"
                :class="`is-${fieldDiagnostic(globalFieldPath('proxy'))?.severity}`"
              >
                {{ fieldDiagnostic(globalFieldPath('proxy'))?.message }}
                <span v-if="fieldDiagnostic(globalFieldPath('proxy'))?.recovery">
                  {{ fieldDiagnostic(globalFieldPath('proxy'))?.recovery }}
                </span>
              </small>
            </label>
          </div>

          <button
            class="advanced-toggle"
            type="button"
            :aria-expanded="networkAdvancedOpen"
            :aria-controls="`studio-network-advanced-${selectedProvider.uid}`"
            @click="networkAdvancedOpen = !networkAdvancedOpen"
          >
            <span>
              <strong>{{ c.sslSettings }}</strong>
              <small>{{ c.advanced }}</small>
            </span>
            <span v-if="hasNetworkAdvancedSettings" class="advanced-state">{{ c.configured }}</span>
            <svg aria-hidden="true" viewBox="0 0 24 24"><path d="m8 10 4 4 4-4" /></svg>
          </button>
          <div
            v-show="networkAdvancedOpen"
            :id="`studio-network-advanced-${selectedProvider.uid}`"
            class="advanced-content"
          >
            <div class="settings-band">
              <div>
                <h3>{{ c.ssl }}</h3>
                <p>{{ c.providerOverridesHint }}</p>
              </div>
              <div class="field-grid">
                <label class="field">
                  <span>{{ isEnglish ? 'Global' : '全局' }} · {{ c.ssl }}</span>
                  <select
                    :id="globalFieldId('ssl')"
                    v-model="globalState.sslMode"
                    :aria-invalid="fieldInvalid(globalFieldPath('ssl'))"
                    :aria-describedby="fieldDescription(globalFieldPath('ssl'))"
                  >
                    <option value="inherit">{{ c.inheritEnvironment }}</option>
                    <option value="auto">{{ c.sslAuto }}</option>
                    <option value="true">{{ c.sslStrict }}</option>
                    <option value="false">{{ c.sslOff }}</option>
                    <option value="custom">{{ c.sslCustom }}</option>
                  </select>
                  <small
                    v-if="fieldDiagnostic(globalFieldPath('ssl'))"
                    :id="fieldFeedbackId(globalFieldPath('ssl'))"
                    class="field-feedback"
                    :class="`is-${fieldDiagnostic(globalFieldPath('ssl'))?.severity}`"
                  >
                    {{ fieldDiagnostic(globalFieldPath('ssl'))?.message }}
                  </small>
                </label>
                <label class="field">
                  <span>{{ selectedMeta.name }} · {{ c.ssl }}</span>
                  <select
                    :id="providerFieldId('ssl')"
                    v-model="selectedProvider.sslMode"
                    :aria-invalid="fieldInvalid(providerFieldPath('ssl'))"
                    :aria-describedby="fieldDescription(providerFieldPath('ssl'))"
                  >
                    <option value="inherit">{{ c.inheritGlobal }}</option>
                    <option value="auto">{{ c.sslAuto }}</option>
                    <option value="true">{{ c.sslStrict }}</option>
                    <option value="false">{{ c.sslOff }}</option>
                    <option value="custom">{{ c.sslCustom }}</option>
                  </select>
                  <small
                    v-if="fieldDiagnostic(providerFieldPath('ssl'))"
                    :id="fieldFeedbackId(providerFieldPath('ssl'))"
                    class="field-feedback"
                    :class="`is-${fieldDiagnostic(providerFieldPath('ssl'))?.severity}`"
                  >
                    {{ fieldDiagnostic(providerFieldPath('ssl'))?.message }}
                  </small>
                </label>
                <label v-if="globalState.sslMode === 'custom'" class="field">
                  <span>{{ c.caPath }}</span>
                  <input v-model="globalState.sslPath" type="text" spellcheck="false" placeholder="/etc/ssl/private-ca.crt" />
                </label>
                <label v-if="selectedProvider.sslMode === 'custom'" class="field">
                  <span>{{ selectedMeta.name }} · {{ c.caPath }}</span>
                  <input v-model="selectedProvider.sslPath" type="text" spellcheck="false" placeholder="/etc/ssl/private-ca.crt" />
                </label>
              </div>
            </div>
          </div>
        </section>

        <section v-show="activeSection === 'runtime'" class="editor-section">
          <div class="section-heading">
            <h2>{{ c.runtimeTitle }}</h2>
            <p>{{ c.runtimeHint }}</p>
          </div>

          <div class="field-grid">
            <label class="field">
              <span>{{ c.cache }}</span>
              <select
                :id="globalFieldId('cache')"
                v-model="globalState.cacheMode"
                :aria-invalid="fieldInvalid(globalFieldPath('cache'))"
                :aria-describedby="fieldDescription(globalFieldPath('cache'))"
              >
                <option value="inherit">{{ c.inheritEnvironment }}</option>
                <option value="true">{{ c.cacheOn }}</option>
                <option value="false">{{ c.cacheOff }}</option>
                <option value="path">{{ c.cachePath }}</option>
              </select>
              <small
                v-if="fieldDiagnostic(globalFieldPath('cache'))"
                :id="fieldFeedbackId(globalFieldPath('cache'))"
                class="field-feedback"
                :class="`is-${fieldDiagnostic(globalFieldPath('cache'))?.severity}`"
              >
                {{ fieldDiagnostic(globalFieldPath('cache'))?.message }}
              </small>
            </label>
            <label class="field">
              <span>{{ c.cacheAge }}</span>
              <input
                :id="globalFieldId('cache-age')"
                v-model="globalState.cacheMaxAge"
                type="text"
                inputmode="numeric"
                pattern="[0-9]*"
                :aria-invalid="fieldInvalid(globalFieldPath('cache_max_age'))"
                :aria-describedby="fieldDescription(globalFieldPath('cache_max_age'))"
              />
              <small
                v-if="fieldDiagnostic(globalFieldPath('cache_max_age'))"
                :id="fieldFeedbackId(globalFieldPath('cache_max_age'))"
                class="field-feedback"
                :class="`is-${fieldDiagnostic(globalFieldPath('cache_max_age'))?.severity}`"
              >
                {{ fieldDiagnostic(globalFieldPath('cache_max_age'))?.message }}
              </small>
            </label>
            <label v-if="globalState.cacheMode === 'path'" class="field field-wide">
              <span>{{ c.cacheFile }}</span>
              <input v-model="globalState.cachePath" type="text" spellcheck="false" placeholder="/var/cache/ddns.cache" />
            </label>
          </div>

          <div class="subsection-heading">
            <h3>{{ c.logging }}</h3>
          </div>
          <div class="field-grid">
            <label class="field">
              <span>{{ c.logLevel }}</span>
              <select
                :id="globalFieldId('log-level')"
                v-model="globalState.logLevel"
                :aria-invalid="fieldInvalid(globalFieldPath('log'))"
                :aria-describedby="fieldDescription(globalFieldPath('log'))"
              >
                <option
                  v-if="typeof globalState.logLevel === 'number'"
                  :value="globalState.logLevel"
                >
                  {{ globalState.logLevel }}
                </option>
                <option value="">{{ c.inheritEnvironment }}</option>
                <option v-for="level in LOG_LEVELS" :key="level" :value="level">{{ level }}</option>
              </select>
              <small
                v-if="fieldDiagnostic(globalFieldPath('log'))"
                :id="fieldFeedbackId(globalFieldPath('log'))"
                class="field-feedback"
                :class="`is-${fieldDiagnostic(globalFieldPath('log'))?.severity}`"
              >
                {{ fieldDiagnostic(globalFieldPath('log'))?.message }}
              </small>
            </label>
            <label class="field">
              <span>{{ c.logFile }} <em>{{ c.optional }}</em></span>
              <input
                v-model="globalState.logFile"
                type="text"
                spellcheck="false"
                placeholder="/var/log/ddns.log"
                @input="
                  globalState.logFilePresent = true;
                  globalState.logFileNull = false
                "
              />
            </label>
            <label class="field">
              <span>{{ c.logFormat }} <em>{{ c.optional }}</em></span>
              <input
                v-model="globalState.logFormat"
                type="text"
                spellcheck="false"
                placeholder="%(asctime)s %(levelname)s %(message)s"
                @input="
                  globalState.logFormatPresent = true;
                  globalState.logFormatNull = false
                "
              />
            </label>
            <label class="field">
              <span>{{ c.dateFormat }} <em>{{ c.optional }}</em></span>
              <input
                v-model="globalState.logDatefmt"
                type="text"
                spellcheck="false"
                placeholder="%Y-%m-%dT%H:%M:%S"
                @input="
                  globalState.logDatefmtPresent = true;
                  globalState.logDatefmtNull = false
                "
              />
            </label>
          </div>

          <button
            class="advanced-toggle"
            type="button"
            :aria-expanded="runtimeAdvancedOpen"
            :aria-controls="`studio-runtime-advanced-${selectedProvider.uid}`"
            @click="runtimeAdvancedOpen = !runtimeAdvancedOpen"
          >
            <span>
              <strong>{{ c.runtimeAdvanced }}</strong>
              <small>{{ c.advanced }}</small>
            </span>
            <span v-if="hasRuntimeAdvancedSettings" class="advanced-state">{{ c.configured }}</span>
            <svg aria-hidden="true" viewBox="0 0 24 24"><path d="m8 10 4 4 4-4" /></svg>
          </button>
          <div
            v-show="runtimeAdvancedOpen"
            :id="`studio-runtime-advanced-${selectedProvider.uid}`"
            class="advanced-content"
          >
            <div class="settings-band">
              <div>
                <h3>{{ c.providerOverrides }}</h3>
                <p>{{ c.providerOverridesHint }}</p>
              </div>
              <div class="field-grid">
                <label class="field">
                  <span>{{ c.cache }}</span>
                  <select
                    :id="providerFieldId('cache')"
                    v-model="selectedProvider.cacheMode"
                    :aria-invalid="fieldInvalid(providerFieldPath('cache'))"
                    :aria-describedby="fieldDescription(providerFieldPath('cache'))"
                  >
                    <option value="inherit">{{ c.inheritGlobal }}</option>
                    <option value="true">{{ c.cacheOn }}</option>
                    <option value="false">{{ c.cacheOff }}</option>
                    <option value="path">{{ c.cachePath }}</option>
                  </select>
                  <small
                    v-if="fieldDiagnostic(providerFieldPath('cache'))"
                    :id="fieldFeedbackId(providerFieldPath('cache'))"
                    class="field-feedback"
                    :class="`is-${fieldDiagnostic(providerFieldPath('cache'))?.severity}`"
                  >
                    {{ fieldDiagnostic(providerFieldPath('cache'))?.message }}
                  </small>
                </label>
                <label class="field">
                  <span>{{ c.cacheAge }} <em>{{ c.optional }}</em></span>
                  <input
                    :id="providerFieldId('cache-age')"
                    v-model="selectedProvider.cacheMaxAge"
                    type="text"
                    inputmode="numeric"
                    pattern="[0-9]*"
                    :placeholder="c.inheritGlobal"
                    :aria-invalid="fieldInvalid(providerFieldPath('cache_max_age'))"
                    :aria-describedby="fieldDescription(providerFieldPath('cache_max_age'))"
                  />
                  <small
                    v-if="fieldDiagnostic(providerFieldPath('cache_max_age'))"
                    :id="fieldFeedbackId(providerFieldPath('cache_max_age'))"
                    class="field-feedback"
                    :class="`is-${fieldDiagnostic(providerFieldPath('cache_max_age'))?.severity}`"
                  >
                    {{ fieldDiagnostic(providerFieldPath('cache_max_age'))?.message }}
                  </small>
                </label>
                <label v-if="selectedProvider.cacheMode === 'path'" class="field">
                  <span>{{ c.cacheFile }}</span>
                  <input v-model="selectedProvider.cachePath" type="text" spellcheck="false" placeholder="/var/cache/provider.cache" />
                </label>
                <label class="field">
                  <span>{{ c.logLevel }}</span>
                  <select
                    :id="providerFieldId('log-level')"
                    v-model="selectedProvider.logLevel"
                    :aria-invalid="fieldInvalid(providerFieldPath('log'))"
                    :aria-describedby="fieldDescription(providerFieldPath('log'))"
                  >
                    <option
                      v-if="typeof selectedProvider.logLevel === 'number'"
                      :value="selectedProvider.logLevel"
                    >
                      {{ selectedProvider.logLevel }}
                    </option>
                    <option value="">{{ c.inheritGlobal }}</option>
                    <option v-for="level in LOG_LEVELS" :key="level" :value="level">{{ level }}</option>
                  </select>
                  <small
                    v-if="fieldDiagnostic(providerFieldPath('log'))"
                    :id="fieldFeedbackId(providerFieldPath('log'))"
                    class="field-feedback"
                    :class="`is-${fieldDiagnostic(providerFieldPath('log'))?.severity}`"
                  >
                    {{ fieldDiagnostic(providerFieldPath('log'))?.message }}
                  </small>
                </label>
              </div>
            </div>

            <div class="field-grid extra-grid">
              <label class="field">
                <span>{{ c.extraGlobal }}</span>
                <textarea
                  :id="globalFieldId('extra')"
                  v-model="globalState.extraText"
                  rows="7"
                  spellcheck="false"
                  placeholder="{&#10;  &quot;region&quot;: &quot;global&quot;&#10;}"
                  :aria-invalid="fieldInvalid(globalFieldPath('extra'))"
                  :aria-describedby="fieldDescription(globalFieldPath('extra'))"
                ></textarea>
                <small
                  v-if="fieldDiagnostic(globalFieldPath('extra'))"
                  :id="fieldFeedbackId(globalFieldPath('extra'))"
                  class="field-feedback"
                  :class="`is-${fieldDiagnostic(globalFieldPath('extra'))?.severity}`"
                >
                  {{ fieldDiagnostic(globalFieldPath('extra'))?.message }}
                </small>
              </label>
              <label class="field">
                <span>{{ c.extraProvider }}</span>
                <textarea
                  :id="providerFieldId('extra')"
                  v-model="selectedProvider.extraText"
                  rows="7"
                  spellcheck="false"
                  placeholder="{&#10;  &quot;proxied&quot;: true&#10;}"
                  :aria-invalid="fieldInvalid(providerFieldPath('extra'))"
                  :aria-describedby="fieldDescription(providerFieldPath('extra'))"
                ></textarea>
                <small
                  v-if="fieldDiagnostic(providerFieldPath('extra'))"
                  :id="fieldFeedbackId(providerFieldPath('extra'))"
                  class="field-feedback"
                  :class="`is-${fieldDiagnostic(providerFieldPath('extra'))?.severity}`"
                >
                  {{ fieldDiagnostic(providerFieldPath('extra'))?.message }}
                </small>
              </label>
            </div>
          </div>
        </section>
      </main>

      <button
        v-show="mobileReviewOpen"
        class="mobile-review-backdrop"
        type="button"
        :aria-label="c.closeReview"
        @click="closeMobileReview()"
      ></button>

      <aside
        ref="mobileReviewPanel"
        class="configuration-inspector"
        :class="{ 'is-mobile-open': mobileReviewOpen }"
        :role="mobileReviewOpen ? 'dialog' : undefined"
        :aria-modal="mobileReviewOpen ? 'true' : undefined"
        :aria-label="mobileReviewOpen ? c.reviewConfig : undefined"
        @keydown="handleMobileReviewKeydown"
      >
        <div class="mobile-inspector-heading">
          <strong>{{ c.reviewConfig }}</strong>
          <button
            ref="mobileReviewCloseButton"
            type="button"
            :aria-label="c.closeReview"
            @click="closeMobileReview()"
          >
            <svg aria-hidden="true" viewBox="0 0 24 24"><path d="m6 6 12 12M18 6 6 18" /></svg>
          </button>
        </div>
        <div class="inspector-tabs" role="tablist">
          <button
            id="studio-tab-preview"
            type="button"
            role="tab"
            aria-controls="studio-panel-preview"
            :aria-selected="inspectorTab === 'preview'"
            :tabindex="inspectorTab === 'preview' ? 0 : -1"
            :class="{ 'is-active': inspectorTab === 'preview' }"
            @click="selectInspectorTab('preview')"
            @keydown="handleInspectorTabKeydown"
          >
            {{ c.inspectorPreview }}
          </button>
          <button
            id="studio-tab-validate"
            type="button"
            role="tab"
            aria-controls="studio-panel-validate"
            :aria-selected="inspectorTab === 'validate'"
            :tabindex="inspectorTab === 'validate' ? 0 : -1"
            :class="{ 'is-active': inspectorTab === 'validate' }"
            @click="selectInspectorTab('validate')"
            @keydown="handleInspectorTabKeydown"
          >
            {{ c.inspectorValidate }}
          </button>
        </div>

        <div
          v-show="inspectorTab === 'preview'"
          id="studio-panel-preview"
          class="inspector-pane"
          role="tabpanel"
          aria-labelledby="studio-tab-preview"
          tabindex="0"
        >
          <label
            v-if="hasSensitiveValues"
            class="credential-export-control"
            :class="{ 'is-sensitive': includeCredentials }"
          >
            <input v-model="includeCredentials" type="checkbox" />
            <span>
              <strong>{{ c.includeCredentials }}</strong>
              <small>{{ includeCredentials ? c.credentialsIncluded : c.credentialsExcluded }}</small>
            </span>
          </label>
          <div class="inspector-toolbar">
            <span
              :class="{
                'is-blocked': !canExport,
                'is-warning': canExport && previewWarnings.length,
              }"
            >
              <span aria-hidden="true"></span>
              {{ exportStatusLabel }}
            </span>
            <div>
              <button type="button" :disabled="!canExport" @click="copyConfiguration">
                <svg aria-hidden="true" viewBox="0 0 24 24">
                  <rect x="8" y="8" width="11" height="11" rx="2" />
                  <path d="M16 8V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h2" />
                </svg>
                {{ c.copy }}
              </button>
              <button type="button" :disabled="!canExport" @click="downloadConfiguration">
                <svg aria-hidden="true" viewBox="0 0 24 24"><path d="M12 3v12m0 0 4-4m-4 4-4-4M5 20h14" /></svg>
                {{ c.download }}
              </button>
            </div>
          </div>

          <pre class="code-preview" :aria-label="c.generatedConfigLabel"><code><span v-for="(line, index) in generatedLines" :key="index" class="code-line"><span class="line-number" aria-hidden="true">{{ index + 1 }}</span><span v-html="line"></span></span></code></pre>

          <div class="diagnostic-panel">
            <div class="diagnostic-heading">
              <h2>{{ c.diagnostics }}</h2>
              <span v-if="previewDiagnostics.length">
                {{ previewErrors.length }} {{ errorCountUnit(previewErrors.length) }} ·
                {{ previewWarnings.length }} {{ warningCountUnit(previewWarnings.length) }}
              </span>
            </div>
            <p v-if="!previewDiagnostics.length" class="diagnostic-empty">
              <svg aria-hidden="true" viewBox="0 0 24 24"><path d="m5 12 4 4L19 6" /></svg>
              {{ c.noIssues }}
            </p>
            <ol v-else class="diagnostic-list">
              <li v-for="item in previewDiagnostics" :key="`${item.severity}-${item.path}-${item.message}`" :class="`is-${item.severity}`">
                <button
                  class="diagnostic-action"
                  type="button"
                  :disabled="!diagnosticTargetId(item.path)"
                  @click="focusDiagnostic(item)"
                >
                  <span class="visually-hidden">{{ item.severity === 'error' ? c.error : c.warning }}{{ isEnglish ? ':' : '：' }}</span>
                  <span class="diagnostic-icon" aria-hidden="true">{{ item.severity === 'error' ? '!' : 'i' }}</span>
                  <span class="diagnostic-copy">
                    <code>{{ item.path }}</code>
                    <strong>{{ item.message }}</strong>
                    <span v-if="item.recovery" class="diagnostic-recovery">{{ item.recovery }}</span>
                    <span v-if="diagnosticTargetId(item.path)" class="diagnostic-jump">{{ c.goToField }} →</span>
                  </span>
                </button>
              </li>
            </ol>
          </div>
        </div>

        <div
          v-show="inspectorTab === 'validate'"
          id="studio-panel-validate"
          class="inspector-pane validator-pane"
          role="tabpanel"
          aria-labelledby="studio-tab-validate"
          tabindex="0"
        >
          <div class="validator-actions">
            <button class="studio-button studio-button-secondary" type="button" @click="triggerImport">
              <svg aria-hidden="true" viewBox="0 0 24 24"><path d="M12 3v11m0 0 4-4m-4 4-4-4M5 14v5h14v-5" /></svg>
              {{ c.import }}
            </button>
            <button class="studio-button studio-button-primary" type="button" :disabled="!validationCanApply" @click="applyToBuilder">
              <svg aria-hidden="true" viewBox="0 0 24 24"><path d="M5 12h14m-5-5 5 5-5 5" /></svg>
              {{ c.apply }}
            </button>
          </div>
          <label class="visually-hidden" for="studio-validator-input">{{ c.validatorLabel }}</label>
          <textarea
            id="studio-validator-input"
            v-model="validationInput"
            class="validator-input"
            spellcheck="false"
            :aria-invalid="validationErrors.length ? 'true' : undefined"
            aria-describedby="studio-validator-hint studio-validator-status"
            :placeholder="c.validatorPlaceholder"
            @input="validatorTouched = true"
          ></textarea>
          <div class="validator-foot">
            <span>{{ validationLineCount }} {{ c.lineCount }}</span>
            <span id="studio-validator-hint">{{ c.validatorHint }}</span>
          </div>

          <div class="diagnostic-panel">
            <div class="diagnostic-heading">
              <h2>{{ c.diagnostics }}</h2>
              <span id="studio-validator-status" role="status" aria-live="polite" aria-atomic="true">
                {{ validationErrors.length }} {{ errorCountUnit(validationErrors.length) }} ·
                {{ validationWarnings.length }} {{ warningCountUnit(validationWarnings.length) }}
              </span>
            </div>
            <p v-if="!validationDiagnostics.length" class="diagnostic-empty">
              <svg aria-hidden="true" viewBox="0 0 24 24"><path d="m5 12 4 4L19 6" /></svg>
              {{ c.noIssues }}
            </p>
            <ol v-else class="diagnostic-list">
              <li v-for="item in validationDiagnostics" :key="`${item.severity}-${item.path}-${item.message}`" :class="`is-${item.severity}`">
                <div class="diagnostic-static">
                  <span class="visually-hidden">{{ item.severity === 'error' ? c.error : c.warning }}{{ isEnglish ? ':' : '：' }}</span>
                  <span class="diagnostic-icon" aria-hidden="true">{{ item.severity === 'error' ? '!' : 'i' }}</span>
                  <div>
                    <code>{{ item.path }}</code>
                    <strong>{{ item.message }}</strong>
                    <p v-if="item.recovery">{{ item.recovery }}</p>
                  </div>
                </div>
              </li>
            </ol>
          </div>
        </div>
      </aside>
    </div>

    <div
      class="studio-toast"
      :class="[`is-${toastTone}`, { 'is-visible': toastVisible }]"
      role="status"
      aria-live="polite"
    >
      <span aria-hidden="true">{{ toastTone === 'success' ? '✓' : '!' }}</span>
      {{ toastMessage }}
      <button v-if="lastRemovedProvider" type="button" @click="restoreRemovedProvider">{{ c.undo }}</button>
    </div>
  </div>
</template>
