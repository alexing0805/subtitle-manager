<template>
  <div class="sidebar-shell" :class="{ open: mobileOpen }">
    <button class="sidebar-backdrop" @click="emit('close')" aria-label="关闭导航"></button>
    <aside class="sidebar" :class="{ open: mobileOpen }">
      <button class="sidebar-close" @click="emit('close')" aria-label="关闭导航">
        <el-icon><Close /></el-icon>
      </button>

      <div class="logo">
        <div class="logo-icon">
          <el-icon><VideoPlay /></el-icon>
        </div>
        <div class="logo-copy">
          <span class="logo-kicker">Neon Relay</span>
          <span class="logo-text">SubMate</span>
        </div>
      </div>

      <nav class="nav-menu">
        <router-link
          v-for="item in menuItems"
          :key="item.path"
          :to="item.path"
          class="nav-item"
          :class="{ active: route.path === item.path }"
          @click="emit('close')"
        >
          <div class="nav-icon-wrapper">
            <el-icon class="nav-icon">
              <component :is="item.icon" />
            </el-icon>
          </div>
          <span class="nav-text">{{ item.name }}</span>
          <div class="nav-glow" v-if="route.path === item.path"></div>
        </router-link>
      </nav>

      <div class="sidebar-footer">
        <div class="status-card" :class="{ online: isOnline }">
          <div class="status-indicator">
            <span class="status-dot"></span>
          </div>
          <div class="status-info">
            <span class="status-label">服务状态</span>
            <span class="status-text">{{ isOnline ? '运行正常' : '已停止' }}</span>
          </div>
        </div>
      </div>
    </aside>
  </div>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import {
  VideoPlay,
  DataLine,
  Film,
  Monitor,
  VideoCamera,
  Upload,
  Setting,
  Close
} from '@element-plus/icons-vue'

defineProps({
  mobileOpen: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close'])
const route = useRoute()
const isOnline = ref(true)

const menuItems = [
  { path: '/', name: '仪表盘', icon: DataLine },
  { path: '/movies', name: '电影', icon: Film },
  { path: '/tvshows', name: '电视剧', icon: Monitor },
  { path: '/anime', name: '动漫', icon: VideoCamera },
  { path: '/batch-upload', name: '批量上传', icon: Upload },
  { path: '/settings', name: '设置', icon: Setting },
]

onMounted(async () => {
  try {
    const response = await fetch('/api/status')
    isOnline.value = response.ok
  } catch {
    isOnline.value = false
  }
})

watch(() => route.fullPath, () => {
  emit('close')
})
</script>

<style scoped>
.sidebar-shell {
  display: contents;
}

.sidebar-backdrop,
.sidebar-close {
  display: none;
}

.sidebar {
  position: fixed;
  left: 0;
  top: 0;
  width: 280px;
  height: 100vh;
  background:
    linear-gradient(180deg, rgba(255,255,255,0.04), transparent 18%),
    rgba(7, 12, 29, 0.88);
  border-right: 1px solid var(--infuse-border);
  display: flex;
  flex-direction: column;
  padding: 32px 24px;
  z-index: 100;
  backdrop-filter: blur(26px);
  box-shadow: 20px 0 50px rgba(0, 0, 0, 0.22);
}

.logo {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 0 8px;
  margin-bottom: 48px;
}

.logo-icon {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, var(--infuse-accent) 0%, var(--infuse-accent-alt) 100%);
  border-radius: var(--infuse-radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #04111c;
  font-size: 24px;
  box-shadow: 0 0 0 1px rgba(119, 247, 255, 0.22), 0 0 24px rgba(34, 246, 255, 0.24);
}

.logo-copy {
  display: flex;
  flex-direction: column;
}

.logo-kicker {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.18em;
  color: var(--infuse-text-muted);
}

.logo-text {
  font-size: 28px;
  font-weight: 800;
  background: linear-gradient(135deg, #f7fbff 0%, #77f7ff 40%, #ff8be9 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.nav-menu {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 20px;
  border-radius: var(--infuse-radius-md);
  color: var(--infuse-text-secondary);
  text-decoration: none;
  transition: all var(--infuse-transition-normal);
  position: relative;
  overflow: hidden;
  border: 1px solid transparent;
}

.nav-item:hover {
  background: rgba(13, 22, 50, 0.92);
  color: var(--infuse-text-primary);
  border-color: rgba(119, 247, 255, 0.12);
}

.nav-item.active {
  background: linear-gradient(135deg, rgba(34, 246, 255, 0.14), rgba(255, 43, 214, 0.12));
  color: var(--infuse-accent);
  border-color: rgba(119, 247, 255, 0.24);
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.04), 0 0 18px rgba(34, 246, 255, 0.08);
}

.nav-icon-wrapper {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--infuse-radius-sm);
  transition: all var(--infuse-transition-normal);
}

.nav-item:hover .nav-icon-wrapper {
  background: var(--infuse-bg-hover);
}

.nav-item.active .nav-icon-wrapper {
  background: rgba(34, 246, 255, 0.14);
  box-shadow: inset 0 0 0 1px rgba(119, 247, 255, 0.12);
}

.nav-icon {
  font-size: 20px;
}

.nav-text {
  font-size: 15px;
  font-weight: 700;
}

.nav-glow {
  position: absolute;
  right: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 24px;
  background: var(--infuse-accent);
  border-radius: 2px 0 0 2px;
  box-shadow: 0 0 14px var(--infuse-accent), 0 0 28px rgba(34, 246, 255, 0.22);
}

.sidebar-footer {
  margin-top: auto;
  padding-top: 24px;
  border-top: 1px solid var(--infuse-border);
}

.status-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  background: rgba(12, 20, 48, 0.82);
  border-radius: var(--infuse-radius-md);
  border: 1px solid var(--infuse-border);
  transition: all var(--infuse-transition-normal);
  backdrop-filter: blur(18px);
}

