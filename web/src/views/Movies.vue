<template>
  <div
    class="movies page-shell"
    :class="`display-mode-${displayMode}`"
    ref="containerRef"
    @mousemove="handleMouseMove"
    @mouseleave="handleMouseLeave"
  >
    <!-- 鼠标跟随后景 -->
    <div class="mouse-glow" :style="mouseGlowStyle"></div>

    <!-- 背景粒子效果 -->
    <div class="bg-particles">
      <div
        v-for="particle in particles"
        :key="particle.id"
        class="particle"
        :style="particle.style"
      ></div>
    </div>

    <!-- 页面标题 -->
    <header class="page-header" :style="parallaxStyle">
      <h1 class="page-title">电影</h1>
      <p class="page-subtitle">{{ filteredMovies.length }} 部影片</p>
    </header>

    <!-- 工具栏 -->
    <div class="toolbar infuse-card">
      <div class="search-box">
        <el-input
          v-model="searchQuery"
          placeholder="搜索电影..."
          prefix-icon="Search"
          clearable
        />
      </div>
      <div class="filter-group">
        <el-radio-group v-model="displayMode" class="display-mode-toggle">
          <el-radio-button label="compact">紧凑模式</el-radio-button>
          <el-radio-button label="wide">宽幅模式</el-radio-button>
        </el-radio-group>
        <el-select v-model="filterStatus" placeholder="筛选状态" clearable class="infuse-select">
          <el-option label="全部" value="" />
          <el-option label="有字幕" value="with" />
          <el-option label="无字幕" value="without" />
        </el-select>
        <el-button class="infuse-btn-default scan-btn" @click="handleScan">
          <el-icon><Refresh /></el-icon>
          扫描
        </el-button>
      </div>
    </div>

    <!-- 电影网格 -->
    <div class="movies-grid">
      <div
        v-for="movie in filteredMovies"
        :key="movie.id"
        class="movie-card infuse-card infuse-tilt"
        @click="handleMovieClick(movie)"
        @mousemove="handleTiltMove"
        @mouseleave="handleTiltLeave"
      >
        <div class="movie-poster">
          <img
            v-if="hasMediaArt(movie)"
            :src="getMovieArtUrl(movie)"
            :alt="movie.name"
            class="poster-image"
            @error="handlePosterError"
          />
          <div v-else class="poster-placeholder">
            <el-icon><Film /></el-icon>
          </div>
          <div class="poster-overlay">
            <div class="movie-actions">
              <button
                v-if="!movie.hasSubtitle"
                class="action-btn primary"
                @click.stop="handleSearch(movie)"
              >
                <el-icon><Search /></el-icon>
                搜索字幕
              </button>
              <button
                v-else
                class="action-btn secondary"
                @click.stop="handleManage(movie)"
              >
                <el-icon><Check /></el-icon>
                管理字幕
              </button>
            </div>
          </div>
          <div class="subtitle-badge" :class="{ has: movie.hasSubtitle }">
            {{ movie.hasSubtitle ? '✓' : '无' }}
          </div>
        </div>
        <div class="movie-info">
          <h3 class="movie-title">{{ movie.name }}</h3>
          <div class="movie-meta">
            <span v-if="movie.year" class="meta-item">{{ movie.year }}</span>
            <span v-if="movie.resolution" class="meta-item">{{ movie.resolution }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 字幕搜索对话框 -->
    <el-dialog
      v-model="searchDialogVisible"
      title="搜索字幕"
      width="800px"
      destroy-on-close
      class="infuse-dialog"
    >
      <div v-if="currentMovie" class="search-dialog-content">
        <div class="movie-info-header">
          <div class="header-poster" v-if="hasMediaArt(currentMovie)">
            <img :src="getMovieArtUrl(currentMovie)" :alt="currentMovie.name" />
          </div>
          <div class="header-info">
            <h3>{{ currentMovie.name }}</h3>
            <p class="filename-text">{{ currentMovie.filename }}</p>
            <div class="header-meta">
              <span v-if="currentMovie.year" class="meta-pill">{{ currentMovie.year }}</span>
              <span v-if="currentMovie.resolution" class="meta-pill">{{ currentMovie.resolution }}</span>
            </div>
          </div>
        </div>

        <div class="search-results" v-loading="searching">
          <div v-if="searchResults.length === 0 && !searching" class="empty-results">
            <el-icon class="empty-icon"><Search /></el-icon>
            <p>点击搜索按钮开始查找字幕</p>
          </div>

          <div
            v-for="result in searchResults"
            :key="result.id"
            class="subtitle-item"
          >
            <div class="subtitle-rank" :class="getRankClass(result.score)">
              {{ (result.score * 100).toFixed(0) }}%
            </div>
            <div class="subtitle-info">
              <div class="subtitle-title">{{ result.title }}</div>
              <!-- SubHD 文件名显示 -->
              <div v-if="result.source === 'SubHD' && shouldShowSubhdFilename(result)" class="subhd-filename">
                <el-icon><Document /></el-icon>
                <span class="filename-text" :title="result.filename">{{ result.filename }}</span>
              </div>
              <div v-if="result.source === 'SubHD' && result.summary" class="subhd-summary">
                {{ result.summary }}
              </div>
              <div class="subtitle-meta">
                <span class="source-tag" :class="result.source.toLowerCase()">{{ result.source }}</span>
                <span class="lang-tag">{{ result.language }}</span>
              </div>
            </div>
            <button
              class="action-btn primary"
              :class="{ loading: downloading === result.id }"
              @click="handleDownload(result)"
              :disabled="downloading === result.id"
            >
              <el-icon v-if="downloading !== result.id"><Download /></el-icon>
              <span v-else class="loading-spinner"></span>
              {{ downloading === result.id ? '下载中...' : '下载' }}
            </button>
          </div>
        </div>
      </div>

      <template #footer>
        <el-button class="infuse-btn-default" @click="searchDialogVisible = false">关闭</el-button>
        <el-button type="primary" class="infuse-btn-primary" @click="handleDoSearch" :loading="searching">
          搜索
        </el-button>
      </template>
    </el-dialog>

    <!-- 字幕管理对话框 -->
    <el-dialog
      v-model="manageDialogVisible"
      title="管理字幕"
      width="700px"
      destroy-on-close
      class="infuse-dialog"
    >
      <div v-if="currentMovie" class="manage-dialog-content">
        <div class="movie-info-header">
          <div class="header-poster" v-if="hasMediaArt(currentMovie)">
            <img :src="getMovieArtUrl(currentMovie)" :alt="currentMovie.name" />
          </div>
          <div class="header-info">
            <h3>{{ currentMovie.name }}</h3>
            <p class="filename-text">{{ currentMovie.filename }}</p>
          </div>
        </div>

        <div class="subtitles-section">
          <div class="section-header">
            <h4>已下载字幕</h4>
            <span class="subtitle-count">{{ movieSubtitles.length }} 个字幕</span>
          </div>

          <div v-if="loadingSubtitles" class="loading-subtitles">
            <el-icon class="is-loading"><Refresh /></el-icon>
            加载中...
          </div>

          <div v-else-if="movieSubtitles.length === 0" class="empty-subtitles">
            <el-icon><Document /></el-icon>
            <p>暂无字幕文件</p>
            <el-button type="primary" class="infuse-btn-primary" @click="switchToSearch">
              搜索字幕
            </el-button>
          </div>

          <div v-else class="subtitles-list">
            <div
              v-for="subtitle in movieSubtitles"
              :key="subtitle.id"
              class="subtitle-file-item"
            >
              <div class="file-icon">
                <el-icon><Document /></el-icon>
              </div>
              <div class="file-info">
                <div class="file-name">{{ subtitle.filename }}</div>
                <div class="file-meta">
                  <span class="lang-tag">{{ subtitle.language }}</span>
                  <span class="format-tag">{{ subtitle.format }}</span>
                  <span class="size-tag">{{ subtitle.sizeFormatted }}</span>
                </div>
              </div>
              <button
                class="action-btn danger"
                @click="handleDeleteSubtitle(subtitle)"
                :disabled="deletingSubtitle === subtitle.path"
              >
                <el-icon v-if="deletingSubtitle !== subtitle.path"><Delete /></el-icon>
                <span v-else class="loading-spinner"></span>
                {{ deletingSubtitle === subtitle.path ? '删除中...' : '删除' }}
              </button>
            </div>
          </div>
        </div>
      </div>

      <template #footer>
        <el-button class="infuse-btn-default" @click="manageDialogVisible = false">关闭</el-button>
        <el-button type="primary" class="infuse-btn-primary" @click="switchToSearch">
          搜索新字幕
        </el-button>
      </template>
    </el-dialog>

    <ScanVisualization
      v-model:visible="scanVisualizationVisible"
      title="电影库扫描可视化"
      :status="store.scanStatus"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useSubtitleStore } from '../stores/subtitle'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, Film, Check, Download, Document, Delete } from '@element-plus/icons-vue'
