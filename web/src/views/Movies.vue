<template>
  <div class="movies">
    <header class="page-header">
      <h1 class="page-title">电影</h1>
      <p class="page-subtitle">{{ filteredMovies.length }} 部影片</p>
    </header>

    <div class="toolbar">
      <div class="search-box">
        <el-input
          v-model="searchQuery"
          placeholder="搜索电影..."
          clearable
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </div>
      <div class="filter-group">
        <el-select v-model="filterStatus" placeholder="筛选状态" clearable>
          <el-option label="全部" value="" />
          <el-option label="有字幕" value="with" />
          <el-option label="无字幕" value="without" />
        </el-select>
        <button class="infuse-button" @click="handleScan">
          <el-icon><Refresh /></el-icon>
          扫描
        </button>
      </div>
    </div>

    <div class="movies-grid">
      <div
        v-for="movie in filteredMovies"
        :key="movie.id"
        class="movie-card"
        @click="handleMovieClick(movie)"
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
            {{ movie.hasSubtitle ? '✓' : '无字幕' }}
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
            <p>{{ currentMovie.filename }}</p>
            <div class="header-meta">
              <span v-if="currentMovie.year">{{ currentMovie.year }}</span>
              <span v-if="currentMovie.resolution">{{ currentMovie.resolution }}</span>
            </div>
          </div>
        </div>

        <div class="search-results" v-loading="searching">
          <div v-if="searchResults.length === 0 && !searching" class="empty-results">
            <div class="empty-icon">
              <el-icon><Search /></el-icon>
            </div>
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
        <button class="infuse-button secondary" @click="searchDialogVisible = false">关闭</button>
        <button class="infuse-button" @click="handleDoSearch" :disabled="searching">
          <el-icon v-if="!searching"><Search /></el-icon>
          <span v-else class="loading-spinner"></span>
          {{ searching ? '搜索中...' : '搜索' }}
        </button>
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
            <p>{{ currentMovie.filename }}</p>
            <div class="header-meta">
              <span v-if="currentMovie.year">{{ currentMovie.year }}</span>
              <span v-if="currentMovie.resolution">{{ currentMovie.resolution }}</span>
            </div>
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
            <button class="infuse-button" @click="switchToSearch">
              <el-icon><Search /></el-icon>
              搜索字幕
            </button>
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
        <button class="infuse-button secondary" @click="manageDialogVisible = false">关闭</button>
        <button class="infuse-button" @click="switchToSearch">
          <el-icon><Search /></el-icon>
          搜索新字幕
        </button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useSubtitleStore } from '../stores/subtitle'
import { ElMessage } from 'element-plus'
import { Search, Refresh, Film, Check, Download, Document, Delete } from '@element-plus/icons-vue'
import axios from 'axios'

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
const isMobileView = ref(false)

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

function updateViewportState() {
  isMobileView.value = window.matchMedia('(max-width: 768px)').matches
}

function hasMediaArt(media) {
  return Boolean(media?.posterPath || media?.fanartPath)
}

function getMovieArtUrl(movie) {
  if (!movie?.id) return ''
  const preferred = isMobileView.value ? 'fanart' : 'poster'
  return `/api/art/movie/${movie.id}?preferred=${preferred}`
}

onMounted(async () => {
  updateViewportState()
  window.addEventListener('resize', updateViewportState)

  try {
    await store.fetchMovies()
    movies.value = store.movies
  } catch (error) {
    ElMessage.error('获取电影列表失败')
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', updateViewportState)
})

function handleMovieClick(movie) {
  console.log('Clicked movie:', movie)
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
    console.error(error)
    movieSubtitles.value = []
  } finally {
    loadingSubtitles.value = false
  }
}

