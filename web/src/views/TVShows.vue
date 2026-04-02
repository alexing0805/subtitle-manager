<template>
  <div
    class="tv-shows page-shell"
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
      <h1 class="page-title">电视剧</h1>
      <p class="page-subtitle">管理电视剧字幕</p>
    </header>

    <!-- 工具栏 -->
    <div class="toolbar infuse-card">
      <div class="search-box">
        <el-input
          v-model="searchQuery"
          placeholder="搜索电视剧..."
          prefix-icon="Search"
          clearable
        />
      </div>
      <div class="filter-group">
        <el-radio-group v-model="displayMode" class="display-mode-toggle">
          <el-radio-button label="compact">紧凑模式</el-radio-button>
          <el-radio-button label="wide">宽幅模式</el-radio-button>
        </el-radio-group>
        <el-button type="primary" class="infuse-btn-primary" @click="handleBatchUpload">
          <el-icon><Upload /></el-icon>
          批量上传字幕
        </el-button>
        <el-button class="infuse-btn-default scan-btn" @click="handleScan">
          <el-icon><Refresh /></el-icon>
          扫描
        </el-button>
      </div>
    </div>

    <!-- 电视剧网格 -->
    <div class="shows-grid">
      <div
        v-for="show in filteredShows"
        :key="show.id"
        class="show-card infuse-card infuse-tilt"
        @click="handleShowClick(show)"
        @mousemove="handleTiltMove"
        @mouseleave="handleTiltLeave"
      >
        <div class="show-poster">
          <img
            v-if="hasMediaArt(show)"
            :src="getShowArtUrl(show)"
            :alt="show.name"
            class="poster-image"
            @error="handlePosterError"
          />
          <div v-else class="poster-placeholder">
            <el-icon><Monitor /></el-icon>
          </div>
          <div class="poster-overlay">
            <div class="show-actions">
              <button
                v-if="show.subtitleStats.missing > 0"
                class="action-btn primary"
                @click.stop="handleSearchShow(show)"
              >
                <el-icon><Search /></el-icon>
                搜索字幕
              </button>
              <button
                v-else
                class="action-btn secondary"
                @click.stop="handleManageShow(show)"
              >
                <el-icon><Check /></el-icon>
                管理字幕
              </button>
            </div>
          </div>
          <div class="subtitle-badge" :class="{ has: show.subtitleStats.missing === 0 }">
            {{ show.subtitleStats.missing === 0 ? '✓' : show.subtitleStats.missing }}
          </div>
        </div>
        <div class="show-info">
          <h3 class="show-title">{{ show.name }}</h3>
          <div class="show-meta">
            <span v-if="show.year" class="meta-item">{{ show.year }}</span>
            <span class="meta-item">{{ show.seasonCount }} 季</span>
            <span class="meta-item">{{ show.episodeCount }} 集</span>
          </div>
          <div class="show-stats-bar">
            <div class="stats-progress">
              <div
                class="progress-fill"
                :style="{ width: `${(show.subtitleStats.has / show.episodeCount) * 100}%` }"
              ></div>
            </div>
            <span class="stats-text">{{ show.subtitleStats.has }}/{{ show.episodeCount }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 电视剧详情对话框 -->
    <el-dialog
      v-model="showDetailVisible"
      :title="currentShow?.name"
      width="900px"
      destroy-on-close
      class="infuse-dialog"
    >
      <div v-if="currentShow" class="show-detail">
        <div class="detail-header">
          <div class="detail-poster">
            <img
              v-if="hasMediaArt(currentShow)"
              :src="getShowArtUrl(currentShow)"
              :alt="currentShow.name"
              class="poster-image"
              @error="handlePosterError"
            />
            <div v-else class="poster-placeholder large">
              <el-icon><Monitor /></el-icon>
            </div>
          </div>
          <div class="detail-info">
            <h2>{{ currentShow.name }}</h2>
            <div class="detail-meta">
              <span v-if="currentShow.year">{{ currentShow.year }}</span>
              <span>{{ currentShow.seasonCount }} 季</span>
              <span>{{ currentShow.episodeCount }} 集</span>
            </div>
            <div class="detail-stats">
              <div class="stat-box has">
                <span class="stat-number">{{ currentShow.subtitleStats.has }}</span>
                <span class="stat-label">有字幕</span>
              </div>
              <div class="stat-box missing">
                <span class="stat-number">{{ currentShow.subtitleStats.missing }}</span>
                <span class="stat-label">无字幕</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 季标签和缩略图 -->
        <div class="seasons-section">
          <div class="seasons-tabs">
            <div
              v-for="season in currentShow.seasons"
              :key="season.number"
              class="season-tab"
              :class="{ active: activeSeasonTab === season.number }"
              @click="activeSeasonTab = season.number"
            >
              第 {{ season.number }} 季
              <span class="episode-count">({{ season.episodes.length }} 集)</span>
            </div>
          </div>
          
          <!-- 当前季缩略图 -->
          <div class="current-season-poster" v-if="currentSeasonPoster">
            <img
              :src="getSeasonPosterUrl(currentSeasonPoster)"
              :alt="`第 ${activeSeasonTab} 季`"
              class="season-poster-image"
              @error="handleSeasonPosterError"
            />
          </div>
        </div>

        <!-- 剧集列表 -->
        <div class="episodes-list">
          <div
            v-for="episode in currentSeasonEpisodes"
            :key="episode.id"
            class="episode-item"
          >
            <div class="episode-number">E{{ String(episode.episodeNumber).padStart(2, '0') }}</div>
            <div class="episode-info">
              <div class="episode-title">{{ episode.name || `第 ${episode.episodeNumber} 集` }}</div>
              <div class="episode-filename">{{ episode.filename }}</div>
            </div>
            <div class="episode-status">
              <el-tag
                :type="episode.hasSubtitle ? 'success' : 'warning'"
                size="small"
                effect="dark"
              >
                {{ episode.hasSubtitle ? '有字幕' : '无字幕' }}
              </el-tag>
            </div>
            <div class="episode-actions">
              <el-button
                v-if="!episode.hasSubtitle"
                type="primary"
                size="small"
                class="infuse-btn-primary"
                @click="handleSearchEpisode(episode)"
              >
                <el-icon><Search /></el-icon>
                搜索
              </el-button>
              <el-button
                v-else
                size="small"
                class="infuse-btn-default"
                @click="handleManageEpisode(episode)"
              >
                <el-icon><Setting /></el-icon>
                管理
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </el-dialog>

    <!-- 字幕搜索对话框 -->
    <el-dialog
      v-model="searchDialogVisible"
      title="搜索字幕"
      width="700px"
      destroy-on-close
      class="infuse-dialog"
    >
      <div v-if="currentEpisode" class="search-dialog-content">
        <div class="episode-info-header">
          <div class="episode-poster">
            <img
              v-if="hasMediaArt(currentShow)"
              :src="getShowArtUrl(currentShow)"
              class="poster-thumb"
            />
            <div v-else class="poster-thumb-placeholder">
              <el-icon><Monitor /></el-icon>
            </div>
          </div>
          <div class="episode-details">
            <h3>{{ currentShow?.name }}</h3>
            <p class="episode-code">S{{ String(activeSeasonTab || 1).padStart(2, '0') }}E{{ String(currentEpisode.episodeNumber).padStart(2, '0') }}</p>
            <p class="episode-file">{{ currentEpisode.filename }}</p>
          </div>
        </div>

        <div class="search-results" v-loading="searching">
          <div v-if="!hasSearched && searchResults.length === 0 && !searching" class="empty-results">
            <el-icon class="empty-icon"><InfoFilled /></el-icon>
            <p>点击搜索按钮开始查找字幕</p>
          </div>
          <div v-if="hasSearched && searchResults.length === 0 && !searching" class="empty-results">
            <el-icon class="empty-icon"><InfoFilled /></el-icon>
            <p>未找到匹配的字幕</p>
          </div>

          <div
            v-for="result in searchResults"
            :key="result.id"
            class="subtitle-item"
          >
            <div class="subtitle-rank" :class="getRankClass(result.score)">
              <small>匹配</small>
              <strong>{{ (result.score * 100).toFixed(0) }}%</strong>
            </div>
            <div class="subtitle-info">
              <div class="subtitle-title">{{ result.title }}</div>
              <SubtitleQualityBadge :result="result" compact />
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

    <ScanVisualization
      v-model:visible="scanVisualizationVisible"
      title="电视剧库扫描可视化"
      :status="store.scanStatus"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { useSubtitleStore } from '../stores/subtitle'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, Upload, Monitor, Check, Setting, InfoFilled, Document, Download } from '@element-plus/icons-vue'
