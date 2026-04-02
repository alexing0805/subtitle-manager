<template>
  <div class="dashboard page-shell" ref="dashboardRef" @mousemove="handleMouseMove" @mouseleave="handleMouseLeave">
    <!-- 背景粒子效果 -->
    <div class="bg-particles">
      <div
        v-for="particle in particles"
        :key="particle.id"
        class="particle"
        :style="particle.style"
      ></div>
    </div>

    <!-- 欢迎区域 -->
    <header class="welcome-section" :style="parallaxStyle">
      <h1 class="welcome-title">仪表盘</h1>
      <p class="welcome-subtitle">概览你的字幕管理状态</p>
    </header>

    <!-- 统计卡片 -->
    <div class="stats-grid">
      <!-- 电影卡片 -->
      <div
        class="stat-card infuse-card infuse-tilt"
        @click="$router.push('/movies')"
        @mousemove="handleTiltMove"
        @mouseleave="handleTiltLeave"
      >
        <div class="card-glow movies-glow"></div>
        <div class="stat-icon" style="background: linear-gradient(135deg, #22f6ff 0%, #00d2ff 100%);">
          <el-icon><Film /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.totalMovies }}</div>
          <div class="stat-label">电影</div>
          <div class="stat-sublabel">
            <span class="highlight-cyan">{{ stats.moviesWithSubtitle }}</span> 有字幕 /
            <span class="highlight-muted">{{ stats.moviesWithoutSubtitle }}</span> 缺字幕
          </div>
        </div>
        <div class="card-arrow">
          <el-icon><ArrowRight /></el-icon>
        </div>
      </div>

      <!-- 电视剧卡片 -->
      <div
        class="stat-card infuse-card infuse-tilt"
        @click="$router.push('/tvshows')"
        @mousemove="handleTiltMove"
        @mouseleave="handleTiltLeave"
      >
        <div class="card-glow tv-glow"></div>
        <div class="stat-icon" style="background: linear-gradient(135deg, #ff2bd6 0%, #d400ff 100%);">
          <el-icon><VideoCamera /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.totalTVShows }}</div>
          <div class="stat-label">电视剧</div>
          <div class="stat-sublabel">
            <span class="highlight-magenta">{{ stats.totalEpisodes }}</span> 集 /
            <span class="highlight-cyan">{{ stats.episodesWithSubtitle }}</span> 有字幕
          </div>
        </div>
        <div class="card-arrow">
          <el-icon><ArrowRight /></el-icon>
        </div>
      </div>

      <!-- 动漫卡片 -->
      <div
        class="stat-card infuse-card infuse-tilt"
        @click="$router.push('/anime')"
        @mousemove="handleTiltMove"
        @mouseleave="handleTiltLeave"
      >
        <div class="card-glow anime-glow"></div>
        <div class="stat-icon" style="background: linear-gradient(135deg, #00f2fe 0%, #4facfe 100%);">
          <el-icon><Grid /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.totalAnime }}</div>
          <div class="stat-label">动漫</div>
          <div class="stat-sublabel">
            <span class="highlight-cyan">{{ stats.animeWithSubtitle }}</span> 有字幕 /
            <span class="highlight-muted">{{ stats.animeWithoutSubtitle }}</span> 缺字幕
          </div>
        </div>
        <div class="card-arrow">
          <el-icon><ArrowRight /></el-icon>
        </div>
      </div>

      <!-- 总览卡片 -->
      <div
        class="stat-card total-card infuse-card infuse-tilt"
        @mousemove="handleTiltMove"
        @mouseleave="handleTiltLeave"
      >
        <div class="card-glow total-glow"></div>
        <div class="stat-icon" style="background: linear-gradient(135deg, #34c759 0%, #30d158 100%);">
          <el-icon><Check /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value-row">
            <div class="stat-mini">
              <span class="mini-value cyan">{{ stats.totalWithSubtitle }}</span>
              <span class="mini-label">已有字幕</span>
            </div>
            <div class="stat-divider"></div>
            <div class="stat-mini">
              <span class="mini-value magenta">{{ stats.totalWithoutSubtitle }}</span>
              <span class="mini-label">缺少字幕</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 快捷操作 -->
    <div class="quick-actions">
      <h2 class="section-title">快捷操作</h2>
      <div class="actions-grid">
        <button class="action-card infuse-card infuse-tilt infuse-ripple-target" @click="triggerRipple($event); handleScan()" @mousemove="handleTiltMove" @mouseleave="handleTiltLeave">
          <div class="card-glow scan-glow"></div>
          <div class="action-icon-wrapper scan-icon-bg">
            <el-icon class="action-icon"><Refresh /></el-icon>
          </div>
          <span class="action-text">扫描库</span>
        </button>

        <button class="action-card infuse-card infuse-tilt infuse-ripple-target" @click="triggerRipple($event); $router.push('/batch-upload')" @mousemove="handleTiltMove" @mouseleave="handleTiltLeave">
          <div class="card-glow upload-glow"></div>
          <div class="action-icon-wrapper upload-icon-bg">
            <el-icon class="action-icon"><Upload /></el-icon>
          </div>
          <span class="action-text">批量上传</span>
        </button>

        <button class="action-card infuse-card infuse-tilt infuse-ripple-target" @click="triggerRipple($event); handleAutoDownload()" @mousemove="handleTiltMove" @mouseleave="handleTiltLeave">
          <div class="card-glow download-glow"></div>
          <div class="action-icon-wrapper download-icon-bg">
            <el-icon class="action-icon"><Download /></el-icon>
          </div>
          <span class="action-text">自动下载</span>
        </button>

        <button class="action-card infuse-card infuse-tilt infuse-ripple-target" @click="triggerRipple($event); $router.push('/settings')" @mousemove="handleTiltMove" @mouseleave="handleTiltLeave">
          <div class="card-glow settings-glow"></div>
          <div class="action-icon-wrapper settings-icon-bg">
            <el-icon class="action-icon"><Setting /></el-icon>
          </div>
          <span class="action-text">设置</span>
        </button>
      </div>
    </div>

    <!-- 最近活动 -->
    <div class="recent-activity">
      <h2 class="section-title">最近活动</h2>
      <div class="activity-list infuse-card" v-loading="loadingActivities">
        <div v-if="!loadingActivities && activities.length === 0" class="empty-state">
          <div class="empty-illustration">
            <el-icon class="empty-icon"><Clock /></el-icon>
          </div>
          <p>暂无活动记录</p>
          <span class="empty-hint">开始扫描或下载字幕后,这里将显示活动日志</span>
        </div>
        <TransitionGroup name="activity" tag="div" class="activity-inner" v-else>
          <div
            v-for="(activity, index) in activities"
            :key="activity.id"
            class="activity-item"
            :style="{ animationDelay: `${index * 0.1}s` }"
          >
            <div class="activity-timeline">
              <div class="timeline-dot" :class="activity.type"></div>
              <div class="timeline-line" v-if="index < activities.length - 1"></div>
            </div>
            <div class="activity-icon" :class="activity.type">
              <el-icon>
                <component :is="getActivityIcon(activity.type)" />
              </el-icon>
            </div>
            <div class="activity-content">
              <div class="activity-title">{{ activity.title }}</div>
              <div class="activity-meta">
                <span class="activity-time">{{ formatTime(activity.time) }}</span>
                <span class="activity-time-absolute">{{ formatAbsoluteTime(activity.time) }}</span>
                <span class="activity-source" v-if="activity.source">{{ activity.source }}</span>
              </div>
            </div>
            <el-tag :type="getActivityTagType(activity.status)" size="small" effect="dark" class="activity-tag">
              {{ getStatusText(activity.status) }}
            </el-tag>
          </div>
        </TransitionGroup>
      </div>
    </div>
    
    <ScanVisualization
      v-model:visible="scanVisualizationVisible"
      title="全盘扫描可视化"
      :status="store.scanStatus"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, computed, onBeforeUnmount } from 'vue'