import axios from 'axios'
import { useAmbientEffects } from '../composables/useAmbientEffects'
import { useMediaDisplayMode } from '../composables/useMediaDisplayMode'
import { buildScanConfirmHtml, createScanDialogOptions } from '../utils/scanDialog'
import ScanVisualization from '../components/ScanVisualization.vue'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000
})

const store = useSubtitleStore()
const searchQuery = ref('')
const filterStatus = ref('')
const searchDialogVisible = ref(false)
const manageDialogVisible = ref(false)
const currentMovie = ref(null)
const searchResults = ref([])
const movieSubtitles = ref([])
const searching = ref(false)
const downloading = ref(null)
const loadingSubtitles = ref(false)
const deletingSubtitle = ref(null)
const scanVisualizationVisible = ref(false)
let scanPollTimer = null
const { displayMode, artPreference } = useMediaDisplayMode()
const {
  containerRef,
  particles,
  parallaxStyle,
  mouseGlowStyle,
  handleMouseMove,
  handleMouseLeave,
  handleTiltMove,
  handleTiltLeave
} = useAmbientEffects({ particleCount: 25, parallaxFactor: 0.005 })

const movies = ref([])

const filteredMovies = computed(() => {
  let result = movies.value
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(m => m.name.toLowerCase().includes(query))
  }
  if (filterStatus.value === 'with') {
    result = result.filter(m => m.hasSubtitle)
  } else if (filterStatus.value === 'without') {
    result = result.filter(m => !m.hasSubtitle)
  }
  return result
})