.status-card.online {
  border-color: rgba(34, 197, 94, 0.3);
  background: rgba(34, 197, 94, 0.1);
}

.status-indicator {
  position: relative;
}

.status-dot {
  display: block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #ef4444;
  position: relative;
}

.status-card.online .status-dot {
  background: #22c55e;
}

.status-card.online .status-dot::after {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: rgba(34, 197, 94, 0.3);
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% {
    transform: translate(-50%, -50%) scale(1);
    opacity: 1;
  }
  100% {
    transform: translate(-50%, -50%) scale(1.5);
    opacity: 0;
  }
}

.status-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.status-label {
  font-size: 12px;
  color: var(--infuse-text-muted);
  font-weight: 500;
}

.status-text {
  font-size: 14px;
  color: var(--infuse-text-secondary);
  font-weight: 600;
}

.status-card.online .status-text {
  color: #22c55e;
}

@media (max-width: 768px) {
  .sidebar-shell {
    display: block;
  }

  .sidebar-backdrop {
    position: fixed;
    inset: 0;
    border: none;
    background: rgba(0, 0, 0, 0.48);
    opacity: 0;
    pointer-events: none;
    transition: opacity var(--infuse-transition-normal);
    z-index: 280;
  }

  .sidebar {
    width: min(82vw, 320px);
    padding: 24px 18px;
    transform: translateX(-100%);
    transition: transform var(--infuse-transition-normal);
    z-index: 300;
  }

  .sidebar.open {
    transform: translateX(0);
  }

  .sidebar-shell.open .sidebar-backdrop {
    opacity: 1;
    pointer-events: auto;
  }

  .sidebar-close {
    position: absolute;
    top: 16px;
    right: 16px;
    width: 36px;
    height: 36px;
    border-radius: 12px;
    border: 1px solid var(--infuse-border);
    background: var(--infuse-bg-card);
    color: var(--infuse-text-primary);
    display: inline-flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
  }

  .logo {
    margin-bottom: 32px;
    padding-right: 48px;
  }

  .logo-text {
    font-size: 24px;
  }

  .nav-item {
    padding: 14px 16px;
  }

  .status-card {
    padding: 14px 16px;
  }
}
</style>