import { useSubtitleStore } from '../stores/subtitle'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Film, Check, Warning, Loading, Refresh, Upload, Download, Setting, InfoFilled,
  VideoCamera, ArrowRight, Grid, Clock
} from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/zh-cn'
import { useAmbientEffects } from '../composables/useAmbientEffects'
import { buildScanConfirmHtml, createScanDialogOptions } from '../utils/scanDialog'
import api from '../utils/api'
import ScanVisualization from '../components/ScanVisualization.vue'

dayjs.extend(relativeTime)
dayjs.locale('zh-cn')

const store = useSubtitleStore()

// Refs
const {
  containerRef: dashboardRef,
  particles,
  parallaxStyle,
  handleMouseMove,
  handleMouseLeave,
  handleTiltMove,
  handleTiltLeave,
  triggerRipple
} = useAmbientEffects({ particleCount: 30, parallaxFactor: 0.01 })

// State
const rawStats = ref({
  totalMovies: 0,
  moviesWithSubtitle: 0,
  moviesWithoutSubtitle: 0,
  totalTVShows: 0,
  totalEpisodes: 0,
  episodesWithSubtitle: 0,
  episodesWithoutSubtitle: 0,
  totalAnime: 0,
  animeWithSubtitle: 0,
  animeWithoutSubtitle: 0,
  recentDownloads: 0,
  pendingTasks: 0
})