import axios from 'axios'
import { useAmbientEffects } from '../composables/useAmbientEffects'
import { useMediaDisplayMode } from '../composables/useMediaDisplayMode'
import { buildScanConfirmHtml, createScanDialogOptions } from '../utils/scanDialog'
import ScanVisualization from '../components/ScanVisualization.vue'
import SubtitleQualityBadge from '../components/SubtitleQualityBadge.vue'

const api = axios.create({
  baseURL: '/api',
  timeout: 60000  // 增加到60秒
})

const router = useRouter()
const store = useSubtitleStore()
const searchQuery = ref('')
const shows = ref([])
const {
  containerRef,
  particles,
  parallaxStyle,
  mouseGlowStyle,
  handleMouseMove,
  handleMouseLeave,
  handleTiltMove,
  handleTiltLeave
} = useAmbientEffects({ particleCount: 20, parallaxFactor: 0.005 })

// 详情对话框
const showDetailVisible = ref(false)
const currentShow = ref(null)
const activeSeasonTab = ref(1)

// 字幕搜索相关
const searchDialogVisible = ref(false)
const currentEpisode = ref(null)
const searchResults = ref([])
const searching = ref(false)
const downloading = ref(null)
const hasSearched = ref(false)  // 记录是否已经搜索过
const scanVisualizationVisible = ref(false)
let scanPollTimer = null
const { displayMode, artPreference } = useMediaDisplayMode()