async function handleDeleteSubtitle(subtitle) {
  try {
    deletingSubtitle.value = subtitle.path
    await api.post('/subtitles/delete', {
      subtitlePath: subtitle.path
    })
    ElMessage.success('字幕已删除')
    await loadMovieSubtitles()
    // 刷新电影列表以更新字幕状态
    await store.fetchMovies()
    movies.value = store.movies
  } catch (error) {
    ElMessage.error('删除字幕失败')
    console.error(error)
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
  return (value || '')
    .toLowerCase()
    .replace(/[.\-_()[\]{}]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
}

function shouldShowSubhdFilename(result) {
  if (!result?.filename) return false
  return normalizeSubtitleLabel(result.filename) !== normalizeSubtitleLabel(result.title)
}

function markMovieHasSubtitle(movieId, hasSubtitle = true) {
  const target = movies.value.find(movie => movie.id === movieId)
  if (target) {
    target.hasSubtitle = hasSubtitle
  }
  if (currentMovie.value?.id === movieId) {
    currentMovie.value = {
      ...currentMovie.value,
      hasSubtitle
    }
  }
}

async function handleDoSearch() {
  if (!currentMovie.value) return

  searching.value = true
  try {
    const response = await api.post(`/movies/${currentMovie.value.id}/search-subtitles`)
    // 按匹配度降序排序
    searchResults.value = response.data.sort((a, b) => b.score - a.score)
    if (searchResults.value.length === 0) {
      ElMessage.info('未找到匹配的字幕')
    }
  } catch (error) {
    ElMessage.error('搜索失败')
    console.error(error)
  } finally {
    searching.value = false
  }
}

async function handleDownload(result) {
  downloading.value = result.id
  try {
    // 构建请求参数
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
    ElMessage.info('开始扫描...')
    await api.post('/scan')
    ElMessage.success('扫描任务已启动')
    setTimeout(async () => {
      await store.fetchMovies()
      movies.value = store.movies
    }, 3000)
  } catch (error) {
    ElMessage.error('扫描失败')
  }
}

function handlePosterError(event) {
  event.target.style.display = 'none'
}
</script>

<style scoped>
.movies {
  max-width: 1600px;
}

.page-header {
  margin-bottom: 32px;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
  gap: 16px;
  padding: 18px 20px;
  border: 1px solid var(--infuse-border);
  border-radius: var(--infuse-radius-lg);
  background: rgba(8, 14, 34, 0.62);
  backdrop-filter: blur(18px);
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.03);
}

.search-box {
  width: 320px;
}

.filter-group {
  display: flex;
  gap: 12px;
  align-items: center;
}

.filter-group .el-select {
  min-width: 120px;
}

.movies-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 24px;
}

.movie-card {
  cursor: pointer;
  transition: transform var(--infuse-transition-slow);
  position: relative;
}

.movie-card:hover {
  transform: translateY(-6px) scale(1.015);
}

.movie-poster {
  position: relative;
  aspect-ratio: 2/3;
  background: linear-gradient(145deg, rgba(11, 20, 48, 0.92), rgba(8, 13, 30, 0.96));
  border-radius: var(--infuse-radius-lg);
  overflow: hidden;
  box-shadow: var(--infuse-shadow-md);
  transition: box-shadow var(--infuse-transition-normal);
  border: 1px solid rgba(119, 247, 255, 0.12);
}

.movie-poster::before {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(34, 246, 255, 0.14), transparent 32%, rgba(255, 43, 214, 0.14));
  opacity: 0;
  transition: opacity var(--infuse-transition-normal);
  z-index: 1;
  pointer-events: none;
}

.movie-card:hover .movie-poster {
  box-shadow: var(--infuse-shadow-glow), var(--infuse-shadow-lg);
}

.movie-card:hover .movie-poster::before {
  opacity: 1;
}

.poster-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform var(--infuse-transition-slow);
}

.movie-card:hover .poster-image {
  transform: scale(1.05);
}

.poster-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 64px;
  color: var(--infuse-text-muted);
  background: linear-gradient(145deg, var(--infuse-bg-tertiary) 0%, var(--infuse-bg-hover) 100%);
}

.poster-overlay {
  position: absolute;
  inset: 0;
  background:
    linear-gradient(180deg, rgba(6, 10, 26, 0.02) 0%, rgba(6, 10, 26, 0.66) 58%, rgba(6, 10, 26, 0.98) 100%),
    radial-gradient(circle at top right, rgba(34, 246, 255, 0.18), transparent 36%);
  opacity: 0;
  transition: opacity var(--infuse-transition-normal);
  display: flex;
  align-items: flex-end;
  justify-content: center;
  padding: 20px;
}

.movie-card:hover .poster-overlay {
  opacity: 1;
}

.movie-actions {
  transform: translateY(20px);
  opacity: 0;
  transition: all var(--infuse-transition-normal);
}

.movie-card:hover .movie-actions {
  transform: translateY(0);
  opacity: 1;
}

.action-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  border-radius: 100px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--infuse-transition-fast);
  border: none;
}

