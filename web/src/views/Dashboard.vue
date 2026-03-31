<template>
  <div class="dashboard" ref="dashboardRef" @mousemove="handleMouseMove" @mouseleave="handleMouseLeave">
    <!-- 背景粒子效果 -->
    <div class="bg-particles">
      <div
        v-for="n in 20"
        :key="n"
        class="particle"
        :style="getParticleStyle(n)"
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
        class="stat-card infuse-card"
        @click="$router.push('/movies')"
        @mouseenter="handleCardHover(0, $event)"
        @mousemove="handleCardMouseMove(0, $event)"
        @mouseleave="handleCardMouseLeave(0)"
      >
        <div class="stat-glow" :ref="el => statGlowRefs[0] = el"></div>
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
        class="stat-card infuse-card"
        @click="$router.push('/tvshows')"
        @mouseenter="handleCardHover(1, $event)"
        @mousemove="handleCardMouseMove(1, $event)"
        @mouseleave="handleCardMouseLeave(1)"
      >
        <div class="stat-glow" :ref="el => statGlowRefs[1] = el"></div>
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
        class="stat-card infuse-card"
        @click="$router.push('/anime')"
        @mouseenter="handleCardHover(2, $event)"
        @mousemove="handleCardMouseMove(2, $event)"
        @mouseleave="handleCardMouseLeave(2)"
      >
        <div class="stat-glow" :ref="el => statGlowRefs[2] = el"></div>
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
        class="stat-card total-card infuse-card"
        @mouseenter="handleCardHover(3, $event)"
        @mousemove="handleCardMouseMove(3, $event)"
        @mouseleave="handleCardMouseLeave(3)"
      >
        <div class="stat-glow" :ref="el => statGlowRefs[3] = el"></div>
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
        <button class="action-card infuse-card" @click="handleScan" @mouseenter="handleActionHover(0, $event)" @mouseleave="handleActionLeave">
          <div class="action-icon-wrapper" style="background: linear-gradient(135deg, #ff6b35 0%, #ff8555 100%);">
            <el-icon class="action-icon"><Refresh /></el-icon>
          </div>
          <span class="action-text">扫描库</span>
          <div class="action-ripple" :ref="el => rippleRefs[0] = el"></div>
        </button>

        <button class="action-card infuse-card" @click="$router.push('/batch-upload')" @mouseenter="handleActionHover(1, $event)" @mouseleave="handleActionLeave">
          <div class="action-icon-wrapper" style="background: linear-gradient(135deg, #5856d6 0%, #af52de 100%);">
            <el-icon class="action-icon"><Upload /></el-icon>
          </div>
          <span class="action-text">批量上传</span>
          <div class="action-ripple" :ref="el => rippleRefs[1] = el"></div>
        </button>

        <button class="action-card infuse-card" @click="handleAutoDownload" @mouseenter="handleActionHover(2, $event)" @mouseleave="handleActionLeave">
          <div class="action-icon-wrapper" style="background: linear-gradient(135deg, #34c759 0%, #30d158 100%);">
            <el-icon class="action-icon"><Download /></el-icon>
          </div>
          <span class="action-text">自动下载</span>
          <div class="action-ripple" :ref="el => rippleRefs[2] = el"></div>
        </button>

        <button class="action-card infuse-card" @click="$router.push('/settings')" @mouseenter="handleActionHover(3, $event)" @mouseleave="handleActionLeave">
          <div class="action-icon-wrapper" style="background: linear-gradient(135deg, #0071e3 0%, #42a5f5 100%);">
            <el-icon class="action-icon"><Setting /></el-icon>
          </div>
          <span class="action-text">设置</span>
          <div class="action-ripple" :ref="el => rippleRefs[3] = el"></div>
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
import { ref, reactive, onMounted, computed } from 'vue'
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
const dashboardRef = ref(null)
const statGlowRefs = reactive([null, null, null, null])
const rippleRefs = reactive([null, null, null, null])

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
const mousePos = reactive({ x: 0, y: 0 })

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

// Parallax style for welcome section
const parallaxStyle = computed(() => ({
  transform: `translateY(${mousePos.y * 0.02}px)`
}))

// Particle style generator
function getParticleStyle(n) {
  const size = Math.random() * 4 + 2
  const duration = Math.random() * 20 + 15
  const delay = Math.random() * 10
  return {
    width: `${size}px`,
    height: `${size}px`,
    left: `${Math.random() * 100}%`,
    top: `${Math.random() * 100}%`,
    animationDuration: `${duration}s`,
    animationDelay: `${delay}s`,
    opacity: Math.random() * 0.5 + 0.1
  }
}

