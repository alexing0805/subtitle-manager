<template>
  <div class="movies">
    <header class="page-header">
      <h1 class="page-title">电影</h1>
      <p class="page-subtitle">管理电影字幕</p>
    </header>

    <div class="toolbar apple-card">
      <div class="search-box">
        <el-input
          v-model="searchQuery"
          placeholder="搜索电影..."
          prefix-icon="Search"
          clearable
        />
      </div>
      <div class="filter-group">
        <el-select v-model="filterStatus" placeholder="筛选状态" clearable>
          <el-option label="全部" value="" />
          <el-option label="有字幕" value="with" />
          <el-option label="无字幕" value="without" />
        </el-select>
        <el-button type="primary" @click="handleScan">
          <el-icon><Refresh /></el-icon>
          扫描
        </el-button>
      </div>
    </div>

    <div class="movies-grid">
      <div
        v-for="movie in filteredMovies"
        :key="movie.id"
        class="movie-card apple-card"
        @click="handleMovieClick(movie)"
      >
        <div class="movie-poster">
          <div class="poster-placeholder">
            <el-icon><Film /></el-icon>
          </div>
          <div class="subtitle-badge" :class="{ has: movie.hasSubtitle }">
            {{ movie.hasSubtitle ? '有字幕' : '无字幕' }}
          </div>
        </div>
        <div class="movie-info">
          <h3 class="movie-title">{{ movie.name }}</h3>
          <div class="movie-meta">
            <span v-if="movie.year" class="year">{{ movie.year }}</span>
            <span v-if="movie.resolution" class="resolution">{{ movie.resolution }}</span>
          </div>
          <div class="movie-actions">
            <el-button
              v-if="!movie.hasSubtitle"
              type="primary"
              size="small"
              @click.stop="handleSearch(movie)"
            >
              搜索字幕
            </el-button>
            <el-button
              v-else
              type="success"
              size="small"
              @click.stop="handleManage(movie)"
            >
              管理字幕
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 字幕搜索对话框 -->
    <el-dialog
      v-model="searchDialogVisible"
      title="搜索字幕"
      width="700px"
      destroy-on-close
    >
      <div v-if="currentMovie" class="search-dialog-content">
        <div class="movie-info-header">
          <h3>{{ currentMovie.name }}</h3>
          <p>{{ currentMovie.filename }}</p>
        </div>

        <div class="search-results" v-loading="searching">
          <div v-if="searchResults.length === 0 && !searching" class="empty-results">
            <el-icon><InfoFilled /></el-icon>
            <p>点击搜索按钮开始查找字幕</p>
          </div>

          <div
            v-for="result in searchResults"
            :key="result.id"
            class="subtitle-item"
          >
            <div class="subtitle-info">
              <div class="subtitle-title">{{ result.title }}</div>
              <div class="subtitle-meta">
                <el-tag size="small">{{ result.source }}</el-tag>
                <el-tag size="small" type="info">{{ result.language }}</el-tag>
                <span class="match-score">匹配度: {{ (result.score * 100).toFixed(0) }}%</span>
              </div>
            </div>
            <el-button
              type="primary"
              size="small"
              :loading="downloading === result.id"
              @click="handleDownload(result)"
            >
              下载
            </el-button>
          </div>
        </div>
      </div>

      <template #footer>
        <el-button @click="searchDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="handleDoSearch" :loading="searching">
          搜索
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useSubtitleStore } from '../stores/subtitle'
import { ElMessage } from 'element-plus'
import { Search, Refresh, Film, InfoFilled } from '@element-plus/icons-vue'

const store = useSubtitleStore()
const searchQuery = ref('')
const filterStatus = ref('')
const searchDialogVisible = ref(false)
const currentMovie = ref(null)
const searchResults = ref([])
const searching = ref(false)
const downloading = ref(null)

const movies = ref([
  { id: 1, name: '星际穿越', year: 2014, resolution: '1080p', filename: 'Interstellar.2014.1080p.BluRay.x264.mkv', hasSubtitle: true },
  { id: 2, name: '盗梦空间', year: 2010, resolution: '4K', filename: 'Inception.2010.2160p.UHD.BluRay.x265.mkv', hasSubtitle: false },
  { id: 3, name: '肖申克的救赎', year: 1994, resolution: '1080p', filename: 'The.Shawshank.Redemption.1994.1080p.BluRay.x264.mkv', hasSubtitle: false },
  { id: 4, name: '阿甘正传', year: 1994, resolution: '720p', filename: 'Forrest.Gump.1994.720p.BluRay.x264.mkv', hasSubtitle: true },
  { id: 5, name: '泰坦尼克号', year: 1997, resolution: '1080p', filename: 'Titanic.1997.1080p.BluRay.x264.mkv', hasSubtitle: false },
])

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

