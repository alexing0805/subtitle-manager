<template>
  <div class="dashboard">
    <!-- 欢迎区域 -->
    <header class="welcome-section">
      <h1 class="welcome-title">仪表盘</h1>
      <p class="welcome-subtitle">概览你的字幕管理状态</p>
    </header>

    <!-- 统计卡片 -->
    <div class="stats-grid">
      <div class="stat-card infuse-card">
        <div class="stat-icon" style="background: linear-gradient(135deg, #ff6b35 0%, #ff8555 100%);">
          <el-icon><Film /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.totalMovies }}</div>
          <div class="stat-label">电影</div>
          <div class="stat-sublabel">{{ stats.moviesWithSubtitle }} 有字幕 / {{ stats.moviesWithoutSubtitle }} 缺字幕</div>
        </div>
      </div>

      <div class="stat-card infuse-card">
        <div class="stat-icon" style="background: linear-gradient(135deg, #5856d6 0%, #af52de 100%);">
          <el-icon><VideoCamera /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.totalTVShows }}</div>
          <div class="stat-label">电视剧</div>
          <div class="stat-sublabel">{{ stats.totalEpisodes }} 集 / {{ stats.episodesWithSubtitle }} 有字幕</div>
        </div>
      </div>

      <div class="stat-card infuse-card">
        <div class="stat-icon" style="background: linear-gradient(135deg, #34c759 0%, #30d158 100%);">
          <el-icon><Check /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.totalWithSubtitle }}</div>
          <div class="stat-label">已有字幕</div>
          <div class="stat-sublabel">电影 + 剧集</div>
        </div>
      </div>

      <div class="stat-card infuse-card">
        <div class="stat-icon" style="background: linear-gradient(135deg, #ff9500 0%, #ffcc00 100%);">
          <el-icon><Warning /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.totalWithoutSubtitle }}</div>
          <div class="stat-label">缺少字幕</div>
          <div class="stat-sublabel">待处理</div>
        </div>
      </div>
    </div>

    <!-- 快捷操作 -->
    <div class="quick-actions">
      <h2 class="section-title">快捷操作</h2>
      <div class="actions-grid">
        <button class="action-card infuse-card" @click="handleScan">
          <div class="action-icon-wrapper" style="background: linear-gradient(135deg, #ff6b35 0%, #ff8555 100%);">
            <el-icon class="action-icon"><Search /></el-icon>
          </div>
          <span class="action-text">扫描库</span>
        </button>
        
        <button class="action-card infuse-card" @click="$router.push('/batch-upload')">
          <div class="action-icon-wrapper" style="background: linear-gradient(135deg, #5856d6 0%, #af52de 100%);">
            <el-icon class="action-icon"><Upload /></el-icon>
          </div>
          <span class="action-text">批量上传</span>
        </button>
        
        <button class="action-card infuse-card" @click="handleAutoDownload">
          <div class="action-icon-wrapper" style="background: linear-gradient(135deg, #34c759 0%, #30d158 100%);">
            <el-icon class="action-icon"><Download /></el-icon>
          </div>
          <span class="action-text">自动下载</span>
        </button>
        
        <button class="action-card infuse-card" @click="$router.push('/settings')">
          <div class="action-icon-wrapper" style="background: linear-gradient(135deg, #0071e3 0%, #42a5f5 100%);">
            <el-icon class="action-icon"><Setting /></el-icon>
          </div>
          <span class="action-text">设置</span>
        </button>
      </div>
    </div>

    <!-- 最近活动 -->
    <div class="recent-activity">
      <h2 class="section-title">最近活动</h2>
      <div class="activity-list infuse-card">
        <div v-if="activities.length === 0" class="empty-state">
          <el-icon class="empty-icon"><InfoFilled /></el-icon>
          <p>暂无活动记录</p>
        </div>
        <div 
          v-for="activity in activities" 
          :key="activity.id"
          class="activity-item"
        >
          <div class="activity-icon" :class="activity.type">
            <el-icon>
              <component :is="getActivityIcon(activity.type)" />
            </el-icon>
          </div>
          <div class="activity-content">
            <div class="activity-title">{{ activity.title }}</div>
            <div class="activity-time">{{ formatTime(activity.time) }}</div>
          </div>
          <el-tag :type="getActivityTagType(activity.status)" size="small" effect="dark">
            {{ activity.status }}
          </el-tag>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useSubtitleStore } from '../stores/subtitle'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Film, Check, Warning, Loading, Search, Upload, Download, Setting, InfoFilled, VideoCamera
} from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/zh-cn'

