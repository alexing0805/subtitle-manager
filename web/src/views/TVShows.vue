<template>
  <div class="tv-shows">
    <header class="page-header">
      <h1 class="page-title">电视剧</h1>
      <p class="page-subtitle">管理电视剧字幕</p>
    </header>

    <div class="toolbar apple-card">
      <div class="search-box">
        <el-input
          v-model="searchQuery"
          placeholder="搜索电视剧..."
          prefix-icon="Search"
          clearable
        />
      </div>
      <div class="filter-group">
        <el-button type="primary" @click="handleBatchUpload">
          <el-icon><Upload /></el-icon>
          批量上传字幕
        </el-button>
        <el-button @click="handleScan">
          <el-icon><Refresh /></el-icon>
          扫描
        </el-button>
      </div>
    </div>

    <div class="shows-list">
      <div
        v-for="show in filteredShows"
        :key="show.id"
        class="show-card apple-card"
      >
        <div class="show-header" @click="toggleShow(show.id)">
          <div class="show-poster">
            <el-icon><Monitor /></el-icon>
          </div>
          <div class="show-info">
            <h3 class="show-title">{{ show.name }}</h3>
            <div class="show-meta">
              <span v-if="show.year" class="year">{{ show.year }}</span>
              <span class="seasons">{{ show.seasonCount }} 季</span>
              <span class="episodes">{{ show.episodeCount }} 集</span>
            </div>
          </div>
          <div class="show-stats">
            <div class="stat-item">
              <span class="stat-value has">{{ show.subtitleStats.has }}</span>
              <span class="stat-label">有字幕</span>
            </div>
            <div class="stat-item">
              <span class="stat-value missing">{{ show.subtitleStats.missing }}</span>
              <span class="stat-label">无字幕</span>
            </div>
          </div>
          <el-icon class="expand-icon" :class="{ expanded: expandedShows.includes(show.id) }">
            <ArrowDown />
          </el-icon>
        </div>

        <div v-if="expandedShows.includes(show.id)" class="seasons-content">
          <div class="seasons-tabs">
            <div
              v-for="season in show.seasons"
              :key="season.number"
              class="season-tab"
              :class="{ active: activeSeason[show.id] === season.number }"
              @click.stop="activeSeason[show.id] = season.number"
            >
              第 {{ season.number }} 季
            </div>
          </div>

          <div class="episodes-table">
            <el-table
              :data="getCurrentSeasonEpisodes(show)"
              style="width: 100%"
            >
              <el-table-column width="60">
                <template #default="{ row }">
                  <el-icon v-if="row.hasSubtitle" class="status-icon success"><CircleCheck /></el-icon>
                  <el-icon v-else class="status-icon missing"><Warning /></el-icon>
                </template>
              </el-table-column>
              <el-table-column label="集数" width="80">
                <template #default="{ row }">
                  <span class="episode-number">E{{ String(row.episodeNumber).padStart(2, '0') }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="name" label="标题" />
              <el-table-column prop="filename" label="文件名" show-overflow-tooltip />
              <el-table-column label="操作" width="150">
                <template #default="{ row }">
                  <el-button
                    v-if="!row.hasSubtitle"
                    type="primary"
                    link
                    size="small"
                    @click="handleSearchSubtitle(show, row)"
                  >
                    搜索字幕
                  </el-button>
                  <el-button
                    v-else
                    type="success"
                    link
                    size="small"
                    @click="handleManageSubtitle(show, row)"
                  >
                    管理
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useSubtitleStore } from '../stores/subtitle'
import { ElMessage } from 'element-plus'
import { Search, Refresh, Upload, Monitor, ArrowDown, CircleCheck, Warning } from '@element-plus/icons-vue'

const router = useRouter()
const store = useSubtitleStore()
const searchQuery = ref('')
const expandedShows = ref([])
const activeSeason = ref({})

const shows = ref([
  {
    id: 1,
    name: '权力的游戏',
    year: 2011,
    seasonCount: 8,
    episodeCount: 73,
    subtitleStats: { has: 45, missing: 28 },
    seasons: [
      {
        number: 1,
        episodes: [
          { id: 's1e1', episodeNumber: 1, name: '凛冬将至', filename: 'Game.of.Thrones.S01E01.1080p.mkv', hasSubtitle: true },
          { id: 's1e2', episodeNumber: 2, name: '国王大道', filename: 'Game.of.Thrones.S01E02.1080p.mkv', hasSubtitle: true },
          { id: 's1e3', episodeNumber: 3, name: '雪诺大人', filename: 'Game.of.Thrones.S01E03.1080p.mkv', hasSubtitle: false },
          { id: 's1e4', episodeNumber: 4, name: '残缺之物', filename: 'Game.of.Thrones.S01E04.1080p.mkv', hasSubtitle: false },
        ]
      },
      {
        number: 2,
        episodes: [
          { id: 's2e1', episodeNumber: 1, name: '北境不忘', filename: 'Game.of.Thrones.S02E01.1080p.mkv', hasSubtitle: false },
          { id: 's2e2', episodeNumber: 2, name: '夜之国度', filename: 'Game.of.Thrones.S02E02.1080p.mkv', hasSubtitle: false },
        ]
      }
    ]
  },
  {
    id: 2,
    name: '绝命毒师',
    year: 2008,
    seasonCount: 5,
    episodeCount: 62,
    subtitleStats: { has: 62, missing: 0 },
    seasons: [
      {
        number: 1,
        episodes: [
          { id: 'bb_s1e1', episodeNumber: 1, name: '试播集', filename: 'Breaking.Bad.S01E01.1080p.mkv', hasSubtitle: true },
          { id: 'bb_s1e2', episodeNumber: 2, name: '木已成舟', filename: 'Breaking.Bad.S01E02.1080p.mkv', hasSubtitle: true },
        ]
      }
    ]
  }
])