const activities = ref([])
const loadingActivities = ref(false)
// Computed
const stats = computed(() => {
  const totalWithSubtitle = rawStats.value.moviesWithSubtitle + rawStats.value.episodesWithSubtitle + rawStats.value.animeWithSubtitle
  const totalWithoutSubtitle = rawStats.value.moviesWithoutSubtitle + rawStats.value.episodesWithoutSubtitle + rawStats.value.animeWithoutSubtitle

  return {
    ...rawStats.value,
    totalWithSubtitle,
    totalWithoutSubtitle
  }
})

// Fetch data
onMounted(async () => {
  try {
    // Fetch stats
    const data = await store.fetchStats()
    rawStats.value = data

    // Fetch recent activities
    await fetchActivities()
  } catch (error) {
    ElMessage.error('获取统计信息失败')
  }
})

onBeforeUnmount(() => {
  stopScanPolling()
})

const scanVisualizationVisible = ref(false)
let scanPollTimer = null

function stopScanPolling() {
  if (scanPollTimer) {
    clearInterval(scanPollTimer)
    scanPollTimer = null
  }
}

async function startScanPolling(onComplete) {
  stopScanPolling()
  const syncStatus = async () => {
    const status = await store.fetchScanStatus()
    scanVisualizationVisible.value = true
    if (!status.isScanning && status.phase === 'complete') {
      stopScanPolling()
      if (typeof onComplete === 'function') {
        await onComplete()
      }
    }
  }
  await syncStatus()
  scanPollTimer = setInterval(() => {
    syncStatus().catch(() => {})
  }, 800)
}

async function fetchActivities() {
  loadingActivities.value = true
  try {
    const response = await api.get('/recent-activity', {
      params: { limit: 10 }
    })
    const activityItems = Array.isArray(response.data)
      ? response.data
      : Array.isArray(response.data?.activities)
        ? response.data.activities
        : []

    activities.value = activityItems
      .filter(activity => activity && (activity.id || activity.title || activity.time))
      .map((activity, index) => ({
        id: activity.id || `activity-${index}-${activity.time || Date.now()}`,
        type: activity.type || 'process',
        title: activity.title || '未命名活动',
        status: activity.status || 'processing',
        time: activity.time || new Date().toISOString(),
        source: activity.source || ''
      }))
  } catch (error) {
    console.error('获取活动记录失败:', error)
    // 静默失败,使用空数组
    activities.value = []
  } finally {
    loadingActivities.value = false
  }
}