function hasMediaArt(media) {
  return Boolean(media?.posterPath || media?.fanartPath)
}

function getMovieArtUrl(movie) {
  if (!movie?.id) return ''
  return `/api/art/movie/${movie.id}?preferred=${artPreference.value}`
}

onMounted(async () => {
  try {
    await store.fetchMovies()
    movies.value = store.movies
  } catch (error) {
    ElMessage.error('获取电影列表失败')
  }
})

onBeforeUnmount(() => {
  stopScanPolling()
})

function handleMovieClick(movie) {
  // 可以展示详情或者管理
}

function handleSearch(movie) {
  currentMovie.value = movie
  searchDialogVisible.value = true
  searchResults.value = []
}

async function handleManage(movie) {
  currentMovie.value = movie
  manageDialogVisible.value = true
  await loadMovieSubtitles()
}

async function loadMovieSubtitles() {
  if (!currentMovie.value) return
  loadingSubtitles.value = true
  try {
    const response = await api.get(`/movies/${currentMovie.value.id}/subtitles`)
    movieSubtitles.value = response.data.subtitles || []
  } catch (error) {
    ElMessage.error('加载字幕列表失败')
    movieSubtitles.value = []
  } finally {
    loadingSubtitles.value = false
  }
}

async function handleDeleteSubtitle(subtitle) {
  try {
    deletingSubtitle.value = subtitle.path
    await api.post('/subtitles/delete', { subtitlePath: subtitle.path })
    ElMessage.success('字幕已删除')
    await loadMovieSubtitles()
    await store.fetchMovies()
    movies.value = store.movies
  } catch (error) {
    ElMessage.error('删除字幕失败')
  } finally {
    deletingSubtitle.value = null
  }
}

function switchToSearch() {
  manageDialogVisible.value = false
  searchDialogVisible.value = true
  searchResults.value = []
}

function getRankClass(score) {
  if (score >= 0.8) return 'excellent'
  if (score >= 0.6) return 'good'
  if (score >= 0.4) return 'fair'
  return 'poor'
}

function normalizeSubtitleLabel(value) {
  return (value || '').toLowerCase().replace(/[.\-_()[\]{}]/g, ' ').replace(/\s+/g, ' ').trim()
}