const filteredShows = computed(() => {
  if (!searchQuery.value) return shows.value
  const query = searchQuery.value.toLowerCase()
  return shows.value.filter(s => s.name.toLowerCase().includes(query))
})

const currentSeasonEpisodes = computed(() => {
  if (!currentShow.value) return []
  const season = currentShow.value.seasons.find(s => s.number === activeSeasonTab.value)
  return season ? season.episodes : []
})

// 当前季的海报路径
const currentSeasonPoster = computed(() => {
  if (!currentShow.value) return null
  const season = currentShow.value.seasons.find(s => s.number === activeSeasonTab.value)
  return season?.posterPath || null
})

// 获取季海报URL
function getSeasonPosterUrl(posterPath) {
  if (!posterPath) return ''
  // 使用API端点获取海报
  return `/api/poster/tvshow/${currentShow.value?.id}/season/${activeSeasonTab.value}`
}

// 处理季海报加载错误
function handleSeasonPosterError(e) {
  e.target.style.display = 'none'
}

function hasMediaArt(media) {
  return Boolean(media?.posterPath || media?.fanartPath)
}

function getShowArtUrl(show) {
  if (!show?.id) return ''
  return `/api/art/tvshow/${show.id}?preferred=${artPreference.value}`
}

onMounted(async () => {
  try {
    await store.fetchTVShows()
    shows.value = store.tvShows
  } catch (error) {
    ElMessage.error('获取电视剧列表失败')
  }
})

onBeforeUnmount(() => {
  stopScanPolling()
})

function handleShowClick(show) {
  currentShow.value = show
  activeSeasonTab.value = show.seasons[0]?.number || 1
  showDetailVisible.value = true
}

function handleSearchShow(show) {
  currentShow.value = show
  activeSeasonTab.value = show.seasons[0]?.number || 1
  showDetailVisible.value = true
}

function handleManageShow(show) {
  currentShow.value = show
  activeSeasonTab.value = show.seasons[0]?.number || 1
  showDetailVisible.value = true
}

function handleSearchEpisode(episode) {
  currentEpisode.value = episode
  searchDialogVisible.value = true
  searchResults.value = []
  hasSearched.value = false  // 重置搜索状态
}

function handleManageEpisode(episode) {
  // 管理字幕也打开搜索对话框，允许搜索更多字幕
  currentEpisode.value = episode
  searchDialogVisible.value = true
  searchResults.value = []
  hasSearched.value = false  // 重置搜索状态
}

function handleBatchUpload() {
  router.push('/batch-upload')
}