dayjs.extend(relativeTime)
dayjs.locale('zh-cn')

const store = useSubtitleStore()
const rawStats = ref({
  totalMovies: 0,
  moviesWithSubtitle: 0,
  moviesWithoutSubtitle: 0,
  totalTVShows: 0,
  totalEpisodes: 0,
  episodesWithSubtitle: 0,
  episodesWithoutSubtitle: 0,
  recentDownloads: 0,
  pendingTasks: 0
})
const activities = ref([])

// 计算总统计
const stats = computed(() => {
  const totalMovies = rawStats.value.totalMovies || 0
  const totalEpisodes = rawStats.value.totalEpisodes || 0
  const moviesWithSubtitle = rawStats.value.moviesWithSubtitle || 0
  const moviesWithoutSubtitle = rawStats.value.moviesWithoutSubtitle || 0
  const episodesWithSubtitle = rawStats.value.episodesWithSubtitle || 0
  const episodesWithoutSubtitle = rawStats.value.episodesWithoutSubtitle || 0
  
  return {
    // 电影统计
    totalMovies,
    moviesWithSubtitle,
    moviesWithoutSubtitle,
    // 电视剧统计
    totalTVShows: rawStats.value.totalTVShows || 0,
    totalEpisodes,
    episodesWithSubtitle,
    episodesWithoutSubtitle,
    // 总计
    totalWithSubtitle: moviesWithSubtitle + episodesWithSubtitle,
    totalWithoutSubtitle: moviesWithoutSubtitle + episodesWithoutSubtitle,
    // 其他
    recentDownloads: rawStats.value.recentDownloads || 0,
    pendingTasks: rawStats.value.pendingTasks || 0
  }
})

onMounted(async () => {
  try {
    const data = await store.fetchStats()
    rawStats.value = data
    // 这里可以从后端获取活动记录
    activities.value = []
  } catch (error) {
    ElMessage.error('获取统计信息失败')
  }
})

async function handleScan() {
  try {
    await ElMessageBox.confirm(
      '即将扫描所有媒体库文件，查找缺失的字幕。此操作可能需要较长时间，是否继续？',
      '确认全盘扫描',
      {
        confirmButtonText: '开始扫描',
        cancelButtonText: '取消',
        type: 'info',
        confirmButtonClass: 'infuse-btn-primary',
      }
    )
    ElMessage.info('开始扫描库...')
    await store.scanLibrary()
    ElMessage.success('扫描完成')
    const data = await store.fetchStats()
    rawStats.value = data
  } catch (error) {
    // 用户取消时不报错
    if (error !== 'cancel') {
      ElMessage.error('扫描失败')
    }
  }
}

async function handleAutoDownload() {
  try {
    ElMessage.info('开始自动下载字幕...')
    // 调用批量处理API
    ElMessage.success('任务已提交')
  } catch (error) {
    ElMessage.error('提交失败')
  }
}

function formatTime(time) {
  return dayjs(time).fromNow()
}

function getActivityIcon(type) {
  const icons = {
    scan: 'Search',
    download: 'Download',
    upload: 'Upload',
    process: 'Loading'
  }
  return icons[type] || 'InfoFilled'
}

function getActivityTagType(status) {
  const types = {
    success: 'success',
    failed: 'danger',
    processing: 'warning'
  }
  return types[status] || 'info'
}
</script>

<style scoped>
.dashboard {
  max-width: 1200px;
}

/* --- Entrance Animations --- */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.dashboard > * {
  animation: fadeInUp 0.6s cubic-bezier(0.22, 1, 0.36, 1) both;
}

.welcome-section { animation-delay: 0.1s; }
.stats-grid { animation-delay: 0.2s; }
.quick-actions { animation-delay: 0.3s; }
.recent-activity { animation-delay: 0.4s; }

/* 欢迎区域 */
.welcome-section {
  margin-bottom: 40px;
}

.welcome-title {
  font-size: 42px;
  font-weight: 800;
  color: var(--infuse-text-primary);
  margin-bottom: 8px;
  letter-spacing: -0.02em;
}

.welcome-subtitle {
  font-size: 18px;
  color: var(--infuse-text-secondary);
  font-weight: 400;
}

/* Infuse 卡片样式 */
.infuse-card {
  background: var(--infuse-bg-card);
  border-radius: var(--infuse-radius-lg);
  border: 1px solid var(--infuse-border);
  overflow: hidden;
  transition: all var(--infuse-transition-normal);
}

.infuse-card:hover {
  border-color: var(--infuse-border-hover);
  transform: translateY(-2px);
  box-shadow: var(--infuse-shadow-md);
}

