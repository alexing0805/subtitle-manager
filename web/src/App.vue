<template>
  <div class="app infuse-theme">
    <div class="app-background" aria-hidden="true">
      <div class="bg-grid"></div>
      <div class="bg-noise"></div>
      <div class="bg-orb orb-a"></div>
      <div class="bg-orb orb-b"></div>
      <div class="bg-beam beam-a"></div>
      <div class="bg-beam beam-b"></div>
    </div>

    <!-- 鼠标光球（放App层级，不受任何子元素transform影响） -->
    <div class="app-mouse-glow" :style="appGlowStyle"></div>

    <Sidebar :mobile-open="mobileMenuOpen" @close="mobileMenuOpen = false" />

    <header class="mobile-topbar">
      <button class="mobile-menu-button" @click="mobileMenuOpen = true" aria-label="打开导航">
        <el-icon><Menu /></el-icon>
      </button>
      <div class="mobile-topbar-copy">
        <span class="mobile-eyebrow">Subtitle Manager</span>
        <strong class="mobile-title">{{ pageTitle }}</strong>
      </div>
    </header>

    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { computed, reactive, ref, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { Menu } from '@element-plus/icons-vue'
import Sidebar from './components/Sidebar.vue'
import { useThemeMode } from './composables/useThemeMode'

const route = useRoute()
const mobileMenuOpen = ref(false)
useThemeMode()

// App-level mouse glow tracking
const appPointer = reactive({ x: 0, y: 0, active: false })
const isOverInteractive = ref(false)

const appGlowStyle = computed(() => ({
  left: `${appPointer.x}px`,
  top: `${appPointer.y}px`,
  opacity: appPointer.active ? 1 : 0,
  width: isOverInteractive.value ? '36px' : '20px',
  height: isOverInteractive.value ? '36px' : '20px',
  background: isOverInteractive.value
    ? 'radial-gradient(circle, rgba(255, 107, 53, 0.9) 0%, rgba(255, 107, 53, 0.4) 60%, transparent 100%)'
    : 'radial-gradient(circle, rgba(34, 246, 255, 1) 0%, rgba(34, 246, 255, 0.5) 50%, transparent 100%)'
}))

function isInteractive(el) {
  if (!el) return false

  const interactiveSelectors = [
    'a',
    'button',
    '[role="button"]',
    '[tabindex]:not([tabindex="-1"])',
    '[disabled]',
    '.action-card',
    '.stat-card',
    '.clickable',
    '.el-button',
    '.infuse-button',
    '.scan-btn',
    '.movie-card',
    '.show-card',
    '.season-tab',
    '.action-btn',
    '.apple-button',
    '[style*="cursor: pointer"]',
    '[style*="cursor:pointer"]',
    '[style*="cursor: not-allowed"]',
    '[style*="cursor:not-allowed"]'
  ].join(', ')

  if (el.closest(interactiveSelectors)) {
    return true
  }

  let current = el
  while (current && current !== document.body) {
    const { cursor } = window.getComputedStyle(current)
    if (cursor === 'pointer' || cursor === 'not-allowed') {
      return true
    }
    current = current.parentElement
  }

  return false
}

function onDocMouseMove(e) {
  appPointer.x = e.clientX
  appPointer.y = e.clientY
  appPointer.active = true
  isOverInteractive.value = !!isInteractive(e.target)
}

function onDocMouseLeave() {
  appPointer.active = false
  isOverInteractive.value = false
}

onMounted(() => {
  document.addEventListener('mousemove', onDocMouseMove)
  document.addEventListener('mouseleave', onDocMouseLeave)
})

onUnmounted(() => {
  document.removeEventListener('mousemove', onDocMouseMove)
  document.removeEventListener('mouseleave', onDocMouseLeave)
})

const routeTitles = {
  '/': '仪表盘',
  '/movies': '电影',
  '/tvshows': '电视剧',
  '/anime': '动漫',
  '/batch-upload': '批量上传',
  '/settings': '设置'
}

const pageTitle = computed(() => routeTitles[route.path] || '字幕管理器')
</script>

<style>
:root {
  --infuse-bg-primary: #060816;
  --infuse-bg-secondary: rgba(9, 13, 33, 0.86);
  --infuse-bg-tertiary: rgba(15, 24, 52, 0.92);
  --infuse-bg-card: rgba(10, 16, 38, 0.72);
  --infuse-bg-hover: rgba(22, 35, 72, 0.92);

  --infuse-accent: #22f6ff;
  --infuse-accent-hover: #77f7ff;
  --infuse-accent-alt: #ff2bd6;
  --infuse-accent-warn: #ffd84d;
  --infuse-accent-glow: rgba(34, 246, 255, 0.32);
  --infuse-magenta-glow: rgba(255, 43, 214, 0.28);

  --infuse-text-primary: #f4f7ff;
  --infuse-text-secondary: rgba(230, 238, 255, 0.76);
  --infuse-text-tertiary: rgba(205, 220, 255, 0.58);
  --infuse-text-muted: rgba(163, 186, 235, 0.52);

  --infuse-border: rgba(92, 133, 255, 0.18);
  --infuse-border-hover: rgba(119, 247, 255, 0.48);

  --infuse-gradient-overlay: linear-gradient(180deg, rgba(2, 6, 20, 0.08) 0%, rgba(6, 10, 29, 0.62) 48%, rgba(6, 8, 22, 0.96) 100%);
  --infuse-gradient-card: linear-gradient(145deg, rgba(12, 20, 48, 0.84) 0%, rgba(6, 10, 28, 0.88) 100%);
  --infuse-gradient-neon: linear-gradient(135deg, rgba(34, 246, 255, 0.18) 0%, rgba(255, 43, 214, 0.16) 100%);
  --infuse-gradient-button: linear-gradient(135deg, #22f6ff 0%, #00a8ff 45%, #ff2bd6 100%);

  --infuse-shadow-sm: 0 8px 20px rgba(0, 0, 0, 0.18);
  --infuse-shadow-md: 0 18px 38px rgba(0, 0, 0, 0.35);
  --infuse-shadow-lg: 0 28px 70px rgba(0, 0, 0, 0.45);
  --infuse-shadow-glow: 0 0 0 1px rgba(34, 246, 255, 0.2), 0 0 26px rgba(34, 246, 255, 0.2), 0 18px 42px rgba(7, 14, 35, 0.48);

  --infuse-radius-sm: 8px;
  --infuse-radius-md: 12px;
  --infuse-radius-lg: 16px;
  --infuse-radius-xl: 24px;

  --infuse-transition-fast: 0.15s ease;
  --infuse-transition-normal: 0.25s ease;
  --infuse-transition-slow: 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html {
  scroll-behavior: smooth;
  font-size: 16px; /* establish base for rem units */
  /* iOS viewport fit */
  viewport-fit: cover;
}

body {
  font-family: "SF Pro Display", "PingFang SC", "Microsoft YaHei UI", "Microsoft YaHei", "Segoe UI", sans-serif;
  font-display: swap;
  background: var(--infuse-bg-primary);
  color: var(--infuse-text-primary);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  line-height: 1.5;
  overflow-x: hidden;
  cursor: none !important;
  transition: background-color 0.3s ease, opacity 0.3s ease;
}

body::before {
  content: "";
  position: fixed;
  inset: 0;
  background:
    linear-gradient(180deg, rgba(6, 8, 22, 0.34), rgba(6, 8, 22, 0.82)),
    radial-gradient(circle at top, rgba(34, 246, 255, 0.08), transparent 38%);
  pointer-events: none;
  z-index: -2;
}

.app {
  display: flex;
  min-height: 100vh;
  background: var(--infuse-bg-primary);
  position: relative;
  isolation: isolate;
  transition: background-color 0.3s ease, opacity 0.3s ease;
}

.mobile-topbar {
  display: none;
}

.app-background {
  position: fixed;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
  z-index: -1;
  transition: opacity 0.3s ease, background-color 0.3s ease;
}

.bg-grid,
.bg-noise,
.bg-orb,
.bg-beam {
  position: absolute;
  inset: 0;
  transition: opacity 0.3s ease, background-color 0.3s ease;
}

:root[data-theme-resolved='oled'] {
  --infuse-bg-primary: #000000;
  --infuse-bg-secondary: rgba(0, 0, 0, 0.92);
  --infuse-bg-tertiary: rgba(0, 0, 0, 0.96);
  --infuse-bg-card: rgba(0, 0, 0, 0.82);
  --infuse-bg-hover: rgba(8, 8, 8, 0.98);
  --infuse-gradient-overlay: linear-gradient(180deg, rgba(0, 0, 0, 0.1) 0%, rgba(0, 0, 0, 0.78) 48%, rgba(0, 0, 0, 0.98) 100%);
  --infuse-gradient-card: linear-gradient(145deg, rgba(8, 8, 8, 0.9) 0%, rgba(0, 0, 0, 0.96) 100%);
}

.bg-grid {
  background:
    linear-gradient(rgba(119, 247, 255, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(119, 247, 255, 0.05) 1px, transparent 1px);
  background-size: 72px 72px;
  mask-image: linear-gradient(180deg, rgba(0, 0, 0, 0.66), transparent 96%);
}

.bg-noise {
  opacity: 0.18;
  background-image:
    radial-gradient(circle at 20% 20%, rgba(255, 255, 255, 0.08) 0 1px, transparent 1px),
    radial-gradient(circle at 80% 30%, rgba(34, 246, 255, 0.12) 0 1px, transparent 1px),
    radial-gradient(circle at 60% 80%, rgba(255, 43, 214, 0.12) 0 1px, transparent 1px);
  background-size: 140px 140px, 210px 210px, 180px 180px;
}

.bg-orb {
  border-radius: 999px;
  filter: blur(24px);
  opacity: 0.55;
  animation: orbFloat 16s ease-in-out infinite alternate;
}

.orb-a {
  top: 4%;
  left: -8%;
  width: 32vw;
  height: 32vw;
  max-width: 480px;
  max-height: 480px;
  background: radial-gradient(circle, rgba(34, 246, 255, 0.28) 0%, rgba(34, 246, 255, 0.08) 45%, transparent 72%);
}

.orb-b {
  right: -10%;
  bottom: 10%;
  width: 28vw;
  height: 28vw;
  max-width: 420px;
  max-height: 420px;
  background: radial-gradient(circle, rgba(255, 43, 214, 0.22) 0%, rgba(255, 43, 214, 0.07) 42%, transparent 72%);
  animation-duration: 20s;
}

.bg-beam {
  background: linear-gradient(90deg, transparent 0%, rgba(34, 246, 255, 0.06) 48%, transparent 100%);
  transform: skewY(-18deg);
  opacity: 0.5;
  animation: beamSlide 14s linear infinite;
}

.beam-a {
  left: -24%;
}

.beam-b {
  left: 48%;
  background: linear-gradient(90deg, transparent 0%, rgba(255, 43, 214, 0.05) 48%, transparent 100%);
  animation-duration: 18s;
}

.main-content {
  flex: 1;
  margin-left: 280px;
  padding: 16px 48px;
  min-height: 100vh;
  background: transparent;
  position: relative;
}

.infuse-card {
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.03), transparent 34%),
    var(--infuse-gradient-card);
  border-radius: var(--infuse-radius-lg);
  border: 1px solid var(--infuse-border);
  overflow: hidden;
  transition: transform var(--infuse-transition-normal), box-shadow var(--infuse-transition-normal), border-color var(--infuse-transition-normal), background var(--infuse-transition-normal);
  backdrop-filter: blur(22px);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04), var(--infuse-shadow-sm);
  position: relative;
  will-change: transform;
}

.infuse-card::before {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(34, 246, 255, 0.08), transparent 40%, rgba(255, 43, 214, 0.08));
  opacity: 0;
  transition: opacity var(--infuse-transition-normal);
  pointer-events: none;
}

