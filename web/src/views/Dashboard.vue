<template>
  <div class="dashboard page-shell" ref="dashboardRef" @mousemove="handleMouseMove" @mouseleave="handleMouseLeave">
    <!-- 鼠标跟随后景(黑洞效果) -->
    <div class="mouse-glow blackhole" :style="mouseGlowStyle"></div>

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
        <div class="stat-icon" style="background: linear-gradient(135deg, #ff6b35 0%, #ff8555 100%);">
          <el-icon><Film /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.totalMovies }}</div>
          <div class="stat-label">电影</div>
          <div class="stat-sublabel">
            <span class="highlight-success">{{ stats.moviesWithSubtitle }}</span> 有字幕 /
            <span class="highlight-warning">{{ stats.moviesWithoutSubtitle }}</span> 缺字幕
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
        <div class="stat-icon" style="background: linear-gradient(135deg, #5856d6 0%, #af52de 100%);">
          <el-icon><VideoCamera /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.totalTVShows }}</div>
          <div class="stat-label">电视剧</div>
          <div class="stat-sublabel">
            <span class="highlight-info">{{ stats.totalEpisodes }}</span> 集 /
            <span class="highlight-success">{{ stats.episodesWithSubtitle }}</span> 有字幕
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
        <div class="stat-icon" style="background: linear-gradient(135deg, #ff2d55 0%, #ff6b8a 100%);">
          <el-icon><Grid /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.totalAnime }}</div>
          <div class="stat-label">动漫</div>
          <div class="stat-sublabel">
            <span class="highlight-success">{{ stats.animeWithSubtitle }}</span> 有字幕 /
            <span class="highlight-warning">{{ stats.animeWithoutSubtitle }}</span> 缺字幕
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
        <div class="stat-icon" style="background: linear-gradient(135deg, #34c759 0%, #30d158 100%);">
          <el-icon><Check /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value-row">
            <div class="stat-mini">
              <span class="mini-value success">{{ stats.totalWithSubtitle }}</span>
              <span class="mini-label">已有字幕</span>
            </div>
            <div class="stat-divider"></div>
            <div class="stat-mini">
              <span class="mini-value warning">{{ stats.totalWithoutSubtitle }}</span>
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
          <div class="action-icon-wrapper" style="background: linear-gradient(135deg, #ff6b35 0%, #ff8555 100%);">
            <el-icon class="action-icon"><Refresh /></el-icon>
          </div>
          <span class="action-text">扫描库</span>
        </button>

        <button class="action-card infuse-card infuse-tilt infuse-ripple-target" @click="triggerRipple($event); $router.push('/batch-upload')" @mousemove="handleTiltMove" @mouseleave="handleTiltLeave">
          <div class="action-icon-wrapper" style="background: linear-gradient(135deg, #5856d6 0%, #af52de 100%);">
            <el-icon class="action-icon"><Upload /></el-icon>
          </div>
          <span class="action-text">批量上传</span>
        </button>

        <button class="action-card infuse-card infuse-tilt infuse-ripple-target" @click="triggerRipple($event); handleAutoDownload()" @mousemove="handleTiltMove" @mouseleave="handleTiltLeave">
          <div class="action-icon-wrapper" style="background: linear-gradient(135deg, #34c759 0%, #30d158 100%);">
            <el-icon class="action-icon"><Download /></el-icon>
          </div>
          <span class="action-text">自动下载</span>
        </button>

        <button class="action-card infuse-card infuse-tilt infuse-ripple-target" @click="triggerRipple($event); $router.push('/settings')" @mousemove="handleTiltMove" @mouseleave="handleTiltLeave">
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
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useSubtitleStore } from '../stores/subtitle'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Film, Check, Warning, Loading, Refresh, Upload, Download, Setting, InfoFilled,
  VideoCamera, ArrowRight, Grid, Clock
} from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/zh-cn'
import axios from 'axios'
import { useAmbientEffects } from '../composables/useAmbientEffects'
import { buildScanConfirmHtml, createScanDialogOptions } from '../utils/scanDialog'