onMounted(async () => {
  // await store.fetchMovies()
  // movies.value = store.movies
})

function handleMovieClick(movie) {
  console.log('Clicked movie:', movie)
}

function handleSearch(movie) {
  currentMovie.value = movie
  searchDialogVisible.value = true
  searchResults.value = []
}

function handleManage(movie) {
  ElMessage.info('字幕管理功能开发中')
}

async function handleDoSearch() {
  if (!currentMovie.value) return

  searching.value = true
  try {
    // const results = await store.searchSubtitle(currentMovie.value.id)
    // searchResults.value = results
    
    // 模拟数据
    setTimeout(() => {
      searchResults.value = [
        { id: 1, title: 'Interstellar.2014.1080p.BluRay.x264.srt', source: 'SubHD', language: 'zh-cn', score: 0.95 },
        { id: 2, title: '星际穿越 2014 简体中文字幕', source: '字幕库', language: 'zh-cn', score: 0.88 },
        { id: 3, title: 'Interstellar.2014.BluRay.720p.srt', source: 'OpenSubtitles', language: 'zh-tw', score: 0.75 },
      ]
      searching.value = false
    }, 1500)
  } catch (error) {
    ElMessage.error('搜索失败')
    searching.value = false
  }
}

async function handleDownload(result) {
  downloading.value = result.id
  try {
    // await store.downloadSubtitle(currentMovie.value.id, result.id)
    ElMessage.success('字幕下载成功')
    searchDialogVisible.value = false
  } catch (error) {
    ElMessage.error('下载失败')
  } finally {
    downloading.value = null
  }
}

async function handleScan() {
  try {
    ElMessage.info('开始扫描...')
    // await store.scanLibrary()
    ElMessage.success('扫描完成')
  } catch (error) {
    ElMessage.error('扫描失败')
  }
}
</script>

<style scoped>
.movies {
  max-width: 1400px;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  margin-bottom: 24px;
}

.search-box {
  width: 300px;
}

.filter-group {
  display: flex;
  gap: 12px;
}

.movies-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 20px;
}

.movie-card {
  cursor: pointer;
  overflow: hidden;
  transition: all 0.3s ease;
}

.movie-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.12);
}

.movie-poster {
  position: relative;
  aspect-ratio: 2/3;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
}

.poster-placeholder {
  font-size: 48px;
  color: rgba(255, 255, 255, 0.5);
}

.subtitle-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 600;
  background: #ff9500;
  color: white;
}

.subtitle-badge.has {
  background: #34c759;
}

.movie-info {
  padding: 16px;
}

.movie-title {
  font-size: 15px;
  font-weight: 600;
  color: #1d1d1f;
  margin-bottom: 8px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.movie-meta {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.year, .resolution {
  font-size: 12px;
  color: #86868b;
  background: rgba(0, 0, 0, 0.04);
  padding: 2px 8px;
  border-radius: 4px;
}

.movie-actions {
  display: flex;
  gap: 8px;
}

.search-dialog-content {
  min-height: 300px;
}

.movie-info-header {
  padding: 16px;
  background: rgba(0, 0, 0, 0.02);
  border-radius: 12px;
  margin-bottom: 20px;
}

.movie-info-header h3 {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 4px;
}

.movie-info-header p {
  font-size: 13px;
  color: #86868b;
}

.search-results {
  min-height: 200px;
}

.empty-results {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: #86868b;
}

.empty-results .el-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.subtitle-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: rgba(0, 0, 0, 0.02);
  border-radius: 12px;
  margin-bottom: 12px;
}

.subtitle-info {
  flex: 1;
}

.subtitle-title {
  font-weight: 500;
  margin-bottom: 8px;
}

.subtitle-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.match-score {
  font-size: 12px;
  color: #0071e3;
  font-weight: 500;
}

@media (max-width: 768px) {
  .toolbar {
    flex-direction: column;
    gap: 12px;
  }
  
  .search-box {
    width: 100%;
  }
  
  .movies-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