async function handleDoSearch() {
  if (!currentEpisode.value) {
    ElMessage.warning('请先选择一个剧集')
    return
  }

  searching.value = true
  hasSearched.value = true  // 标记已经搜索过
  searchResults.value = [] // 清空之前的结果

  try {
    const url = `/episodes/${currentEpisode.value.id}/search-subtitles`
    const response = await api.post(url)

    if (Array.isArray(response.data)) {
      // 按匹配度降序排序
      searchResults.value = response.data.sort((a, b) => b.score - a.score)

      if (searchResults.value.length === 0) {
        ElMessage.info('未找到匹配的字幕')
      } else {
        ElMessage.success(`找到 ${searchResults.value.length} 个字幕`)
      }
    } else {
      ElMessage.error('返回数据格式错误')
    }
  } catch (error) {
    ElMessage.error('搜索失败: ' + (error.message || '未知错误'))
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
        filename: result.filename,
        votes: result.votes,
        downloadCount: result.downloadCount,
        rating: result.rating
      }
    }
    await api.post(`/episodes/${currentEpisode.value.id}/download-subtitle`, requestData)
    ElMessage.success('字幕下载成功')
    searchDialogVisible.value = false
    markEpisodeHasSubtitle(currentEpisode.value.id, true)
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
        title: '确认扫描电视剧库',
        description: '系统将同步剧集目录、重建季集索引，并刷新缺失字幕统计。',
        steps: ['扫描剧集文件', '重建季集索引', '更新字幕缺失状态']
      }),
      '',
      createScanDialogOptions('扫描中...')
    )
    
    ElMessage.info({ message: '正在启动电视剧库扫描任务...', customClass: 'infuse-message' })
    const result = await store.scanLibrary()
    
    if (result && result.success === false) {
      throw new Error(result.message || '扫描任务提交失败')
    }
    
    scanVisualizationVisible.value = true
    startScanPolling(async () => {
      await store.fetchTVShows()
      shows.value = store.tvShows
      ElMessage.success({ message: '电视剧库数据已同步更新', customClass: 'infuse-message' })
    })

    ElMessage.success({ message: '扫描任务已成功提交，正在展开扫描树...', customClass: 'infuse-message' })

  } catch (error) {
    if (error === 'cancel' || error === 'close' || error === '') return
    console.error('Scan Error:', error)
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

function handlePosterError(e) {
  e.target.style.display = 'none'
  e.target.nextElementSibling?.classList.add('show-placeholder')
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

function markEpisodeHasSubtitle(episodeId, hasSubtitle = true) {
  for (const show of shows.value) {
    let updated = false
    let totalEpisodes = 0
    let episodesWithSubtitle = 0

    for (const season of show.seasons || []) {
      for (const episode of season.episodes || []) {
        if (episode.id === episodeId) {
          episode.hasSubtitle = hasSubtitle
          updated = true
        }
        totalEpisodes += 1
        if (episode.hasSubtitle) {
          episodesWithSubtitle += 1
        }
      }
    }

    if (updated) {
      show.subtitleStats = {
        ...show.subtitleStats,
        has: episodesWithSubtitle,
        missing: totalEpisodes - episodesWithSubtitle
      }
      if (currentShow.value?.id === show.id) {
        currentShow.value = { ...show }
      }
      if (currentEpisode.value?.id === episodeId) {
        currentEpisode.value = { ...currentEpisode.value, hasSubtitle }
      }
      return
    }
  }
}
</script>

<style scoped>
.tv-shows {
  max-width: 1400px;
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
  0% {
    transform: translateY(0) scale(1);
    opacity: 0;
  }
  10% { opacity: 1; }
  90% { opacity: 1; }
  100% {
    transform: translateY(-100vh) scale(0.5);
    opacity: 0;
  }
}

/* 页面标题 */
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
  font-weight: 400;
}

/* 工具栏 */
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  margin-bottom: 40px;
  background: rgba(8, 14, 34, 0.62);
  border: 1px solid var(--infuse-border);
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

/* 扫描按钮特殊样式 */
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

/* Infuse 按钮 */
.infuse-btn-primary {
  background: var(--infuse-accent) !important;
  border-color: var(--infuse-accent) !important;
  color: #fff !important;
}

.infuse-btn-primary:hover {
  background: var(--infuse-accent-hover) !important;
  border-color: var(--infuse-accent-hover) !important;
}

.infuse-btn-default {
  background: var(--infuse-bg-card) !important;
  border-color: var(--infuse-border) !important;
  color: var(--infuse-text-primary) !important;
}

.infuse-btn-default:hover {
  border-color: var(--infuse-accent) !important;
  color: var(--infuse-accent) !important;
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

/* 电视剧网格 */
.shows-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 32px;
  position: relative;
  z-index: 1;
}

.display-mode-wide .shows-grid {
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
}

.show-card {
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.165, 0.84, 0.44, 1);
  position: relative;
  transform-style: preserve-3d;
  will-change: transform;
}