async function handleScan() {
  try {
    await ElMessageBox.confirm(
      buildScanConfirmHtml({
        title: '确认全盘扫描',
        description: '系统将深度扫描所有媒体库目录，自动关联缺失字幕并刷新统计面板。',
        steps: ['检索文件变动', '匹配 TMDB 元数据', '更新本地数据库']
      }),
      '',
      { ...createScanDialogOptions('扫描任务已提交...'), confirmButtonText: '开启深度扫描', cancelButtonText: '暂不执行' }
    )

    ElMessage.info({ message: '扫描进程已在后台启动...', customClass: 'infuse-message' })
    const result = await store.scanLibrary()
    if (result && result.success === false) {
      throw new Error(result.message || '服务器内部扫描任务调度失败')
    }

    scanVisualizationVisible.value = true
    startScanPolling(async () => {
      const data = await store.fetchStats()
      rawStats.value = data
      await fetchActivities()
      ElMessage.success({
        message: '媒体库扫描同步完成, 数据已更新',
        customClass: 'infuse-message'
      })
    })

  } catch (error) {
    if (error === 'cancel' || error === 'close' || error === '') return
    
    console.error('Scan Error:', error)
    ElMessageBox.alert(
      `<div class="error-msg-content">
        <p>扫描过程遇到异常中止:</p>
        <div class="error-detail">${error.message || '网络连接超时或远程服务未响应'}</div>
        <p class="error-hint">请检查媒体目录权限或重试</p>
      </div>`,
      '扫描异常',
      {
        confirmButtonText: '知道了',
        type: 'error',
        dangerouslyUseHTMLString: true,
        customClass: 'infuse-message-box error-modal'
      }
    )
  }
}

async function handleAutoDownload() {
  try {
    ElMessage.info('开始自动下载字幕...')
    ElMessage.success('功能开发中...')
  } catch (error) {
    ElMessage.error('提交失败')
  }
}

function formatTime(time) {
  return dayjs(time).fromNow()
}

function formatAbsoluteTime(time) {
  return dayjs(time).format('YYYY-MM-DD HH:mm:ss')
}

function getActivityIcon(type) {
  const icons = {
    scan: Refresh,
    download: Download,
    upload: Upload,
    process: Loading
  }
  return icons[type] || InfoFilled
}

function getActivityTagType(status) {
  const types = {
    success: 'success',
    failed: 'danger',
    processing: 'warning',
    completed: 'success'
  }
  return types[status] || 'info'
}

function getStatusText(status) {
  const texts = {
    success: '成功',
    failed: '失败',
    processing: '处理中',
    completed: '完成'
  }
  return texts[status] || status
}
</script>

<style scoped>
.dashboard {
  max-width: 1200px;
  position: relative;
  overflow: hidden;
  padding: 12px 20px;
}

/* 背景粒子效果 */
.bg-particles {
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  overflow: hidden;
}

.particle {
  position: absolute;
  background: var(--infuse-accent);
  border-radius: 50%;
  animation: float-particle linear infinite;
}

@keyframes float-particle {
  0% {
    transform: translateY(0) scale(1);
    opacity: 0;
  }
  10% {
    opacity: 1;
  }
  90% {
    opacity: 1;
  }
  100% {
    transform: translateY(-100vh) scale(0.5);
    opacity: 0;
  }
}

/* 入场动画 */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px) scale(0.98);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.dashboard > * {
  position: relative;
  z-index: 2;
  animation: fadeInUp 0.8s cubic-bezier(0.16, 1, 0.3, 1) both;
}

.welcome-section { animation-delay: 0.1s; }
.stats-grid { animation-delay: 0.2s; }
.quick-actions { animation-delay: 0.3s; }
.recent-activity { animation-delay: 0.4s; }

/* 欢迎区域 */
.welcome-section {
  margin-bottom: 32px;
  padding-left: 10px;
}

