import { computed, ref, watch } from 'vue'

const STORAGE_KEY = 'subtitle-manager:theme-mode'
const DEFAULT_MODE = 'dark'
const themeMode = ref(DEFAULT_MODE)
const resolvedTheme = ref('dark')
let mediaQuery
let transitionTimer = null
let initialized = false

function isValidThemeMode(value) {
  return value === 'dark' || value === 'oled' || value === 'system'
}

function resolveTheme(mode) {
  if (mode === 'oled') return 'oled'
  if (mode === 'system') {
    return mediaQuery?.matches ? 'dark' : 'dark'
  }
  return 'dark'
}

function triggerThemeTransition() {
  if (typeof document === 'undefined' || typeof window === 'undefined') return
  document.documentElement.classList.add('theme-transition')
  window.clearTimeout(transitionTimer)
  transitionTimer = window.setTimeout(() => {
    document.documentElement.classList.remove('theme-transition')
  }, 360)
}

function applyTheme(mode) {
  if (typeof document === 'undefined') return
  resolvedTheme.value = resolveTheme(mode)
  document.documentElement.dataset.themeMode = mode
  document.documentElement.dataset.themeResolved = resolvedTheme.value
  triggerThemeTransition()
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
    { label: '深灰', value: 'dark', description: '保留霓虹层次和背景光晕' },
    { label: '真黑', value: 'oled', description: 'OLED 纯黑底，减少杂光' },
    { label: '跟随系统', value: 'system', description: '跟随系统深色偏好，默认落到深灰主题' }
  ])

  return {
    themeMode,
    resolvedTheme,
    themeOptions
  }
}