/* 海报 */
.show-poster {
  position: relative;
  aspect-ratio: 2/3;
  overflow: hidden;
  background: linear-gradient(145deg, rgba(11, 20, 48, 0.92), rgba(8, 13, 30, 0.96));
  border: 1px solid rgba(119, 247, 255, 0.12);
  border-radius: var(--infuse-radius-lg);
}

.display-mode-wide .show-poster {
  aspect-ratio: 16 / 9;
}

.show-poster::before {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(34, 246, 255, 0.14), transparent 32%, rgba(255, 43, 214, 0.14));
  opacity: 0;
  transition: opacity var(--infuse-transition-normal);
  z-index: 1;
  pointer-events: none;
}

.poster-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.6s cubic-bezier(0.165, 0.84, 0.44, 1);
}

.show-card:hover .poster-image {
  transform: scale(1.08);
}

.show-card:hover .show-poster::before {
  opacity: 1;
}

.poster-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  font-size: 48px;
}

.poster-overlay {
  position: absolute;
  inset: 0;
  background:
    linear-gradient(180deg, rgba(6, 10, 26, 0.02) 0%, rgba(6, 10, 26, 0.66) 58%, rgba(6, 10, 26, 0.98) 100%),
    radial-gradient(circle at top right, rgba(34, 246, 255, 0.18), transparent 36%);
  display: flex;
  align-items: flex-end;
  justify-content: center;
  padding: 20px;
  opacity: 0;
  transition: opacity var(--infuse-transition-normal);
}

.show-card:hover .poster-overlay {
  opacity: 1;
}

.show-actions {
  display: flex;
  gap: 8px;
  transform: translateY(10px);
  transition: transform var(--infuse-transition-normal);
}

.show-card:hover .show-actions {
  transform: translateY(0);
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 16px;
  border-radius: var(--infuse-radius-md);
  border: none;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--infuse-transition-fast);
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

/* 字幕徽章 */
.subtitle-badge {
  position: absolute;
  top: 12px;
  right: 12px;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: rgba(255, 43, 214, 0.86);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  box-shadow: 0 4px 12px rgba(255, 43, 214, 0.3);
}

.subtitle-badge.has {
  background: rgba(34, 246, 255, 0.84);
  color: #07101a;
  box-shadow: 0 4px 12px rgba(34, 246, 255, 0.3);
}

/* 剧集信息 */
.show-info {
  padding: 16px;
}

.show-title {
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

.show-meta {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.meta-item {
  font-size: 11px;
  color: var(--infuse-text-secondary);
  background: rgba(11, 18, 42, 0.76);
  padding: 2px 8px;
  border-radius: 4px;
  border: 1px solid rgba(119, 247, 255, 0.1);
}

/* 进度条 */
.show-stats-bar {
  display: flex;
  align-items: center;
  gap: 10px;
}

.stats-progress {
  flex: 1;
  height: 4px;
  background: var(--infuse-bg-tertiary);
  border-radius: 2px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--infuse-accent), var(--infuse-accent-hover));
  border-radius: 2px;
  transition: width var(--infuse-transition-slow);
}

.stats-text {
  font-size: 11px;
  color: var(--infuse-text-muted);
  font-weight: 500;
}

/* 详情对话框 */
:deep(.infuse-dialog) {
  background: var(--infuse-bg-secondary);
  border-radius: 20px;
  border: 1px solid var(--infuse-border);
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
}

:deep(.infuse-dialog .el-dialog__header) {
  border-bottom: 1px solid var(--infuse-border);
  padding: 24px 32px;
}

