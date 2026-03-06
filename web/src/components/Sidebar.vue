<template>
  <aside class="sidebar">
    <div class="logo">
      <el-icon class="logo-icon"><VideoPlay /></el-icon>
      <span class="logo-text">Subtitle Manager</span>
    </div>
    
    <nav class="nav-menu">
      <router-link 
        v-for="item in menuItems" 
        :key="item.path"
        :to="item.path"
        class="nav-item"
        :class="{ active: $route.path === item.path }"
      >
        <el-icon class="nav-icon">
          <component :is="item.icon" />
        </el-icon>
        <span class="nav-text">{{ item.name }}</span>
      </router-link>
    </nav>
    
    <div class="sidebar-footer">
      <div class="status-indicator" :class="{ online: isOnline }">
        <span class="status-dot"></span>
        <span class="status-text">{{ isOnline ? '运行中' : '已停止' }}</span>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { 
  VideoPlay, 
  DataLine, 
  Film, 
  Monitor, 
  Upload, 
  Setting 
} from '@element-plus/icons-vue'

const isOnline = ref(true)

const menuItems = [
  { path: '/', name: '仪表盘', icon: 'DataLine' },
  { path: '/movies', name: '电影', icon: 'Film' },
  { path: '/tvshows', name: '电视剧', icon: 'Monitor' },
  { path: '/batch-upload', name: '批量上传', icon: 'Upload' },
  { path: '/settings', name: '设置', icon: 'Setting' },
]

onMounted(async () => {
  // 检查服务状态
  try {
    const response = await fetch('/api/status')
    isOnline.value = response.ok
  } catch {
    isOnline.value = false
  }
})
</script>

<style scoped>
.sidebar {
  position: fixed;
  left: 0;
  top: 0;
  width: 260px;
  height: 100vh;
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(20px);
  border-right: 1px solid rgba(0, 0, 0, 0.08);
  display: flex;
  flex-direction: column;
  padding: 24px 16px;
  z-index: 100;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 12px;
  margin-bottom: 32px;
}

.logo-icon {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #0071e3 0%, #42a5f5 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 20px;
}

.logo-text {
  font-size: 18px;
  font-weight: 600;
  color: #1d1d1f;
  letter-spacing: -0.01em;
}

.nav-menu {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 12px;
  color: #86868b;
  text-decoration: none;
  transition: all 0.2s ease;
  font-size: 15px;
  font-weight: 500;
}

.nav-item:hover {
  background: rgba(0, 0, 0, 0.04);
  color: #1d1d1f;
}

.nav-item.active {
  background: #0071e3;
  color: white;
}

.nav-icon {
  font-size: 20px;
}

.sidebar-footer {
  padding: 16px;
  border-top: 1px solid rgba(0, 0, 0, 0.06);
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #86868b;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #ff3b30;
  transition: background 0.3s ease;
}

.status-indicator.online .status-dot {
  background: #34c759;
}

@media (max-width: 768px) {
  .sidebar {
    transform: translateX(-100%);
    transition: transform 0.3s ease;
  }
  
  .sidebar.open {
    transform: translateX(0);
  }
}
</style>