.infuse-card:hover {
  border-color: var(--infuse-border-hover);
  transform: translateY(-4px) scale(1.005);
  box-shadow: var(--infuse-shadow-glow), var(--infuse-shadow-lg);
}

.infuse-card:hover::before {
  opacity: 1;
}

.infuse-button {
  background: var(--infuse-gradient-button);
  color: #04111c;
  border: none;
  border-radius: 100px;
  padding: 12px 32px;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  transition: all var(--infuse-transition-fast);
  display: inline-flex;
  align-items: center;
  gap: 8px;
  white-space: nowrap;
  min-width: fit-content;
  position: relative;
  overflow: hidden;
  box-shadow: 0 12px 28px rgba(0, 168, 255, 0.28);
}

.infuse-button::before {
  content: "";
  position: absolute;
  inset: 1px;
  border-radius: inherit;
  background: linear-gradient(135deg, rgba(255,255,255,0.22), rgba(255,255,255,0.04));
  opacity: 0.8;
  pointer-events: none;
}

.infuse-button > * {
  position: relative;
  z-index: 1;
}

.infuse-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 0 0 1px rgba(119, 247, 255, 0.3), 0 0 26px rgba(34, 246, 255, 0.24), 0 18px 36px rgba(255, 43, 214, 0.18);
}