/* 统计卡片 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 48px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 24px;
  background:
    linear-gradient(180deg, rgba(255,255,255,0.04), transparent 28%),
    rgba(10, 16, 38, 0.76);
  border: 1px solid rgba(119, 247, 255, 0.12);
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.04);
  position: relative;
  overflow: hidden;
}

.stat-card::after {
  content: "";
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle, rgba(255,255,255,0.03) 0%, transparent 70%);
  opacity: 0;
  transition: opacity 0.5s ease;
  pointer-events: none;
}

.stat-card:hover::after {
  opacity: 1;
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 24px;
  flex-shrink: 0;
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);
  transition: transform 0.3s ease;
}

.stat-card:hover .stat-icon {
  transform: scale(1.1) rotate(5deg);
}

.stat-value {
  font-size: 36px;
  font-weight: 800;
  line-height: 1;
  margin-bottom: 4px;
  background: linear-gradient(180deg, #fff 0%, rgba(255,255,255,0.7) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.stat-label {
  font-size: 14px;
  color: var(--infuse-text-secondary);
  font-weight: 500;
}

.stat-sublabel {
  font-size: 12px;
  color: var(--infuse-text-muted);
  margin-top: 4px;
}

/* 分区标题 */
.section-title {
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 20px;
  color: var(--infuse-text-primary);
  letter-spacing: -0.01em;
}

/* 快捷操作 */
.quick-actions {
  margin-bottom: 48px;
}

.actions-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.action-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 32px 24px;
  cursor: pointer;
  border: none;
  background:
    linear-gradient(180deg, rgba(255,255,255,0.04), transparent 28%),
    rgba(10, 16, 38, 0.76);
  border: 1px solid rgba(119, 247, 255, 0.12) !important;
  transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

.action-card:hover {
  background: rgba(15, 24, 52, 0.8) !important;
  border-color: var(--infuse-accent) !important;
  transform: translateY(-6px);
  box-shadow: var(--infuse-shadow-glow), var(--infuse-shadow-lg);
}

.action-icon-wrapper {
  width: 64px;
  height: 64px;
  border-radius: var(--infuse-radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 28px;
  transition: transform var(--infuse-transition-normal);
  box-shadow: 0 10px 20px rgba(0,0,0,0.3);
}

.action-card:hover .action-icon-wrapper {
  transform: scale(1.05);
}

.action-icon {
  font-size: 28px;
}

.action-text {
  font-size: 15px;
  font-weight: 600;
  color: var(--infuse-text-primary);
}

/* 最近活动 */
.recent-activity {
  margin-bottom: 48px;
}

.activity-list {
  position: relative;
  padding: 20px 0 !important;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: var(--infuse-text-muted);
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
  opacity: 0.5;
}

.activity-item {
  position: relative;
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 24px 16px 32px;
  border-bottom: none !important;
  transition: background var(--infuse-transition-fast);
}

.activity-item::before {
  content: "";
  position: absolute;
  left: 43px;
  top: 56px;
  bottom: -16px;
  width: 2px;
  background: linear-gradient(180deg, var(--infuse-border) 0%, transparent 100%);
  z-index: 0;
}

.activity-item:last-child::before {
  display: none;
}

.activity-item:hover {
  background: rgba(18, 29, 62, 0.88);
}

.activity-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 107, 53, 0.15);
  color: var(--infuse-accent);
  flex-shrink: 0;
  z-index: 1;
  box-shadow: 0 0 0 4px var(--infuse-bg-primary);
}

.activity-icon.download {
  background: rgba(52, 199, 89, 0.15);
  color: #34c759;
}

.activity-icon.upload {
  background: rgba(175, 82, 222, 0.15);
  color: #af52de;
}

.activity-content {
  flex: 1;
  background: rgba(255, 255, 255, 0.02);
  padding: 12px 16px;
  border-radius: var(--infuse-radius-md);
  border: 1px solid transparent;
  transition: all 0.3s ease;
}

.activity-item:hover .activity-content {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(255, 255, 255, 0.1);
  transform: translateX(4px);
}

.activity-title {
  font-size: 15px;
  font-weight: 500;
  color: var(--infuse-text-primary);
}

.activity-time {
  font-size: 13px;
  color: var(--infuse-text-muted);
  margin-top: 2px;
}

/* 响应式 */
@media (max-width: 1024px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .actions-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 640px) {
  .welcome-title {
    font-size: 32px;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .actions-grid {
    grid-template-columns: 1fr;
  }
}
</style>