function shouldShowSubhdFilename(result) {
  if (!result?.filename) return false
  return normalizeSubtitleLabel(result.filename) !== normalizeSubtitleLabel(result.title)
}

function markMovieHasSubtitle(movieId, hasSubtitle = true) {
  const target = movies.value.find(movie => movie.id === movieId)
  if (target) target.hasSubtitle = hasSubtitle
  if (currentMovie.value?.id === movieId) {
    currentMovie.value = { ...currentMovie.value, hasSubtitle }
  }
}

async function handleDoSearch() {
  if (!currentMovie.value) return
  searching.value = true
  try {
    const response = await api.post(`/movies/${currentMovie.value.id}/search-subtitles`)
    searchResults.value = response.data.sort((a, b) => b.score - a.score)
    if (searchResults.value.length === 0) ElMessage.info('未找到匹配的字幕')
  } catch (error) {
    ElMessage.error('搜索失败')
  } finally {
    searching.value = false
  }
}

async function handleDownload(result) {
  downloading.value = result.id
  try {
    const requestData = {
      subtitle_id: result.id,
      source_name: result.source,
      subtitle_result: {
        id: result.id,
        source: result.source,
        title: result.title,
        language: result.language,
        downloadUrl: result.downloadUrl,
        score: result.score,
        filename: result.filename
      }
    }
    await api.post(`/movies/${currentMovie.value.id}/download-subtitle`, requestData)
    ElMessage.success('字幕下载成功')
    searchDialogVisible.value = false
    markMovieHasSubtitle(currentMovie.value.id, true)
  } catch (error) {
    ElMessage.error('下载失败')
  } finally {
    downloading.value = null
  }
}

async function handleScan() {
  try {
    await ElMessageBox.confirm(
      buildScanConfirmHtml({
        title: '确认扫描电影库',
        description: '系统会重新遍历电影目录，同步新增影片并补齐缺失字幕状态。',
        steps: ['扫描电影文件', '更新媒体元数据', '刷新字幕状态']
      }),
      '',
      createScanDialogOptions('扫描中...')
    )
    
    ElMessage.info({ message: '正在扫描电影库...', customClass: 'infuse-message' })
    const result = await store.scanLibrary()
    if (result && result.success === false) throw new Error(result.message || '扫描失败')
    scanVisualizationVisible.value = true
    startScanPolling(async () => {
      await store.fetchMovies()
      movies.value = store.movies
      ElMessage.success({ message: '电影库列表已更新', customClass: 'infuse-message' })
    })
    ElMessage.success({ message: '扫描任务已提交，正在展开扫描树...', customClass: 'infuse-message' })
  } catch (error) {
    if (error === 'cancel' || error === 'close') return
    ElMessage.error({ message: '扫描失败: ' + (error.message || '未知错误'), customClass: 'infuse-message' })
  }
}

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

function handlePosterError(event) {
  event.target.style.display = 'none'
  event.target.nextElementSibling?.classList.add('show-placeholder')
}
</script>

<style scoped>
.movies {
  max-width: 1600px;
  position: relative;
  overflow: hidden;
}

/* 鼠标跟随后景 */
.mouse-glow {
  position: fixed;
  width: 600px;
  height: 600px;
  background: radial-gradient(circle, rgba(34, 246, 255, 0.05) 0%, transparent 70%);
  border-radius: 50%;
  pointer-events: none;
  z-index: 0;
  transform: translate(-50%, -50%);
  transition: opacity 1s ease;
  filter: blur(40px);
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
  0% { transform: translateY(0) scale(1); opacity: 0; }
  10% { opacity: 1; }
  90% { opacity: 1; }
  100% { transform: translateY(-100vh) scale(0.5); opacity: 0; }
}

.page-header {
  margin-bottom: 32px;
  position: relative;
  z-index: 1;
}

.page-title {
  font-size: 42px;
  font-weight: 800;
  color: var(--infuse-text-primary);
  margin-bottom: 8px;
  letter-spacing: -0.02em;
}

.page-subtitle {
  font-size: 18px;
  color: var(--infuse-text-secondary);
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 40px;
  gap: 16px;
  padding: 20px 24px;
  background: rgba(8, 14, 34, 0.62);
  border: 1px solid var(--infuse-border);
  border-radius: var(--infuse-radius-lg);
  backdrop-filter: blur(18px);
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.03);
  position: relative;
  z-index: 1;
}