.infuse-button:active {
  transform: scale(0.98);
}

.infuse-button.secondary {
  background: rgba(10, 18, 42, 0.78);
  color: var(--infuse-text-primary);
  border: 1px solid var(--infuse-border);
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.04);
}

.infuse-button.secondary:hover {
  background: var(--infuse-bg-hover);
  border-color: var(--infuse-border-hover);
}

.page-title {
  font-size: 42px;
  font-weight: 800;
  margin-bottom: 8px;
  letter-spacing: 0.02em;
  text-transform: uppercase;
  background: linear-gradient(135deg, #f4f7ff 0%, #77f7ff 42%, #ff8be9 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  text-shadow: 0 0 18px rgba(34, 246, 255, 0.16);
}

.page-subtitle {
  font-size: 16px;
  color: var(--infuse-text-secondary);
  margin-bottom: 40px;
  font-weight: 400;
  max-width: 72ch;
}

.el-input__wrapper {
  background: rgba(8, 14, 34, 0.84) !important;
  border: 1px solid var(--infuse-border) !important;
  border-radius: var(--infuse-radius-md) !important;
  box-shadow: none !important;
  backdrop-filter: blur(12px);
}

.el-input__wrapper:hover {
  border-color: var(--infuse-border-hover) !important;
}

.el-input__wrapper.is-focus {
  border-color: var(--infuse-accent) !important;
  box-shadow: 0 0 0 1px rgba(34, 246, 255, 0.32), 0 0 0 4px rgba(34, 246, 255, 0.12) !important;
}

.el-input__inner {
  color: var(--infuse-text-primary) !important;
  background: transparent !important;
}

.el-input__inner::placeholder {
  color: var(--infuse-text-muted) !important;
}

.el-select .el-input__wrapper,
.el-textarea__inner,
.el-input-number .el-input__wrapper {
  background: rgba(8, 14, 34, 0.84) !important;
}

.el-textarea__inner {
  color: var(--infuse-text-primary) !important;
  border: 1px solid var(--infuse-border) !important;
  box-shadow: none !important;
}

.el-dialog {
  background:
    linear-gradient(180deg, rgba(255,255,255,0.04), transparent 24%),
    rgba(7, 11, 29, 0.92) !important;
  border-radius: var(--infuse-radius-xl) !important;
  border: 1px solid var(--infuse-border) !important;
  box-shadow: 0 0 0 1px rgba(34, 246, 255, 0.12), 0 24px 80px rgba(0, 0, 0, 0.5), 0 0 26px rgba(255, 43, 214, 0.12) !important;
  backdrop-filter: blur(26px) !important;
}

.el-dialog__title {
  color: var(--infuse-text-primary) !important;
  font-weight: 700 !important;
  font-size: 20px !important;
}

.el-dialog__header {
  border-bottom: 1px solid var(--infuse-border) !important;
  padding: 24px 32px !important;
}

.el-dialog__body {
  color: var(--infuse-text-secondary) !important;
  padding: 24px 32px !important;
}

.el-button {
  border-radius: 100px !important;
  font-weight: 700 !important;
  transition: all var(--infuse-transition-fast) !important;
}

.el-button--primary {
  background: linear-gradient(135deg, #22f6ff 0%, #00a8ff 50%, #ff2bd6 100%) !important;
  border-color: rgba(119, 247, 255, 0.45) !important;
  color: #051420 !important;
}

.el-button--primary:hover {
  box-shadow: 0 0 0 1px rgba(119, 247, 255, 0.24), 0 0 22px rgba(34, 246, 255, 0.2) !important;
}

.el-button--default,
.el-button:not(.el-button--primary):not(.el-button--success):not(.el-button--danger) {
  background: rgba(9, 14, 36, 0.82) !important;
  border-color: var(--infuse-border) !important;
  color: var(--infuse-text-primary) !important;
}

.el-tag {
  border-radius: 100px !important;
  font-weight: 700 !important;
  padding: 4px 12px !important;
}

.el-tag--success {
  background: rgba(34, 197, 94, 0.15) !important;
  border-color: rgba(34, 197, 94, 0.3) !important;
  color: #22c55e !important;
}

.el-tag--warning {
  background: rgba(255, 216, 77, 0.12) !important;
  border-color: rgba(255, 216, 77, 0.28) !important;
  color: var(--infuse-accent-warn) !important;
}

.el-loading-mask {
  background: rgba(6, 8, 22, 0.72) !important;
  backdrop-filter: blur(4px) !important;
}

::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: var(--infuse-bg-secondary);
}

::-webkit-scrollbar-thumb {
  background: var(--infuse-border-hover);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: var(--infuse-text-muted);
}

@keyframes orbFloat {
  from {
    transform: translate3d(0, 0, 0) scale(1);
  }
  to {
    transform: translate3d(40px, -30px, 0) scale(1.08);
  }
}

@keyframes beamSlide {
  from {
    transform: translateX(-28%) skewY(-18deg);
  }
  to {
    transform: translateX(28%) skewY(-18deg);
  }
}

@media (prefers-reduced-motion: reduce) {
  html {
    scroll-behavior: auto;
  }

  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}

@media (max-width: 1200px) {
  .main-content {
    margin-left: 240px;
    padding: 32px;
  }
}

@media (max-width: 768px) {
  .mobile-topbar {
    position: fixed;
    inset: 0 0 auto 0;
    height: 72px;
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 14px 18px;
    padding-top: max(14px, env(safe-area-inset-top));
    background: rgba(6, 10, 25, 0.82);
    backdrop-filter: blur(18px);
    border-bottom: 1px solid var(--infuse-border);
    z-index: 250;
    box-shadow: 0 10px 24px rgba(0, 0, 0, 0.24);
  }

  .mobile-menu-button {
    width: 42px;
    height: 42px;
    border: 1px solid var(--infuse-border);
    border-radius: 12px;
    background: var(--infuse-bg-card);
    color: var(--infuse-text-primary);
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
    cursor: pointer;
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.04);
  }

  .mobile-topbar-copy {
    min-width: 0;
    display: flex;
    flex-direction: column;
  }

  .mobile-eyebrow {
    font-size: 11px;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: var(--infuse-text-muted);
  }

  .mobile-title {
    font-size: 18px;
    line-height: 1.1;
    color: var(--infuse-text-primary);
  }

  .main-content {
    margin-left: 0;
    padding: 80px 14px 20px;
    /* iOS notch / dynamic island safe area */
    padding-top: max(80px, env(safe-area-inset-top));
    padding-bottom: max(20px, env(safe-area-inset-bottom));
    padding-left: max(14px, env(safe-area-inset-left));
    padding-right: max(14px, env(safe-area-inset-right));
  }

  .page-title {
    font-size: 32px;
  }

  .page-subtitle {
    margin-bottom: 28px;
  }

  .el-dialog {
    width: calc(100vw - 20px) !important;
    margin-top: 5vh !important;
  }

  .el-dialog__header {
    padding: 18px 20px !important;
  }

  .el-dialog__body {
    padding: 18px 20px !important;
  }

  .el-dialog__footer {
    padding: 14px 20px 20px !important;
  }
}