.action-btn.primary {
  background: linear-gradient(135deg, rgba(34,246,255,0.92), rgba(255,43,214,0.9));
  color: #07101a;
}

.action-btn.primary:hover {
  background: var(--infuse-accent-hover);
  box-shadow: var(--infuse-shadow-glow);
}

.action-btn.secondary {
  background: rgba(8, 16, 38, 0.66);
  color: var(--infuse-text-primary);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(119, 247, 255, 0.14);
}

.action-btn.secondary:hover {
  background: rgba(255, 255, 255, 0.25);
}

.action-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.subtitle-badge {
  position: absolute;
  top: 12px;
  right: 12px;
  min-width: 32px;
  height: 32px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  background: rgba(255, 43, 214, 0.86);
  color: white;
  backdrop-filter: blur(10px);
  padding: 0 10px;
  white-space: nowrap;
  box-shadow: 0 0 18px rgba(255, 43, 214, 0.18);
}

.subtitle-badge.has {
  background: rgba(34, 246, 255, 0.84);
  color: #07101a;
  box-shadow: 0 0 18px rgba(34, 246, 255, 0.18);
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
  text-overflow: ellipsis;
  max-height: 2.8em;
}

.movie-meta {
  display: flex;
  gap: 8px;
}

.meta-item {
  font-size: 12px;
  color: var(--infuse-text-secondary);
  background: rgba(11, 18, 42, 0.76);
  padding: 4px 10px;
  border-radius: 100px;
  font-weight: 500;
  border: 1px solid rgba(119, 247, 255, 0.1);
}

/* 搜索对话框样式 */
.search-dialog-content {
  min-height: 400px;
}

.movie-info-header {
  display: flex;
  gap: 20px;
  padding: 20px;
  background: rgba(10, 16, 38, 0.72);
  border-radius: var(--infuse-radius-lg);
  margin-bottom: 24px;
  border: 1px solid var(--infuse-border);
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.04);
}

.header-poster {
  width: 80px;
  height: 120px;
  border-radius: var(--infuse-radius-md);
  overflow: hidden;
  flex-shrink: 0;
}

.header-poster img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.header-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.header-info h3 {
  font-size: 20px;
  font-weight: 700;
  color: var(--infuse-text-primary);
  margin-bottom: 8px;
}

.header-info p {
  font-size: 13px;
  color: var(--infuse-text-tertiary);
  margin-bottom: 12px;
}

.header-meta {
  display: flex;
  gap: 12px;
}

.header-meta span {
  font-size: 13px;
  color: var(--infuse-text-secondary);
  background: var(--infuse-bg-hover);
  padding: 4px 12px;
  border-radius: 100px;
}

.search-results {
  min-height: 300px;
}

.empty-results {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  color: var(--infuse-text-muted);
}

.empty-icon {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: var(--infuse-bg-tertiary);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 20px;
}

.empty-icon .el-icon {
  font-size: 36px;
}

.subtitle-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 20px;
  background: rgba(10, 16, 38, 0.74);
  border-radius: var(--infuse-radius-md);
  margin-bottom: 12px;
  border: 1px solid var(--infuse-border);
  transition: all var(--infuse-transition-fast);
}

.subtitle-item:hover {
  border-color: var(--infuse-border-hover);
  background: rgba(18, 29, 62, 0.88);
}

.subtitle-rank {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 700;
  flex-shrink: 0;
}

.subtitle-rank.excellent {
  background: rgba(34, 197, 94, 0.15);
  color: #22c55e;
}

.subtitle-rank.good {
  background: rgba(59, 130, 246, 0.15);
  color: #3b82f6;
}

.subtitle-rank.fair {
  background: rgba(245, 158, 11, 0.15);
  color: #f59e0b;
}

.subtitle-rank.poor {
  background: rgba(107, 114, 128, 0.15);
  color: #6b7280;
}

.subtitle-info {
  flex: 1;
  min-width: 0;
}