const filteredShows = computed(() => {
  if (!searchQuery.value) return shows.value
  const query = searchQuery.value.toLowerCase()
  return shows.value.filter(s => s.name.toLowerCase().includes(query))
})

onMounted(async () => {
  // await store.fetchTVShows()
  // shows.value = store.tvShows
})

function toggleShow(showId) {
  const index = expandedShows.value.indexOf(showId)
  if (index > -1) {
    expandedShows.value.splice(index, 1)
  } else {
    expandedShows.value.push(showId)
    // 默认展开第一季
    if (!activeSeason.value[showId]) {
      const show = shows.value.find(s => s.id === showId)
      if (show && show.seasons.length > 0) {
        activeSeason.value[showId] = show.seasons[0].number
      }
    }
  }
}

function getCurrentSeasonEpisodes(show) {
  const seasonNumber = activeSeason.value[show.id] || 1
  const season = show.seasons.find(s => s.number === seasonNumber)
  return season ? season.episodes : []
}

function handleBatchUpload() {
  router.push('/batch-upload')
}

function handleSearchSubtitle(show, episode) {
  ElMessage.info(`搜索 ${show.name} - E${String(episode.episodeNumber).padStart(2, '0')} 的字幕`)
}

function handleManageSubtitle(show, episode) {
  ElMessage.info(`管理 ${show.name} - E${String(episode.episodeNumber).padStart(2, '0')} 的字幕`)
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
.tv-shows {
  max-width: 1200px;
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

.shows-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.show-card {
  overflow: hidden;
}

.show-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  cursor: pointer;
  transition: background 0.2s ease;
}

.show-header:hover {
  background: rgba(0, 0, 0, 0.02);
}

.show-poster {
  width: 60px;
  height: 60px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 24px;
}

.show-info {
  flex: 1;
}

.show-title {
  font-size: 17px;
  font-weight: 600;
  color: #1d1d1f;
  margin-bottom: 6px;
}

.show-meta {
  display: flex;
  gap: 12px;
  font-size: 13px;
  color: #86868b;
}

.year, .seasons, .episodes {
  background: rgba(0, 0, 0, 0.04);
  padding: 2px 10px;
  border-radius: 4px;
}

.show-stats {
  display: flex;
  gap: 24px;
  margin-right: 16px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.stat-value {
  font-size: 20px;
  font-weight: 700;
}

.stat-value.has {
  color: #34c759;
}

.stat-value.missing {
  color: #ff9500;
}

.stat-label {
  font-size: 12px;
  color: #86868b;
}

.expand-icon {
  font-size: 20px;
  color: #86868b;
  transition: transform 0.3s ease;
}

.expand-icon.expanded {
  transform: rotate(180deg);
}

.seasons-content {
  border-top: 1px solid rgba(0, 0, 0, 0.06);
  padding: 20px;
}

.seasons-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.season-tab {
  padding: 8px 16px;
  border-radius: 8px;
  background: rgba(0, 0, 0, 0.04);
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 14px;
  font-weight: 500;
}

.season-tab:hover {
  background: rgba(0, 0, 0, 0.08);
}

.season-tab.active {
  background: #0071e3;
  color: white;
}

.episodes-table {
  background: rgba(0, 0, 0, 0.02);
  border-radius: 12px;
  padding: 8px;
}

.status-icon {
  font-size: 18px;
}

.status-icon.success {
  color: #34c759;
}

.status-icon.missing {
  color: #ff9500;
}

.episode-number {
  font-weight: 600;
  color: #0071e3;
}

@media (max-width: 768px) {
  .toolbar {
    flex-direction: column;
    gap: 12px;
  }
  
  .search-box {
    width: 100%;
  }
  
  .show-header {
    flex-wrap: wrap;
  }
  
  .show-stats {
    width: 100%;
    justify-content: flex-start;
    margin-top: 8px;
  }
}
</style>
