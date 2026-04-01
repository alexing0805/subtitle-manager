import { computed, ref, watch } from 'vue'

const STORAGE_KEY = 'subtitle-manager:media-display-mode'
const DEFAULT_MODE = 'compact'

const displayMode = ref(DEFAULT_MODE)
let initialized = false

function isValidMode(value) {
  return value === 'compact' || value === 'wide'
}

function initDisplayMode() {
  if (initialized || typeof window === 'undefined') return
  const savedMode = window.localStorage.getItem(STORAGE_KEY)
  if (isValidMode(savedMode)) {
    displayMode.value = savedMode
  }
  initialized = true
}

watch(
  displayMode,
  value => {
    if (typeof window === 'undefined' || !isValidMode(value)) return
    window.localStorage.setItem(STORAGE_KEY, value)
  },
  { flush: 'post' }
)

export function useMediaDisplayMode() {
  initDisplayMode()

  const artPreference = computed(() => (displayMode.value === 'wide' ? 'fanart' : 'poster'))
  const isCompactMode = computed(() => displayMode.value === 'compact')
  const isWideMode = computed(() => displayMode.value === 'wide')

  return {
    displayMode,
    artPreference,
    isCompactMode,
    isWideMode
  }
}
