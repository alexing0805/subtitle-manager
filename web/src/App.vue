<template>
  <div class="app">
    <Sidebar />
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import Sidebar from './components/Sidebar.vue'
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: #f5f5f7;
  color: #1d1d1f;
  -webkit-font-smoothing: antialiased;
}

.app {
  display: flex;
  min-height: 100vh;
}

.main-content {
  flex: 1;
  margin-left: 260px;
  padding: 40px;
  min-height: 100vh;
}

/* Apple Design System */
.apple-card {
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.3);
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.04);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.apple-card:hover {
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
  transform: translateY(-2px);
}

.apple-button {
  background: #0071e3;
  color: white;
  border: none;
  border-radius: 980px;
  padding: 12px 24px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.apple-button:hover {
  background: #0077ed;
  transform: scale(1.02);
}

.apple-button:active {
  transform: scale(0.98);
}

.apple-button.secondary {
  background: rgba(0, 0, 0, 0.05);
  color: #1d1d1f;
}

.apple-button.secondary:hover {
  background: rgba(0, 0, 0, 0.1);
}

.page-title {
  font-size: 32px;
  font-weight: 700;
  margin-bottom: 8px;
  letter-spacing: -0.015em;
}

.page-subtitle {
  font-size: 16px;
  color: #86868b;
  margin-bottom: 32px;
}

/* Element Plus 苹果风格覆盖 */
.el-table {
  background: transparent !important;
  --el-table-border-color: rgba(0, 0, 0, 0.05);
  --el-table-header-bg-color: transparent;
  --el-table-row-hover-bg-color: rgba(0, 113, 227, 0.04);
}

.el-table th {
  font-weight: 600;
  color: #1d1d1f;
}

.el-tag {
  border-radius: 6px;
  font-weight: 500;
}

.el-progress-bar__outer {
  border-radius: 4px;
  background: rgba(0, 0, 0, 0.05);
}

.el-progress-bar__inner {
  border-radius: 4px;
}

@media (max-width: 768px) {
  .main-content {
    margin-left: 0;
    padding: 20px;
  }
}
</style>