dayjs.extend(relativeTime)
dayjs.locale('zh-cn')

const api = axios.create({
  baseURL: '/api',
  timeout: 30000
})

// Add API key to requests
api.interceptors.request.use(config => {
  const apiKey = localStorage.getItem('apiKey')
  if (apiKey) {
    config.headers['X-API-Key'] = apiKey
  }
  return config
})

const store = useSubtitleStore()

// Refs
const {
  containerRef: dashboardRef,
  particles,
  parallaxStyle,
  mouseGlowStyle,
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

async function fetchActivities() {
  loadingActivities.value = true
  try {
    const response = await api.get('/recent-activity', {
      params: { limit: 10 }
    })
    activities.value = response.data || []
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

    ElMessage({
      message: '扫描进程已在后台启动, 请稍后查看更新',
      type: 'info',
      duration: 5000,
      customClass: 'infuse-message'
    })
    
    const result = await store.scanLibrary()

    if (result && result.success === false) {
      throw new Error(result.message || '服务器内部扫描任务调度失败')
    }

    // 等待后台扫描并更新UI状态
    setTimeout(async () => {
      const data = await store.fetchStats()
      rawStats.value = data
      await fetchActivities()
      ElMessage.success({
        message: '媒体库扫描同步完成, 数据已更新',
        customClass: 'infuse-message'
      })
    }, 3000)

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
    ElMessage.success('功能开发中')
  } catch (error) {
    ElMessage.error('提交失败')
  }
}

function formatTime(time) {
  return dayjs(time).fromNow()
}

function getActivityIcon(type) {
  const icons = {
    scan: 'Refresh',
    download: 'Download',
    upload: 'Upload',
    process: 'Loading',
    delete: 'Delete'
  }
  return icons[type] || 'InfoFilled'
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

/* 黑洞效果 */
.mouse-glow {
  position: absolute;
  width: 280px;
  height: 280px;
  background: radial-gradient(circle, rgba(34, 246, 255, 0.22) 0%, transparent 70%);
  border-radius: 50%;
  pointer-events: none;
  z-index: 1;
  transform: translate(-50%, -50%);
  transition: opacity 0.3s ease;
  filter: blur(20px);
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

/* Infuse 卡片增强 */
.infuse-card {
  background: rgba(10, 16, 38, 0.65);
  border-radius: var(--infuse-radius-lg);
  border: 1px solid rgba(119, 247, 255, 0.12);
  backdrop-filter: blur(24px);
  overflow: hidden;
  transition: all 0.5s cubic-bezier(0.16, 1, 0.3, 1);
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
}

.infuse-card:hover {
  border-color: var(--infuse-accent);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4), var(--infuse-shadow-glow);
}

/* 统计卡片 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24px;
  margin-bottom: 50px;
}

.stat-card {
  position: relative;
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 28px;
  cursor: pointer;
  transform-style: preserve-3d;
  will-change: transform;
}

.stat-glow {
  position: absolute;
  width: 250px;
  height: 250px;
  background: radial-gradient(circle, rgba(34, 246, 255, 0.12) 0%, transparent 70%);
  border-radius: 50%;
  transform: translate(-50%, -50%);
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.4s ease;
  filter: blur(30px);
  z-index: 0;
}

.stat-icon {
  width: 64px;
  height: 64px;
  border-radius: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 28px;
  flex-shrink: 0;
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.3);
  transition: all 0.5s cubic-bezier(0.16, 1, 0.3, 1);
  position: relative;
  z-index: 1;
}

.stat-card:hover .stat-icon {
  transform: scale(1.15) translateZ(20px) rotate(-5deg);
}

.stat-content {
  flex: 1;
  min-width: 0;
  position: relative;
  z-index: 1;
}

.stat-value {
  font-size: 40px;
  font-weight: 800;
  line-height: 1;
  margin-bottom: 6px;
  background: linear-gradient(180deg, #fff 0%, rgba(255,255,255,0.7) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  transition: transform 0.4s ease;
}

.stat-card:hover .stat-value {
  transform: translateZ(10px);
}

.stat-label {
  font-size: 14px;
  color: var(--infuse-text-secondary);
  font-weight: 500;
  margin-bottom: 4px;
}

.stat-sublabel {
  font-size: 12px;
  color: var(--infuse-text-muted);
}

.highlight-success {
  color: #34c759;
  font-weight: 600;
}

.highlight-warning {
  color: #ff9500;
  font-weight: 600;
}

.highlight-info {
  color: #5856d6;
  font-weight: 600;
}

.card-arrow {
  position: absolute;
  right: 16px;
  top: 50%;
  transform: translateY(-50%) translateX(10px);
  opacity: 0;
  color: var(--infuse-accent);
  transition: all 0.3s;
}

.stat-card.hovered .card-arrow {
  opacity: 1;
  transform: translateY(-50%) translateX(0);
}

/* 总览卡片 */
.total-card {
  grid-column: span 1;
}

.stat-value-row {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-mini {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.mini-value {
  font-size: 28px;
  font-weight: 800;
  line-height: 1;
  background: linear-gradient(180deg, #fff 0%, rgba(255,255,255,0.7) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.mini-value.success {
  background: linear-gradient(180deg, #34c759 0%, #30d158 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.mini-value.warning {
  background: linear-gradient(180deg, #ff9500 0%, #ffcc00 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.mini-label {
  font-size: 11px;
  color: var(--infuse-text-muted);
  margin-top: 4px;
}

.stat-divider {
  width: 1px;
  height: 40px;
  background: linear-gradient(180deg, transparent, var(--infuse-border), transparent);
}

/* 分区标题 */
.section-title {
  font-size: 22px;
  font-weight: 700;
  margin-bottom: 20px;
  color: var(--infuse-text-primary);
  letter-spacing: -0.01em;
  display: flex;
  align-items: center;
  gap: 12px;
}

.section-title::after {
  content: "";
  flex: 1;
  height: 1px;
  background: linear-gradient(90deg, var(--infuse-border), transparent);
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
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 32px 24px;
  cursor: pointer;
  border: none;
  background: linear-gradient(180deg, rgba(255,255,255,0.04), transparent 28%), rgba(10, 16, 38, 0.76);
  border: 1px solid rgba(119, 247, 255, 0.12) !important;
  overflow: hidden;
}

.action-card::before {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(255, 107, 53, 0.1), transparent 50%);
  opacity: 0;
  transition: opacity 0.3s;
}

.action-card.hovered::before {
  opacity: 1;
}

.action-card.hovered {
  transform: translateY(-8px) scale(1.02);
  border-color: var(--infuse-accent) !important;
  box-shadow: var(--infuse-shadow-glow), var(--infuse-shadow-lg);
}

.action-icon-wrapper {
  width: 68px;
  height: 68px;
  border-radius: var(--infuse-radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 30px;
  box-shadow: 0 10px 25px rgba(0,0,0,0.3);
  transition: transform 0.4s cubic-bezier(0.22, 1, 0.36, 1);
}

.action-card.hovered .action-icon-wrapper {
  transform: scale(1.1) rotate(5deg);
}

.action-text {
  font-size: 15px;
  font-weight: 600;
  color: var(--infuse-text-primary);
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

/* 扫描按钮特殊效果 */
.actions-grid .action-card:first-child.hovered .action-icon-wrapper {
  animation: pulse-glow 1.5s ease-in-out infinite;
}

@keyframes pulse-glow {
  0%, 100% {
    box-shadow: 0 10px 25px rgba(0,0,0,0.3);
  }
  50% {
    box-shadow: 0 10px 35px rgba(255, 107, 53, 0.6), 0 0 50px rgba(255, 107, 53, 0.3);
  }
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