.search-box {
  width: 320px;
}

.filter-group {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.display-mode-toggle {
  --el-border-radius-base: 999px;
}

.display-mode-toggle :deep(.el-radio-button__inner) {
  background: rgba(255, 255, 255, 0.04);
  border-color: rgba(255, 255, 255, 0.08);
  color: var(--infuse-text-secondary);
  box-shadow: none;
  min-width: 96px;
}

.display-mode-toggle :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background: linear-gradient(135deg, rgba(34, 246, 255, 0.9), rgba(0, 168, 255, 0.9));
  border-color: transparent;
  color: #04111c;
}

.scan-btn {
  background: linear-gradient(135deg, rgba(255, 107, 53, 0.15), rgba(255, 133, 85, 0.15)) !important;
  border-color: rgba(255, 107, 53, 0.4) !important;
  color: #ff6b35 !important;
}

.scan-btn:hover {
  background: linear-gradient(135deg, rgba(255, 107, 53, 0.25), rgba(255, 133, 85, 0.25)) !important;
  border-color: #ff6b35 !important;
  color: #ff8555 !important;
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(255, 107, 53, 0.3);
}

.scan-btn .el-icon {
  transition: transform 0.3s ease;
}

.scan-btn:hover .el-icon {
  transform: rotate(90deg);
}

.movies-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 32px;
  position: relative;
  z-index: 1;
}

.movie-card {
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.165, 0.84, 0.44, 1);
  position: relative;
  transform-style: preserve-3d;
  will-change: transform;
}

.movie-poster {
  position: relative;
  aspect-ratio: 2/3;
  background: linear-gradient(145deg, rgba(11, 20, 48, 0.92), rgba(8, 13, 30, 0.96));
  border-radius: var(--infuse-radius-lg);
  overflow: hidden;
  border: 1px solid rgba(119, 247, 255, 0.12);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
}

.display-mode-wide .movies-grid {
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
}

.display-mode-wide .movie-poster {
  aspect-ratio: 16 / 9;
}

.movie-poster::before {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(34, 246, 255, 0.14), transparent 32%, rgba(255, 43, 214, 0.14));
  opacity: 0;
  transition: opacity 0.4s;
  z-index: 1;
}

.movie-card:hover .movie-poster::before {
  opacity: 1;
}

.poster-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.6s cubic-bezier(0.165, 0.84, 0.44, 1);
}

.movie-card:hover .poster-image {
  transform: scale(1.08);
}

.poster-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, transparent 40%, rgba(6, 10, 26, 0.9) 100%);
  opacity: 0;
  transition: opacity 0.3s;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  padding: 24px;
  z-index: 2;
}

.movie-card:hover .poster-overlay {
  opacity: 1;
}

.movie-actions {
  transform: translateY(10px);
  transition: transform 0.3s;
}

.movie-card:hover .movie-actions {
  transform: translateY(0);
}

.action-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  border-radius: 100px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}

.action-btn.primary {
  background: var(--infuse-accent);
  color: #07101a;
}

.action-btn.primary:hover {
  background: var(--infuse-accent-hover);
  box-shadow: 0 0 15px var(--infuse-accent);
}

.action-btn.secondary {
  background: rgba(255, 255, 255, 0.1);
  color: white;
  backdrop-filter: blur(10px);
}

.subtitle-badge {
  position: absolute;
  top: 12px;
  right: 12px;
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 11px;
  font-weight: 700;
  background: rgba(255, 43, 214, 0.8);
  color: white;
  z-index: 3;
}

.subtitle-badge.has {
  background: rgba(34, 246, 255, 0.8);
  color: #07101a;
}

.movie-info {
  padding: 16px 8px;
}

.movie-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--infuse-text-primary);
  margin-bottom: 8px;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.movie-meta {
  display: flex;
  gap: 8px;
}

.meta-item {
  font-size: 11px;
  color: var(--infuse-text-secondary);
  background: rgba(255, 255, 255, 0.05);
  padding: 2px 8px;
  border-radius: 4px;
}

/* 对话框通用样式 */
:deep(.infuse-dialog) {
  background: var(--infuse-bg-secondary);
  border-radius: 20px;
}

.movie-info-header {
  display: flex;
  gap: 20px;
  padding: 24px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 16px;
  margin-bottom: 24px;
}