// Mouse handlers
function handleMouseMove(e) {
  const rect = dashboardRef.value.getBoundingClientRect()
  mousePos.x = e.clientX - rect.left
  mousePos.y = e.clientY - rect.top
}

function handleMouseLeave() {
  mousePos.x = 0
  mousePos.y = 0
}

function handleCardHover(index, e) {
  const card = e.currentTarget
  card.classList.add('hovered')
}

function handleCardMouseMove(index, e) {
  const card = e.currentTarget
  const rect = card.getBoundingClientRect()
  const x = e.clientX - rect.left
  const y = e.clientY - rect.top
  const centerX = rect.width / 2
  const centerY = rect.height / 2
  const rotateX = (y - centerY) / 10
  const rotateY = (centerX - x) / 10

  card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateY(-4px)`

  // Update glow position
  const glow = statGlowRefs[index]
  if (glow) {
    glow.style.left = `${x}px`
    glow.style.top = `${y}px`
    glow.style.opacity = '1'
  }
}

function handleCardMouseLeave(index) {
  const cards = document.querySelectorAll('.stat-card')
  cards[index].style.transform = ''
  cards[index].classList.remove('hovered')

  const glow = statGlowRefs[index]
  if (glow) {
    glow.style.opacity = '0'
  }
}

function handleActionHover(index, e) {
  const btn = e.currentTarget
  btn.classList.add('hovered')

  // Create ripple effect
  const ripple = rippleRefs[index]
  if (ripple) {
    const rect = btn.getBoundingClientRect()
    const x = e.clientX - rect.left
    const y = e.clientY - rect.top
    ripple.style.left = `${x}px`
    ripple.style.top = `${y}px`
    ripple.classList.add('active')
  }
}

function handleActionLeave() {
  document.querySelectorAll('.action-card').forEach(btn => {
    btn.classList.remove('hovered')
  })
  document.querySelectorAll('.action-ripple').forEach(ripple => {
    ripple.classList.remove('active')
  })
}

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
      `<div class="scan-confirm-content">
        <p>即将扫描所有媒体库文件</p>
        <p class="scan-hint">查找缺失的字幕文件</p>
      </div>`,
      '确认全盘扫描',
      {
        confirmButtonText: '开始扫描',
        cancelButtonText: '取消',
        type: 'info',
        dangerouslyUseHTMLString: true,
        confirmButtonClass: 'infuse-btn-primary scan-confirm-btn',
        cancelButtonClass: 'infuse-btn-cancel',
        showClose: false,
        closeOnClickModal: false,
        closeOnPressEscape: false,
        beforeClose: (action, instance, done) => {
          if (action === 'confirm') {
            instance.confirmButtonLoading = true
            instance.confirmButtonText = '扫描中...'
            instance.cancelButtonText = ''
            instance.showClose = false
            // 返回不关闭
            return
          }
          done()
        }
      }
    )

    ElMessage.info('正在扫描媒体库...')
    const result = await store.scanLibrary()

    if (result && result.success === false) {
      ElMessage.error(result.message || '扫描失败')
      return
    }

    ElMessage.success('扫描完成!正在更新数据...')

    // 等待后台扫描完成
    await new Promise(resolve => setTimeout(resolve, 2000))

    // 刷新统计数据
    const data = await store.fetchStats()
    rawStats.value = data

    // 刷新活动记录
    await fetchActivities()

    ElMessage.success('数据已更新')
  } catch (error) {
    if (error === 'cancel' || error === 'close' || error === '') {
      return
    }
    console.error('扫描失败:', error)
    ElMessage.error('扫描失败: ' + (error.message || '未知错误'))
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
  padding: 20px;
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
  box-shadow: 0 0 10px var(--infuse-accent);
}

@keyframes float-particle {
  0% {
    transform: translateY(0) rotate(0deg);
    opacity: 0;
  }
  10% {
    opacity: 1;
  }
  90% {
    opacity: 1;
  }
  100% {
    transform: translateY(-100vh) rotate(720deg);
    opacity: 0;
  }
}

/* 黑洞效果 */
/* 入场动画 */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.dashboard > * {
  position: relative;
  z-index: 2;
  animation: fadeInUp 0.6s cubic-bezier(0.22, 1, 0.36, 1) both;
}

.welcome-section { animation-delay: 0.05s; }
.stats-grid { animation-delay: 0.1s; }
.quick-actions { animation-delay: 0.15s; }
.recent-activity { animation-delay: 0.2s; }

/* 欢迎区域 */
.welcome-section {
  margin-bottom: 40px;
}

.welcome-title {
  font-size: 48px;
  font-weight: 900;
  background: linear-gradient(135deg, #fff 0%, #77f7ff 42%, #ff8be9 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin-bottom: 8px;
  letter-spacing: -0.02em;
  text-shadow: 0 0 40px rgba(119, 247, 255, 0.3);
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
  transition: all 0.4s cubic-bezier(0.22, 1, 0.36, 1);
}

.infuse-card:hover {
  border-color: var(--infuse-border-hover);
}

/* 统计卡片 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 48px;
}

.stat-card {
  position: relative;
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 24px;
  background: linear-gradient(180deg, rgba(255,255,255,0.04), transparent 28%), rgba(10, 16, 38, 0.76);
  border: 1px solid rgba(119, 247, 255, 0.12);
  cursor: pointer;
  transform-style: preserve-3d;
}

.stat-card::before {
  content: "";
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at var(--mouse-x, 50%) var(--mouse-y, 50%), rgba(255, 255, 255, 0.1) 0%, transparent 50%);
  opacity: 0;
  transition: opacity 0.3s;
  pointer-events: none;
}

.stat-card.hovered::before {
  opacity: 1;
}

.stat-glow {
  position: absolute;
  width: 200px;
  height: 200px;
  background: radial-gradient(circle, var(--infuse-accent) 0%, transparent 70%);
  border-radius: 50%;
  transform: translate(-50%, -50%);
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.3s;
  filter: blur(30px);
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 26px;
  flex-shrink: 0;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3);
  transition: transform 0.4s cubic-bezier(0.22, 1, 0.36, 1);
}

.stat-card.hovered .stat-icon {
  transform: scale(1.1) rotate(5deg);
}

.stat-content {
  flex: 1;
  min-width: 0;
}

.stat-value {
  font-size: 36px;
  font-weight: 800;
  line-height: 1;
  margin-bottom: 4px;
  background: linear-gradient(180deg, #fff 0%, rgba(255,255,255,0.7) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  transition: transform 0.3s;
}

.stat-card.hovered .stat-value {
  transform: scale(1.05);
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

/* 扫描确认对话框样式 */
:deep(.scan-confirm-content) {
  text-align: center;
}

:deep(.scan-confirm-content p) {
  margin: 0;
  font-size: 15px;
}

:deep(.scan-hint) {
  color: var(--infuse-text-muted);
  font-size: 13px !important;
  margin-top: 8px !important;
}

:deep(.scan-confirm-btn) {
  background: linear-gradient(135deg, #ff6b35 0%, #ff8555 100%) !important;
  border-color: #ff6b35 !important;
  color: white !important;
  font-weight: 600;
  padding: 12px 32px !important;
  border-radius: 10px;
  transition: all 0.3s ease;
}

:deep(.scan-confirm-btn:hover) {
  background: linear-gradient(135deg, #ff7b45 0%, #ff9555 100%) !important;
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(255, 107, 53, 0.4);
}

:deep(.scan-confirm-btn.el-button--primary.is-loading) {
  background: linear-gradient(135deg, #ff6b35 0%, #ff8555 100%) !important;
}

:deep(.infuse-btn-cancel) {
  background: rgba(255, 255, 255, 0.05) !important;
  border: 1px solid rgba(255, 255, 255, 0.15) !important;
  color: var(--infuse-text-secondary) !important;
  border-radius: 10px;
}

:deep(.infuse-btn-cancel:hover) {
  background: rgba(255, 255, 255, 0.1) !important;
  color: var(--infuse-text-primary) !important;
}

/* 对话框背景美化 */
:deep(.el-message-box) {
  background: var(--infuse-bg-card) !important;
  border: 1px solid var(--infuse-border) !important;
  border-radius: 20px !important;
  box-shadow: 0 25px 80px rgba(0, 0, 0, 0.6), 0 0 0 1px rgba(255, 255, 255, 0.05) inset !important;
  backdrop-filter: blur(30px) !important;
  padding: 30px !important;
}

:deep(.el-message-box__title) {
  color: var(--infuse-text-primary) !important;
  font-weight: 700;
  font-size: 18px;
}

:deep(.el-message-box__message) {
  color: var(--infuse-text-secondary) !important;
  line-height: 1.6;
  font-size: 14px;
}

:deep(.el-message-box__headerbtn .el-message-box__close) {
  color: var(--infuse-text-muted) !important;
  font-size: 18px;
}

:deep(.el-message-box__headerbtn:hover .el-message-box__close) {
  color: var(--infuse-text-primary) !important;
}

:deep(.el-message-box__content) {
  padding: 20px 0 !important;
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