/* --- Global Polish --- */
@keyframes shimmer {
  0% { transform: translateX(-100%) skewX(-15deg); }
  100% { transform: translateX(300%) skewX(-15deg); }
}

.infuse-card {
  position: relative;
  overflow: hidden;
}

.infuse-card::after {
  content: "";
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgba(255, 255, 255, 0.12) 40%,
    rgba(255, 255, 255, 0.18) 50%,
    rgba(255, 255, 255, 0.12) 60%,
    transparent 100%
  );
  transition: opacity 0.2s ease;
  z-index: 1;
  pointer-events: none;
  opacity: 0;
}

.infuse-card:hover::after {
  animation: shimmer 0.8s ease-out forwards;
  opacity: 1;
}

/* 全局隐藏原生鼠标，避免子页面 scoped 样式重新设置 pointer/not-allowed */
html,
body,
#app,
#app * {
  cursor: none !important;
}

/* App-level mouse glow — always on top, viewport-anchored */
.app-mouse-glow {
  position: fixed;
  width: 20px;
  height: 20px;
  background: radial-gradient(circle, rgba(34, 246, 255, 1) 0%, rgba(34, 246, 255, 0.5) 50%, transparent 100%);
  border-radius: 50%;
  pointer-events: none;
  z-index: 9999;
  transform: translate(-50%, -50%);
  transition: opacity 0.3s ease;
}

/* Better Text Rendering */
h1, h2, h3 {
  letter-spacing: -0.02em;
  text-rendering: optimizeLegibility;
}

/* Global Selection Color */
::selection {
  background: var(--infuse-accent);
  color: #000;
}

/* Mobile touch targets - minimum 44px */
@media (max-width: 768px) {
  button, .el-button, .el-input__wrapper, a {
    min-height: 44px;
    min-width: 44px;
  }

  /* Prevent text selection on interactive elements */
  button, .el-button {
    -webkit-tap-highlight-color: transparent;
  }
}

/* Smooth Scrollbar */
body::-webkit-scrollbar {
  width: 10px;
}
body::-webkit-scrollbar-thumb {
  background: linear-gradient(var(--infuse-accent), var(--infuse-accent-alt));
  border: 3px solid var(--infuse-bg-primary);
  border-radius: 10px;
}
</style>
<!-- 小慧测试完成 -->