.subtitle-title {
  font-weight: 600;
  color: var(--infuse-text-primary);
  margin-bottom: 8px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.subtitle-meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.source-tag, .lang-tag {
  font-size: 11px;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 100px;
  text-transform: uppercase;
}

.source-tag {
  background: var(--infuse-accent-glow);
  color: var(--infuse-accent);
}

.source-tag.shooter {
  background: rgba(59, 130, 246, 0.15);
  color: #3b82f6;
}

.source-tag.assrt {
  background: rgba(139, 92, 246, 0.15);
  color: #8b5cf6;
}

.source-tag.opensubtitles {
  background: rgba(245, 158, 11, 0.15);
  color: #f59e0b;
}

.lang-tag {
  background: var(--infuse-bg-hover);
  color: var(--infuse-text-secondary);
}

.loading-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 768px) {
  .toolbar {
    flex-direction: column;
    align-items: stretch;
    gap: 14px;
  }

  .search-box {
    width: 100%;
  }

  .filter-group {
    width: 100%;
    flex-wrap: wrap;
  }

  .filter-group > * {
    flex: 1 1 100%;
  }

  .movies-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
  }

  .movie-card {
    min-width: 0;
  }

  .movie-title {
    font-size: 14px;
  }

  .movie-info-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .header-poster {
    width: 112px;
  }

  .subtitle-item,
  .subtitle-file-item {
    flex-direction: column;
    align-items: flex-start;
  }

  .subtitle-rank,
  .file-icon {
    width: 48px;
    height: 48px;
  }

  .action-btn {
    width: 100%;
    justify-content: center;
  }

  .section-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
}

@media (max-width: 560px) {
  .movies-grid {
    grid-template-columns: 1fr;
  }

  .movie-poster {
    aspect-ratio: 16 / 9;
  }
}

/* 字幕管理对话框样式 */
.manage-dialog-content {
  min-height: 400px;
}

.subtitles-section {
  margin-top: 24px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-header h4 {
  font-size: 16px;
  font-weight: 600;
  color: var(--infuse-text-primary);
}

.subtitle-count {
  font-size: 13px;
  color: var(--infuse-text-secondary);
  background: var(--infuse-bg-tertiary);
  padding: 4px 12px;
  border-radius: 100px;
}

.loading-subtitles {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 60px 20px;
  color: var(--infuse-text-muted);
}

.empty-subtitles {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: var(--infuse-text-muted);
}

.empty-subtitles .el-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.empty-subtitles p {
  margin-bottom: 20px;
}

.subtitles-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.subtitle-file-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 20px;
  background: var(--infuse-bg-tertiary);
  border-radius: var(--infuse-radius-md);
  border: 1px solid var(--infuse-border);
  transition: all var(--infuse-transition-fast);
}

.subtitle-file-item:hover {
  border-color: var(--infuse-border-hover);
  background: var(--infuse-bg-hover);
}

.file-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: var(--infuse-accent-glow);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.file-icon .el-icon {
  font-size: 24px;
  color: var(--infuse-accent);
}

.file-info {
  flex: 1;
  min-width: 0;
}

.file-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--infuse-text-primary);
  margin-bottom: 6px;
  word-break: break-all;
}

.file-meta {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.format-tag {
  font-size: 11px;
  color: var(--infuse-text-tertiary);
  background: var(--infuse-bg-hover);
  padding: 2px 8px;
  border-radius: 4px;
}

.size-tag {
  font-size: 11px;
  color: var(--infuse-text-tertiary);
  background: var(--infuse-bg-hover);
  padding: 2px 8px;
  border-radius: 4px;
}

.action-btn.danger {
  background: rgba(239, 68, 68, 0.9);
  color: white;
}

.action-btn.danger:hover {
  background: rgba(239, 68, 68, 1);
  box-shadow: 0 0 20px rgba(239, 68, 68, 0.3);
}

/* SubHD 文件名显示样式 */
.subhd-filename {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 6px 0;
  padding: 6px 10px;
  background: rgba(59, 130, 246, 0.1);
  border-radius: 6px;
  border-left: 3px solid #3b82f6;
}

.subhd-filename .el-icon {
  font-size: 14px;
  color: #3b82f6;
  flex-shrink: 0;
}

.subhd-filename .filename-text {
  font-size: 12px;
  color: var(--infuse-text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-family: 'SF Mono', Monaco, monospace;
}

.subhd-summary {
  margin-bottom: 8px;
  font-size: 12px;
  color: var(--infuse-text-secondary);
  line-height: 1.5;
}

.subhd-meta-tag {
  padding: 4px 10px;
  border-radius: 100px;
  font-size: 11px;
  font-weight: 600;
  color: #c084fc;
  background: rgba(192, 132, 252, 0.14);
  border: 1px solid rgba(192, 132, 252, 0.2);
}

.source-tag.subhd {
  background: rgba(59, 130, 246, 0.15);
  color: #3b82f6;
}
</style>