:deep(.infuse-dialog .el-dialog__title) {
  color: var(--infuse-text-primary);
  font-weight: 700;
  font-size: 20px;
}

:deep(.infuse-dialog .el-dialog__body) {
  padding: 32px;
  color: var(--infuse-text-primary);
}

/* 详情头部 */
.detail-header {
  display: flex;
  gap: 24px;
  margin-bottom: 32px;
}

.detail-poster {
  width: 150px;
  flex-shrink: 0;
  box-shadow: 0 10px 25px rgba(0,0,0,0.3);
}

.detail-poster .poster-image {
  width: 100%;
  aspect-ratio: 2/3;
  border-radius: var(--infuse-radius-md);
  object-fit: cover;
}

.detail-info h2 {
  font-size: 28px;
  font-weight: 800;
  color: var(--infuse-text-primary);
  margin-bottom: 12px;
  letter-spacing: -0.01em;
}

.detail-meta {
  display: flex;
  gap: 12px;
  color: var(--infuse-text-secondary);
  margin-bottom: 24px;
}

.detail-stats {
  display: flex;
  gap: 16px;
}

.stat-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12px 24px;
  background: rgba(10, 16, 38, 0.72);
  border-radius: var(--infuse-radius-md);
  border: 1px solid var(--infuse-border);
  min-width: 100px;
}

.stat-box.has { border-color: rgba(52, 199, 89, 0.3); }
.stat-box.missing { border-color: rgba(255, 149, 0, 0.3); }

.stat-box .stat-number {
  font-size: 24px;
  font-weight: 700;
}

.stat-box.has .stat-number { color: #34c759; }
.stat-box.missing .stat-number { color: #ff9500; }

.stat-box .stat-label {
  font-size: 12px;
  color: var(--infuse-text-tertiary);
  margin-top: 4px;
}

/* 季标签和缩略图 */
.seasons-section {
  display: flex;
  gap: 24px;
  margin-bottom: 32px;
  align-items: flex-start;
}

.seasons-tabs {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  flex: 1;
}

.season-tab {
  padding: 10px 18px;
  border-radius: var(--infuse-radius-md);
  background: var(--infuse-bg-card);
  border: 1px solid var(--infuse-border);
  cursor: pointer;
  transition: all 0.2s;
  font-size: 14px;
  font-weight: 500;
  color: var(--infuse-text-secondary);
}

.season-tab:hover {
  border-color: var(--infuse-accent);
  color: var(--infuse-text-primary);
}

.season-tab.active {
  background: var(--infuse-accent);
  border-color: var(--infuse-accent);
  color: #07101a;
  font-weight: 600;
}

.current-season-poster {
  width: 160px;
  flex-shrink: 0;
  border-radius: var(--infuse-radius-md);
  overflow: hidden;
  box-shadow: 0 8px 20px rgba(0,0,0,0.3);
}

.season-poster-image {
  width: 100%;
  height: auto;
  aspect-ratio: 2/3;
  object-fit: cover;
}

/* 剧集列表 */
.episodes-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-height: 450px;
  overflow-y: auto;
  padding-right: 8px;
}

.episodes-list::-webkit-scrollbar {
  width: 6px;
}

.episodes-list::-webkit-scrollbar-thumb {
  background: var(--infuse-border);
  border-radius: 3px;
}

.episode-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 20px;
  background: rgba(10, 16, 38, 0.74);
  border-radius: var(--infuse-radius-md);
  border: 1px solid var(--infuse-border);
  transition: all 0.2s;
}

.episode-item:hover {
  border-color: var(--infuse-accent);
  background: rgba(18, 29, 62, 0.88);
  transform: translateX(4px);
}

.episode-number {
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(34, 246, 255, 0.1);
  border-radius: 10px;
  font-size: 14px;
  font-weight: 700;
  color: var(--infuse-accent);
  flex-shrink: 0;
}

.episode-info {
  flex: 1;
  min-width: 0;
}

.episode-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--infuse-text-primary);
  margin-bottom: 4px;
}