.header-poster {
  width: 100px;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 8px 16px rgba(0,0,0,0.3);
}

.header-poster img {
  width: 100%;
  height: auto;
}

.header-info h3 {
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 8px;
}

.filename-text {
  font-size: 13px;
  color: var(--infuse-text-muted);
  margin-bottom: 12px;
  word-break: break-all;
}

.meta-pill {
  padding: 4px 12px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 20px;
  font-size: 12px;
  margin-right: 8px;
}

/* 响应式 */
@media (max-width: 768px) {
  .movies-grid {
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
    gap: 16px;
  }
  .toolbar {
    flex-direction: column;
  }
  .search-box {
    width: 100%;
  }

  .filter-group {
    width: 100%;
    justify-content: stretch;
  }

  .display-mode-toggle {
    width: 100%;
    display: grid;
    grid-template-columns: 1fr 1fr;
  }

  .display-mode-toggle :deep(.el-radio-button) {
    width: 100%;
  }

  .display-mode-toggle :deep(.el-radio-button__inner) {
    width: 100%;
    min-width: 0;
  }

  .display-mode-compact .movies-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 16px;
  }

  .display-mode-compact .movie-poster {
    aspect-ratio: 2 / 3;
  }

  .display-mode-wide .movies-grid {
    grid-template-columns: 1fr;
    gap: 20px;
  }

  .display-mode-wide .movie-poster {
    aspect-ratio: 16 / 9;
  }
}

/* 扫描确认对话框样式 */
:deep(.scan-modal) {
  max-width: 420px !important;
}

:deep(.scan-confirm-content) {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

:deep(.scan-icon-pulse) {
  width: 80px;
  height: 80px;
  background: radial-gradient(circle, rgba(34, 246, 255, 0.15) 0%, transparent 70%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--infuse-accent);
  margin-bottom: 20px;
  animation: modal-pulse 2s infinite;
}

@keyframes modal-pulse {
  0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(34, 246, 255, 0.4); }
  70% { transform: scale(1); box-shadow: 0 0 0 15px rgba(34, 246, 255, 0); }
  100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(34, 246, 255, 0); }
}

:deep(.infuse-btn-scan-main) {
  background: linear-gradient(135deg, #22f6ff 0%, #00a8ff 100%) !important;
  border: none !important;
  color: #04111c !important;
  font-weight: 700 !important;
  padding: 12px 32px !important;
  border-radius: 100px !important;
  width: 100% !important;
}

:deep(.infuse-btn-cancel-main) {
  background: transparent !important;
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
  color: var(--infuse-text-muted) !important;
  margin-top: 10px !important;
  width: 100% !important;
}

/* 字幕项样式 */
.subtitle-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 12px;
  margin-bottom: 10px;
  border: 1px solid transparent;
  transition: all 0.2s;
}

.subtitle-item:hover {
  background: rgba(255, 255, 255, 0.06);
  border-color: var(--infuse-accent);
}

.subtitle-rank {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 13px;
}

.subtitle-rank.excellent { background: rgba(52, 199, 89, 0.2); color: #34c759; }
.subtitle-rank.good { background: rgba(0, 113, 227, 0.2); color: #0071e3; }
.subtitle-rank.fair { background: rgba(255, 149, 0, 0.2); color: #ff9500; }
.subtitle-rank.poor { background: rgba(255, 59, 48, 0.2); color: #ff3b30; }

.subtitle-info {
  flex: 1;
  min-width: 0;
}

.subtitle-title {
  font-weight: 600;
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.subtitle-meta {
  display: flex;
  gap: 10px;
  font-size: 11px;
}

.source-tag {
  color: var(--infuse-accent);
  font-weight: 700;
}

.subhd-filename {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 6px 0;
  padding: 6px 10px;
  background: rgba(34, 246, 255, 0.05);
  border-radius: 6px;
  border-left: 3px solid var(--infuse-accent);
}

.subhd-filename .filename-text {
  font-size: 11px;
  color: var(--infuse-text-muted);
  overflow: hidden;
  text-overflow: ellipsis;
}

.action-btn.danger {
  background: rgba(255, 59, 48, 0.15);
  color: #ff3b30;
}

.action-btn.danger:hover {
  background: #ff3b30;
  color: white;
}
</style>
