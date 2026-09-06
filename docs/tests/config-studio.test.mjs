// npm --prefix docs run test:studio
// Use the existing Vite/Vue toolchain, not Node's newer TypeScript stripping API.
// Exercise setup, template events and disabled gates with real Vue reactivity;
// browser storage, file selection, clipboard and download are in-memory doubles.
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import vm from 'node:vm'
import { afterEach, test } from 'node:test'
import { transformWithOxc } from 'vite'
import * as Vue from 'vue'

const sfc = await readFile(new URL('../.vitepress/theme/components/ConfigStudio.vue', import.meta.url), 'utf8')
const model = JSON.parse(await readFile(new URL('../../ddns/config/field-model.json', import.meta.url), 'utf8'))
const setup = sfc.match(/<script setup lang="ts">([\s\S]*?)<\/script>/)[1]
const { code } = await transformWithOxc(setup, 'ConfigStudio.ts')
const script = code.replace(/^import[\s\S]*?;\s*/gm, '')
const tags = [...sfc.split('</script>')[1].matchAll(/<(?:button|input|textarea|select)\b(?:[^>"']|"[^"]*"|'[^']*')*>/g)]
  .map((match) => match[0])
const attr = (tag, name) => tag.match(new RegExp(`\\s${name}="([\\s\\S]*?)"`))?.[1]
const plain = (value) => JSON.parse(JSON.stringify(value))
const scopes = []
afterEach(() => scopes.splice(0).forEach((scope) => scope.stop()))

async function studio(storage = new Map()) {
  const mounted = [], timers = new Map(), listeners = new Map(), clipboard = [], downloads = [], blobs = new Map()
  let timerId = 0
  class MemoryURL extends URL {
    static createObjectURL(blob) { const key = `blob:${++timerId}`; blobs.set(key, blob); return key }
    static revokeObjectURL(key) { blobs.delete(key) }
  }
  const context = vm.createContext({
    ...Vue, __DDNS_FIELD_MODEL__: model,
    onMounted: (fn) => mounted.push(fn), onBeforeUnmount: () => {},
    useData: () => ({ lang: Vue.ref('en') }), useRouter: () => ({}), withBase: (value) => value,
    readHistoryPosition: () => null, URL: MemoryURL, Blob,
    setTimeout: (fn, delay) => { const id = ++timerId; timers.set(id, { fn, delay }); return id },
    clearTimeout: (id) => timers.delete(id),
    window: {
      location: new URL('https://docs.example.com/en/config/studio'), history: { state: null },
      matchMedia: () => ({ matches: true }), confirm: () => true,
      addEventListener: (name, fn) => listeners.set(name, fn), removeEventListener: (name) => listeners.delete(name),
      sessionStorage: {
        getItem: (key) => storage.get(key) ?? null,
        setItem: (key, value) => storage.set(key, value),
        removeItem: (key) => storage.delete(key),
      },
    },
    document: {
      body: { classList: { toggle() {}, remove() {} } },
      getElementById: () => ({ focus() {} }),
      createElement: (name) => {
        assert.equal(name, 'a')
        return { click() { downloads.push(blobs.get(this.href)) } }
      },
    },
    navigator: { clipboard: { async writeText(text) { clipboard.push(text) } } },
  })
  const scope = Vue.effectScope()
  scopes.push(scope)
  scope.run(() => vm.runInContext(`${script}
    globalThis.bindings = {
      selectedProvider, globalState, providers, activeSection, inspectorTab,
      sourceAdvancedOpen, runtimeAdvancedOpen, validationInput, validatorTouched,
      hasUnsavedChanges, validationCanApply, validationErrors, canExport, previewErrors,
      generatedJson, importFile, applyToBuilder, copyConfiguration, downloadConfiguration,
      selectInspectorTab, toggleProviderPicker, chooseProvider, selectSection,
      resetBuilder, duplicateProvider, addProvider,
      ...(typeof validationFromFile === 'undefined' ? {} : { validationFromFile })
    };
    globalThis.draftKey = DRAFT_STORAGE_KEY;
    globalThis.saveDelay = DRAFT_SAVE_DELAY;
  `, context))
  context.ui = Vue.proxyRefs(context.bindings)
  const evaluate = (expression, locals = {}) => {
    context.locals = locals
    return vm.runInContext(`with (ui) { with (locals) { ${expression} } }`, context)
  }
  const settle = async () => { await Vue.nextTick(); await Vue.nextTick() }
  for (const fn of mounted) await fn()
  await settle()
  const api = {
    storage,
    get: (name) => evaluate(name),
    json: () => JSON.parse(evaluate('generatedJson')),
    draft: () => storage.has(context.draftKey) ? JSON.parse(storage.get(context.draftKey)) : null,
    async click(handler, locals = {}) {
      const tag = tags.find((tag) => tag.startsWith('<button') && attr(tag, '@click') === handler)
      assert(tag, `Missing template button: ${handler}`)
      const disabled = attr(tag, ':disabled')
      assert(!disabled || !evaluate(disabled, locals), `Button is disabled: ${handler}`)
      await evaluate(/^\w+$/.test(handler) ? `${handler}()` : handler, locals)
      await settle()
    },
    async input(name, value) {
      const tag = tags.find((tag) => attr(tag, 'v-model') === name)
      assert(tag, `Missing template input: ${name}`)
      evaluate(`${name} = $event.target.value; ${attr(tag, '@input') || ''}`, { $event: { target: { value } } })
      await settle()
    },
    async import(value) {
      assert(tags.some((tag) => attr(tag, '@change') === 'importFile'))
      await evaluate('importFile($event)', {
        $event: { target: { value: 'config.json', files: [{ text: async () => JSON.stringify(value) }] } },
      })
      await settle()
      assert.deepEqual(plain(evaluate('validationErrors')), [])
      assert.equal(evaluate('validationCanApply'), true)
    },
    async apply() { await api.click('applyToBuilder') },
    async persist() {
      await settle()
      for (const [id, timer] of timers) {
        if (timer.delay !== context.saveDelay) continue
        timers.delete(id)
        timer.fn()
      }
      await settle()
    },
    async refresh() {
      const event = { warned: false, preventDefault() { this.warned = true } }
      listeners.get('beforeunload')(event)
      scope.stop()
      return { warned: event.warned, page: await studio(storage) }
    },
    async copy() { await api.click('copyConfiguration'); return JSON.parse(clipboard.at(-1)) },
    async download() {
      await api.click('downloadConfiguration')
      return JSON.parse(await downloads.at(-1).text())
    },
  }
  return api
}

const base = {
  $schema: model.schema.url, ssl: true, cache: false, log: { level: 'INFO' },
  providers: [{
    provider: 'cloudflare', id: null, token: 'offline-placeholder',
    ipv4: ['home.example.com'], ipv6: [], index4: ['public', 'default'], index6: false, ttl: 300,
  }],
}
async function importApply(value) {
  const page = await studio()
  await page.import(value)
  await page.apply()
  assert.equal(page.get('canExport'), true)
  return page
}
async function createUnsaved() {
  const page = await studio()
  await page.click('toggleProviderPicker')
  await page.click('chooseProvider(provider.value)', { provider: { value: 'cloudflare' } })
  await page.input('selectedProvider.token', 'offline-page-token')
  await page.click('selectSection(section.key)', { section: { key: 'records' } })
  await page.input('selectedProvider.ipv4Text', 'unsaved.example.com')
  await page.click('sourceAdvancedOpen = !sourceAdvancedOpen')
  await page.input('selectedProvider.ttl', '600')
  await page.persist()
  return page
}

test('page-created, unexported JSON edits survive Apply and refresh', async () => {
  const page = await createUnsaved()
  await page.click("selectInspectorTab('validate')")
  const edited = page.json()
  edited.providers[0].ttl = 900
  await page.input('validationInput', JSON.stringify(edited))
  await page.apply()
  assert.equal(page.get('hasUnsavedChanges'), true)
  await page.persist()
  assert(page.draft())
  const { page: restored, warned } = await page.refresh()
  assert.equal(warned, true)
  assert.deepEqual(restored.json(), edited)
  assert.equal(restored.get('validatorTouched'), false)
  await restored.copy()
  assert.equal(restored.get('hasUnsavedChanges'), false)
  assert.equal(restored.draft(), null)
})

test('ordinary unsaved refresh and successful export keep their existing behavior', async () => {
  const page = await createUnsaved()
  const original = page.json()
  const { page: restored, warned } = await page.refresh()
  assert.equal(warned, true)
  assert.deepEqual(restored.json(), original)
  assert.deepEqual(await restored.copy(), original)
  assert.deepEqual(await restored.download(), original)
  assert.equal(restored.get('hasUnsavedChanges'), false)
  assert.equal(restored.draft(), null)
})

test('unchanged saved-file imports stay clean, including a draft restored before Apply', async () => {
  const page = await studio()
  await page.import(base)
  await page.persist()
  const { page: restored } = await page.refresh()
  await restored.apply()
  assert.equal(restored.get('hasUnsavedChanges'), false)
  assert.equal(restored.draft(), null)
  assert.deepEqual(await restored.download(), base)
})

test('editing imported JSON invalidates its saved-file provenance', async () => {
  const page = await studio()
  await page.import(base)
  const edited = plain(base)
  edited.providers[0].ttl = 900
  await page.input('validationInput', JSON.stringify(edited))
  await page.apply()
  assert.equal(page.get('hasUnsavedChanges'), true)
  const { page: restored } = await page.refresh()
  assert.equal(restored.json().providers[0].ttl, 900)
})

test('JSON regenerated from an edited builder is not treated as the imported file', async () => {
  const page = await importApply(base)
  await page.click('selectSection(section.key)', { section: { key: 'records' } })
  await page.input('selectedProvider.ipv4Text', 'changed.example.com')
  await page.click("selectInspectorTab('validate')")
  await page.apply()
  assert.equal(page.get('hasUnsavedChanges'), true)
  const { page: restored } = await page.refresh()
  assert.deepEqual(restored.json().providers[0].ipv4, ['changed.example.com'])
})

test('old v2 drafts without import provenance are retained conservatively', async () => {
  const page = await studio()
  await page.import(base)
  await page.persist()
  const draft = page.draft()
  delete draft.validationFromFile
  const storage = new Map(page.storage)
  storage.set([...storage.keys()][0], JSON.stringify(draft))
  const restored = await studio(storage)
  await restored.apply()
  assert.equal(restored.get('hasUnsavedChanges'), true)
})

test('v1 drafts retain explicit empty overrides and unapplied validation text', async () => {
  const config = { ...base, extra: { proxied: true }, providers: [{ ...base.providers[0], extra: {} }] }
  const validationInput = '{ "unfinished":'
  const restored = await studio(new Map([[
    'ddns-config-studio-draft-v1',
    JSON.stringify({ version: 1, config, validationInput }),
  ]]))
  assert.deepEqual(restored.json().providers[0].extra, {})
  assert.equal(restored.get('validationInput'), validationInput)
  assert.equal(restored.get('validatorTouched'), true)
  assert.equal(restored.get('hasUnsavedChanges'), true)
})

const extraCases = [
  ['flat global plus provider extra', { proxied: true }, { extra: { comment: 'home' } }, { comment: 'home', proxied: true }],
  ['nested global plus flat provider field', { extra: { proxied: true } }, { comment: 'home' }, { proxied: true, comment: 'home' }],
  ['explicit empty provider override', { extra: { proxied: true } }, { extra: {} }, {}],
  ['nonempty provider override', { extra: { proxied: true } }, { extra: { proxied: false } }, { proxied: false }],
  ['flat aliases override nested fields', { extra_proxied: true }, { extra: { proxied: false } }, { proxied: true }],
  ['flat alias order survives cross-scope overrides', { proxied: true, extra_proxied: false }, { proxied: true }, { proxied: false }],
  ['nested custom objects flatten before inheritance', { settings: { first: 1, second: 2 } }, { settings: { first: 3 } }, { settings_first: 3, settings_second: 2 }],
]
for (const [name, global, provider, expected] of extraCases) {
  test(`extra round trip: ${name}`, async () => {
    const page = await importApply({ ...base, ...global, providers: [{ ...base.providers[0], ...provider }] })
    assert.deepEqual(JSON.parse(page.get('selectedProvider.extraText')), expected)
    assert.deepEqual((await page.copy()).providers[0].extra, expected)
    assert.deepEqual((await page.download()).providers[0].extra, expected)
    // Change an unrelated visible field so the normal draft lifecycle saves this state.
    await page.click('selectSection(section.key)', { section: { key: 'records' } })
    await page.input('selectedProvider.ipv4Text', 'draft.example.com')
    const { page: restored } = await page.refresh()
    assert.deepEqual(restored.json().providers[0].extra, expected)
  })
}

test('providers without custom fields keep inheriting global extra', async () => {
  const page = await importApply({ ...base, proxied: true })
  assert.equal(page.get('selectedProvider.extraText'), '')
  assert(!('extra' in page.json().providers[0]))
  assert.deepEqual(page.json().extra, { proxied: true })
})

test('empty extra text inherits, while an explicit object remains an override', async () => {
  const page = await importApply({ ...base, extra: { proxied: true }, providers: [{ ...base.providers[0], extra: {} }] })
  await page.click('selectSection(section.key)', { section: { key: 'runtime' } })
  await page.input('selectedProvider.extraText', '')
  assert(!('extra' in page.json().providers[0]))
  await page.input('selectedProvider.extraText', '{}')
  assert.deepEqual(page.json().providers[0].extra, {})
  await page.input('globalState.extraText', '{}')
  assert.deepEqual(page.json().extra, {})
})

test('new, duplicated and changed providers do not retain previous custom overrides', async () => {
  const page = await importApply({ ...base, extra: { proxied: true }, providers: [{ ...base.providers[0], extra: {} }] })
  await page.click('duplicateProvider')
  assert.equal(page.get('selectedProvider.extraText'), '')
  assert(!('extra' in page.json().providers[1]))
  assert(!('token' in page.json().providers[1]))
  await page.click('addProvider')
  assert(!('extra' in page.json().providers[2]))
  await page.click('selectSection(section.key)', { section: { key: 'runtime' } })
  await page.input('selectedProvider.extraText', '{"comment":"discard on provider change"}')
  await page.click('selectSection(section.key)', { section: { key: 'provider' } })
  await page.click('toggleProviderPicker')
  await page.click('chooseProvider(provider.value)', { provider: { value: 'cloudflare' } })
  assert.equal(page.get('selectedProvider.extraText'), '')
  await page.click('resetBuilder')
  assert.equal(page.get('hasUnsavedChanges'), false)
  assert.equal(page.get('selectedProvider.extraText'), '')
})

test('legacy single-provider imports retain extra values and absence', async () => {
  const legacy = { dns: 'cloudflare', token: 'offline-placeholder', ipv4: ['home.example.com'] }
  const inherited = await importApply(legacy)
  assert(!('extra' in inherited.json().providers[0]))
  const explicit = await importApply({ ...legacy, extra: {} })
  assert.deepEqual(explicit.json().providers[0].extra, {})
  const fields = await importApply({ ...legacy, extra: { proxied: false }, extra_proxied: true })
  assert.deepEqual(fields.json().providers[0].extra, { proxied: true })
})