.episode-filename {
  font-size: 12px;
  color: var(--infuse-text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.subtitle-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 20px;
  background: rgba(10, 16, 38, 0.74);
  border-radius: var(--infuse-radius-md);
  border: 1px solid var(--infuse-border);
  transition: all 0.2s;
}

.subtitle-item:hover {
  border-color: var(--infuse-accent);
  background: rgba(18, 29, 62, 0.88);
}

.subtitle-rank {
  width: 72px;
  min-width: 72px;
  min-height: 72px;
  border-radius: 18px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  font-size: 14px;
  font-weight: 700;
  flex-shrink: 0;
}

.subtitle-rank small {
  font-size: 10px;
  letter-spacing: 0.12em;
  opacity: 0.72;
}

.subtitle-rank strong {
  font-size: 16px;
  line-height: 1;
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
  font-size: 14px;
  font-weight: 600;
  color: var(--infuse-text-primary);
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.subtitle-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 10px;
}

.subhd-filename,
.subhd-summary {
  margin-top: 10px;
}

.subhd-filename {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--infuse-text-muted);
}

.subhd-summary {
  font-size: 12px;
  line-height: 1.5;
  color: var(--infuse-text-secondary);
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

/* 搜索对话框 */
.search-dialog-content {
  min-height: 300px;
}

.episode-info-header {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--infuse-border);
}

.episode-poster {
  width: 80px;
  flex-shrink: 0;
}

.poster-thumb,
.poster-thumb-placeholder {
  width: 100%;
  aspect-ratio: 2/3;
  border-radius: var(--infuse-radius-sm);
  object-fit: cover;
}

.poster-thumb-placeholder {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 24px;
}

.episode-details h3 {
  font-size: 18px;
  font-weight: 700;
  color: var(--infuse-text-primary);
  margin-bottom: 4px;
}

.episode-code {
  font-size: 14px;
  color: var(--infuse-accent);
  font-weight: 600;
  margin-bottom: 4px;
}

.episode-file {
  font-size: 12px;
  color: var(--infuse-text-muted);
}

/* 搜索结果 */
.search-results {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.empty-results {
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

.subtitle-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: rgba(10, 16, 38, 0.74);
  border-radius: var(--infuse-radius-md);
  border: 1px solid var(--infuse-border);
  transition: all var(--infuse-transition-fast);
}

.subtitle-item:hover {
  border-color: var(--infuse-border-hover);
  background: rgba(18, 29, 62, 0.88);
}

.subtitle-rank {
  width: 72px;
  min-width: 72px;
  min-height: 72px;
  border-radius: 18px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  font-size: 14px;
  font-weight: 700;
  flex-shrink: 0;
}

.subtitle-rank small {
  font-size: 10px;
  letter-spacing: 0.12em;
  opacity: 0.72;
}

.subtitle-rank strong {
  font-size: 16px;
  line-height: 1;
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

/* 响应式 */
@media (max-width: 768px) {
  .shows-grid {
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
    gap: 16px;
  }

  .toolbar {
    flex-direction: column;
    gap: 16px;
  }

  .search-box {
    width: 100%;
  }

  .filter-group {
    width: 100%;
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
  }

  .display-mode-toggle {
    grid-column: 1 / -1;
    width: 100%;
    display: grid;
    grid-template-columns: 1fr 1fr;
  }

  .display-mode-toggle :deep(.el-radio-button) {
    width: 100%;
  }

  .display-mode-toggle :deep(.el-radio-button__inner),
  .filter-group .el-button {
    margin: 0 !important;
    width: 100%;
    min-width: 0;
  }

  .display-mode-compact .shows-grid {
    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
    gap: 12px;
  }

  .display-mode-compact .show-poster {
    aspect-ratio: 2 / 3;
  }

  .display-mode-wide .shows-grid {
    grid-template-columns: 1fr;
    gap: 20px;
  }

  .display-mode-wide .show-poster {
    aspect-ratio: 16 / 9;
  }

  .detail-header {
    flex-direction: column;
  }

  .detail-poster {
    width: 120px;
    margin: 0 auto;
  }

  .seasons-section {
    flex-direction: column;
  }

  .current-season-poster {
    width: 100%;
    max-width: 200px;
    margin: 0 auto;
  }

  .subtitle-item,
  .episode-info-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .subtitle-rank {
    width: 100%;
    min-height: 56px;
  }
}
</style>
