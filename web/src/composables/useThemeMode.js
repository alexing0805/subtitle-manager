import { computed, ref, watch } from 'vue'

const STORAGE_KEY = 'subtitle-manager:theme-mode'
const DEFAULT_MODE = 'dark'
const themeMode = ref(DEFAULT_MODE)
const resolvedTheme = ref('dark')
let mediaQuery
let initialized = false

function isValidThemeMode(value) {
  return value === 'dark' || value === 'oled' || value === 'system'
}

function resolveTheme(mode) {
  if (mode === 'oled') return 'oled'
  if (mode === 'system') {
    return mediaQuery?.matches ? 'oled' : 'dark'
  }
  return 'dark'
}

function applyTheme(mode) {
  if (typeof document === 'undefined') return
  resolvedTheme.value = resolveTheme(mode)
  document.documentElement.dataset.themeMode = mode
  document.documentElement.dataset.themeResolved = resolvedTheme.value
}

function handleSystemThemeChange() {
  if (themeMode.value === 'system') {
    applyTheme(themeMode.value)
  }
}

function initThemeMode() {
  if (initialized || typeof window === 'undefined') return
  mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
  const savedMode = window.localStorage.getItem(STORAGE_KEY)
  if (isValidThemeMode(savedMode)) {
    themeMode.value = savedMode
  }
  applyTheme(themeMode.value)
  mediaQuery.addEventListener?.('change', handleSystemThemeChange)
  initialized = true
}

watch(
  themeMode,
  value => {
    if (typeof window === 'undefined' || !isValidThemeMode(value)) return
    window.localStorage.setItem(STORAGE_KEY, value)
    applyTheme(value)
  },
  { flush: 'post' }
)

export function useThemeMode() {
  initThemeMode()

  const themeOptions = computed(() => [
    { label: '深灰', value: 'dark', description: '默认霓虹深灰背景' },
    { label: '真黑色', value: 'oled', description: 'OLED 纯黑背景' },
    { label: '跟随系统', value: 'system', description: '自动匹配系统深色偏好' }
  ])

  return {
    themeMode,
    resolvedTheme,
    themeOptions
  }
}