.welcome-title {
  font-size: 56px;
  font-weight: 900;
  background: linear-gradient(135deg, #fff 0%, #77f7ff 42%, #ff8be9 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin-bottom: 12px;
  letter-spacing: -0.04em;
  filter: drop-shadow(0 0 20px rgba(34, 246, 255, 0.3));
}

.welcome-subtitle {
  font-size: 20px;
  color: var(--infuse-text-secondary);
  font-weight: 400;
  opacity: 0.85;
}

/* Infuse 卡片增强 - 深度玻璃拟态 */
.infuse-card {
  background: rgba(15, 23, 42, 0.4);
  border-radius: 24px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(20px) saturate(180%);
  overflow: hidden;
  transition: all 0.5s cubic-bezier(0.23, 1, 0.32, 1);
  box-shadow: 
    0 4px 24px -1px rgba(0, 0, 0, 0.2),
    inset 0 0 0 1px rgba(255, 255, 255, 0.05);
  position: relative;
}

.infuse-card:hover {
  background: rgba(15, 23, 42, 0.5);
  border-color: rgba(34, 246, 255, 0.3);
  box-shadow: 
    0 20px 40px -12px rgba(0, 0, 0, 0.4),
    0 0 20px rgba(34, 246, 255, 0.1);
}

/* 动态光晕层 */
.card-glow {
  position: absolute;
  inset: 0;
  opacity: 0;
  transition: opacity 0.6s ease;
  pointer-events: none;
  z-index: 0;
}

.infuse-card:hover .card-glow {
  opacity: 1;
}

.movies-glow { background: radial-gradient(circle at top right, rgba(34, 246, 255, 0.15), transparent 60%); }
.tv-glow { background: radial-gradient(circle at top right, rgba(255, 43, 214, 0.15), transparent 60%); }
.anime-glow { background: radial-gradient(circle at top right, rgba(0, 242, 254, 0.15), transparent 60%); }
.total-glow { background: radial-gradient(circle at top right, rgba(52, 199, 89, 0.15), transparent 60%); }

.scan-glow { background: radial-gradient(circle at center, rgba(34, 246, 255, 0.12), transparent 70%); }
.upload-glow { background: radial-gradient(circle at center, rgba(255, 43, 214, 0.12), transparent 70%); }
.download-glow { background: radial-gradient(circle at center, rgba(52, 199, 89, 0.12), transparent 70%); }
.settings-glow { background: radial-gradient(circle at center, rgba(66, 165, 245, 0.12), transparent 70%); }

/* 统计卡片 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 48px;
}

.stat-card {
  padding: 24px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 18px;
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
  transition: all 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  position: relative;
  z-index: 1;
}

.stat-card:hover .stat-icon {
  transform: scale(1.15) rotate(-5deg);
  box-shadow: 0 12px 24px rgba(34, 246, 255, 0.3);
}

.stat-content {
  flex: 1;
  min-width: 0;
  position: relative;
  z-index: 1;
}

.stat-value {
  font-size: 32px;
  font-weight: 800;
  line-height: 1.1;
  margin-bottom: 4px;
  background: linear-gradient(to bottom, #fff, #cbd5e1);
  background-size: 200% auto;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  letter-spacing: -0.02em;
  transition: background-position 0.5s ease;
}

.stat-card:hover .stat-value {
  background-position: center bottom;
  filter: drop-shadow(0 0 8px rgba(255, 255, 255, 0.4));
}

.stat-label {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.5);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 2px;
}

.stat-sublabel {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.35);
}

.highlight-cyan { color: #22f6ff; font-weight: 600; }
.highlight-magenta { color: #ff2bd6; font-weight: 600; }
.highlight-muted { color: rgba(255, 255, 255, 0.5); }

.card-arrow {
  position: absolute;
  right: 16px;
  top: 50%;
  transform: translateY(-50%) translateX(-10px);
  opacity: 0;
  color: #22f6ff;
  transition: all 0.3s ease;
}

.stat-card:hover .card-arrow {
  opacity: 1;
  transform: translateY(-50%) translateX(0);
}

/* 总览卡片 */
.stat-value-row {
  display: flex;
  align-items: center;
  justify-content: space-around;
  width: 100%;
}

.stat-mini {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.mini-value {
  font-size: 24px;
  font-weight: 800;
}

.mini-value.cyan {
  background: linear-gradient(135deg, #22f6ff, #00d2ff);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.mini-value.magenta {
  background: linear-gradient(135deg, #ff2bd6, #d400ff);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.mini-label {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.3);
  margin-top: 4px;
}

.stat-divider {
  width: 1px;
  height: 32px;
  background: rgba(255, 255, 255, 0.1);
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
  padding: 28px 20px;
  cursor: pointer;
  background: rgba(15, 23, 42, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
}

.action-icon-wrapper {
  width: 60px;
  height: 60px;
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 28px;
  transition: all 0.5s cubic-bezier(0.23, 1, 0.32, 1);
  position: relative;
  z-index: 1;
}

.scan-icon-bg { background: linear-gradient(135deg, #22f6ff 0%, #0099ff 100%); box-shadow: 0 10px 20px rgba(34, 246, 255, 0.2); }
.upload-icon-bg { background: linear-gradient(135deg, #ff2bd6 0%, #a200ff 100%); box-shadow: 0 10px 20px rgba(255, 43, 214, 0.2); }
.download-icon-bg { background: linear-gradient(135deg, #34c759 0%, #15803d 100%); box-shadow: 0 10px 20px rgba(52, 199, 89, 0.2); }
.settings-icon-bg { background: linear-gradient(135deg, #0ea5e9 0%, #2563eb 100%); box-shadow: 0 10px 20px rgba(14, 165, 233, 0.2); }

.action-card:hover .action-icon-wrapper {
  transform: translateY(-8px) scale(1.12) rotate(5deg);
  filter: brightness(1.2);
}

.action-text {
  font-size: 15px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.9);
  letter-spacing: 0.02em;
  position: relative;
  z-index: 1;
  transition: color 0.3s ease;
}

.action-card:hover .action-text {
  color: #fff;
  text-shadow: 0 0 10px rgba(255, 255, 255, 0.4);
}

.action-ripple {
  position: absolute;
  width: 0;
  height: 0;
  background: rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  transform: translate(-50%, -50%);
  pointer-events: none;
  opacity: 0;
}

.action-ripple.active {
  animation: ripple-effect 0.6s ease-out forwards;
}

@keyframes ripple-effect {
  0% {
    width: 0;
    height: 0;
    opacity: 0.5;
  }
  100% {
    width: 300px;
    height: 300px;
    opacity: 0;
  }
}

/* 扫描按钮脉冲效果 */
.actions-grid .action-card:first-child:hover .action-icon-wrapper {
  animation: pulse-glow 2s ease-in-out infinite;
}

@keyframes pulse-glow {
  0%, 100% { box-shadow: 0 10px 20px rgba(34, 246, 255, 0.2); }
  50% { box-shadow: 0 10px 30px rgba(34, 246, 255, 0.5), 0 0 20px rgba(34, 246, 255, 0.3); }
}

/* 最近活动 */
.recent-activity {
  margin-bottom: 48px;
}

.activity-list {
  position: relative;
  padding: 0 !important;
  overflow: hidden;
}

.activity-inner {
  padding: 20px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  color: var(--infuse-text-muted);
}

.empty-illustration {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--infuse-bg-tertiary), var(--infuse-bg-hover));
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 20px;
}

.empty-icon {
  font-size: 48px;
  opacity: 0.5;
}

.empty-hint {
  font-size: 13px;
  color: var(--infuse-text-muted);
  margin-top: 8px;
  opacity: 0.7;
}

/* 活动项动画 */
.activity-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  margin-bottom: 8px;
  border-radius: var(--infuse-radius-md);
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid transparent;
  transition: all 0.3s;
  animation: slideIn 0.4s cubic-bezier(0.22, 1, 0.36, 1) both;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateX(-20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.activity-item:hover {
  background: rgba(255, 255, 255, 0.05);
  border-color: var(--infuse-border);
  transform: translateX(4px);
}

.activity-timeline {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-right: 8px;
}

.timeline-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: var(--infuse-accent);
  box-shadow: 0 0 10px var(--infuse-accent);
}

.timeline-dot.scan { background: #ff6b35; box-shadow: 0 0 10px #ff6b35; }
.timeline-dot.download { background: #34c759; box-shadow: 0 0 10px #34c759; }
.timeline-dot.upload { background: #5856d6; box-shadow: 0 0 10px #5856d6; }

.timeline-line {
  width: 2px;
  flex: 1;
  min-height:  20px;
  background: linear-gradient(180deg, var(--infuse-border) 0%, transparent 100%);
}

.activity-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 107, 53, 0.15);
  color: var(--infuse-accent);
  flex-shrink: 0;
  transition: transform 0.3s;
}

.activity-icon.scan { background: rgba(255, 107, 53, 0.15); color: #ff6b35; }
.activity-icon.download { background: rgba(52, 199, 89, 0.15); color: #34c759; }
.activity-icon.upload { background: rgba(88, 86, 214, 0.15); color: #5856d6; }

.activity-item:hover .activity-icon {
  transform: scale(1.1) rotate(5deg);
}

.activity-content {
  flex: 1;
  min-width: 0;
}

.activity-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--infuse-text-primary);
  margin-bottom: 4px;
}

.activity-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: var(--infuse-text-muted);
}

.activity-time-absolute {
  opacity: 0.85;
}

.activity-source {
  padding: 2px 8px;
  background: var(--infuse-bg-tertiary);
  border-radius: 4px;
}

.activity-tag {
  flex-shrink: 0;
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

/* 扫描确认对话框全局美化 */
:deep(.infuse-message-box) {
  background: rgba(10, 16, 38, 0.9) !important;
  backdrop-filter: blur(40px) saturate(150%) !important;
  border: 1px solid rgba(119, 247, 255, 0.2) !important;
  border-radius: 28px !important;
  box-shadow: 0 40px 100px rgba(0, 0, 0, 0.6), 0 0 40px rgba(34, 246, 255, 0.1) !important;
  padding: 40px !important;
}

:deep(.scan-modal) {
  max-width: 480px !important;
}

:deep(.scan-confirm-content) {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

:deep(.scan-icon-pulse) {
  width: 100px;
  height: 100px;
  background: radial-gradient(circle, rgba(34, 246, 255, 0.15) 0%, transparent 70%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--infuse-accent);
  margin-bottom: 24px;
  animation: modal-pulse 2s infinite;
}

@keyframes modal-pulse {
  0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(34, 246, 255, 0.4); }
  70% { transform: scale(1); box-shadow: 0 0 0 20px rgba(34, 246, 255, 0); }
  100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(34, 246, 255, 0); }
}

:deep(.scan-confirm-content h3) {
  font-size: 24px;
  font-weight: 800;
  color: #fff;
  margin-bottom: 12px;
}

:deep(.scan-confirm-content p) {
  font-size: 15px;
  color: var(--infuse-text-secondary);
  line-height: 1.6;
  margin-bottom: 24px;
}

:deep(.scan-status-list) {
  width: 100%;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 16px;
  padding: 16px;
  margin-bottom: 30px;
}

:deep(.status-item) {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 13px;
  color: var(--infuse-text-tertiary);
  margin-bottom: 8px;
}

:deep(.status-item:last-child) { margin-bottom: 0; }

:deep(.status-item .dot) {
  width: 6px;
  height: 6px;
  background: var(--infuse-accent);
  border-radius: 50%;
  box-shadow: 0 0 8px var(--infuse-accent);
}

:deep(.infuse-btn-scan-main) {
  background: linear-gradient(135deg, #22f6ff 0%, #00a8ff 100%) !important;
  border: none !important;
  color: #04111c !important;
  font-weight: 800 !important;
  font-size: 16px !important;
  padding: 16px 40px !important;
  border-radius: 100px !important;
  transition: all 0.3s ease !important;
  width: 100% !important;
}

:deep(.infuse-btn-scan-main:hover) {
  transform: translateY(-3px) !important;
  box-shadow: 0 15px 30px rgba(34, 246, 255, 0.3) !important;
}

:deep(.infuse-btn-cancel-main) {
  background: transparent !important;
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
  color: var(--infuse-text-muted) !important;
  margin-top: 12px !important;
  width: 100% !important;
}

/* 错误弹窗美化 */
:deep(.error-modal) {
  border-color: rgba(255, 43, 214, 0.3) !important;
}

:deep(.error-msg-content) {
  text-align: center;
}

:deep(.error-detail) {
  background: rgba(255, 43, 214, 0.05);
  border: 1px solid rgba(255, 43, 214, 0.1);
  border-radius: 12px;
  padding: 12px;
  font-family: monospace;
  font-size: 12px;
  color: #ff2bd6;
  margin: 16px 0;
}

/* 全局消息提醒美化 */
:deep(.infuse-message) {
  background: rgba(15, 24, 52, 0.8) !important;
  backdrop-filter: blur(20px) !important;
  border: 1px solid var(--infuse-border) !important;
  border-radius: 100px !important;
  padding: 12px 24px !important;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3) !important;
}

/* 活动过渡动画 */
.activity-enter-active,
.activity-leave-active {
  transition: all 0.4s ease;
}

.activity-enter-from {
  opacity: 0;
  transform: translateX(-30px);
}

.activity-leave-to {
  opacity: 0;
  transform: translateX(30px);
}

/* 脉冲动画增强 */
@keyframes pulse-scale {
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.02);
  }
}
</style>
