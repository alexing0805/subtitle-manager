<template>
  <div class="batch-upload">
    <header class="page-header">
      <h1 class="page-title">批量上传字幕</h1>
      <p class="page-subtitle">为电视剧或动漫批量上传并匹配字幕文件</p>
    </header>

    <!-- 步骤条 -->
    <div class="steps-container apple-card">
      <el-steps :active="currentStep" finish-status="success">
        <el-step title="选择剧集" description="选择要上传字幕的电视剧" />
        <el-step title="匹配文件" description="将字幕文件与剧集匹配" />
        <el-step title="确认上传" description="检查并上传字幕" />
      </el-steps>
    </div>

    <!-- 步骤 1: 选择剧集 -->
    <div v-if="currentStep === 0" class="step-content">
      <div class="apple-card" style="padding: 24px;">
        <h3 class="step-title">选择剧集库</h3>

        <el-radio-group v-model="mediaType" style="margin-bottom: 20px;" @change="handleLibraryTypeChange">
          <el-radio-button label="tv">电视剧</el-radio-button>
          <el-radio-button label="anime">动漫</el-radio-button>
        </el-radio-group>
        
        <el-select
          v-model="selectedShow"
          filterable
          placeholder="搜索或选择条目"
          style="width: 100%; margin-bottom: 20px;"
          @change="handleShowChange"
        >
          <el-option
            v-for="show in mediaShows"
            :key="show.id"
            :label="show.name"
            :value="show.id"
          >
            <div class="show-option">
              <span class="show-name">{{ show.name }}</span>
              <span class="show-meta">{{ show.seasonCount }}季 / {{ show.episodeCount }}集</span>
            </div>
          </el-option>
        </el-select>

        <div v-if="selectedShowData" class="show-info">
          <div class="info-header">
            <h4>{{ selectedShowData.name }}</h4>
            <el-tag v-if="selectedShowData.year" type="info">{{ selectedShowData.year }}</el-tag>
          </div>
          
          <div class="seasons-tabs">
            <div
              v-for="season in selectedShowData.seasons"
              :key="season.number"
              class="season-tab"
              :class="{ active: selectedSeason === season.number }"
              @click="selectedSeason = season.number"
            >
              第{{ season.number }}季
              <span class="episode-count">({{ season.episodes.length }}集)</span>
            </div>
          </div>

          <div v-if="currentSeason" class="episodes-list">
            <div class="episodes-header">
              <span>共 {{ currentSeason.episodes.length }} 集</span>
              <span class="subtitle-status">
                有字幕: {{ episodesWithSubtitle }} / 无字幕: {{ episodesWithoutSubtitle }}
              </span>
            </div>
            
            <el-table :data="currentSeason.episodes" style="width: 100%">
              <el-table-column prop="episodeNumber" label="集数" width="80">
                <template #default="{ row }">
                  <span class="episode-number">E{{ String(row.episodeNumber).padStart(2, '0') }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="name" label="标题" />
              <el-table-column prop="filename" label="文件名" show-overflow-tooltip />
              <el-table-column label="字幕状态" width="120">
                <template #default="{ row }">
                  <el-tag :type="row.hasSubtitle ? 'success' : 'warning'" size="small">
                    {{ row.hasSubtitle ? '有字幕' : '无字幕' }}
                  </el-tag>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>

        <div class="step-actions">
          <button class="apple-button" @click="nextStep" :disabled="!selectedShow || !selectedSeason">
            下一步
          </button>
        </div>
      </div>
    </div>

    <!-- 步骤 2: 匹配文件 -->
    <div v-if="currentStep === 1" class="step-content">
      <div class="apple-card" style="padding: 24px;">
        <h3 class="step-title">上传并匹配字幕文件</h3>
        
        <div class="upload-area">
          <el-upload
            ref="uploadRef"
            v-model:file-list="subtitleFiles"
            action="#"
            :auto-upload="false"
            :on-change="handleFileChange"
            :on-remove="handleFileRemove"
            multiple
            drag
            accept=".srt,.ass,.ssa,.vtt"
          >
            <el-icon class="upload-icon"><Upload /></el-icon>
            <div class="upload-text">
              <p>拖拽字幕文件到此处，或 <em>点击上传</em></p>
              <p class="upload-hint">支持 SRT, ASS, SSA, VTT 格式</p>
            </div>
          </el-upload>
        </div>

        <div v-if="subtitleFiles.length > 0" class="matching-section">
          <div class="matching-header">
            <h4>自动匹配结果</h4>
            <div class="matching-stats">
              <el-tag type="success">已匹配: {{ matchedCount }}</el-tag>
              <el-tag type="warning">待匹配: {{ unmatchedCount }}</el-tag>
            </div>
          </div>

          <div class="matching-list">
            <div
              v-for="(match, index) in fileMatches"
              :key="index"
              class="match-item"
              :class="{ matched: match.episode }"
            >
              <div class="file-info">
                <el-icon class="file-icon"><Document /></el-icon>
                <div class="file-details">
                  <div class="filename">{{ match.file.name }}</div>
                  <div v-if="match.parsedInfo" class="parsed-info">
                    识别到: S{{ String(match.parsedInfo.season).padStart(2, '0') }}E{{ String(match.parsedInfo.episode).padStart(2, '0') }}
                  </div>
                </div>
              </div>

              <div class="match-arrow">
                <el-icon><ArrowRight /></el-icon>
              </div>

              <div class="episode-select">
                <el-select
                  v-model="match.selectedEpisode"
                  placeholder="选择剧集"
                  style="width: 200px;"
                  size="small"
                  @change="(val) => handleEpisodeSelect(match, val)"
                >
                  <el-option
                    v-for="ep in availableEpisodes"
                    :key="ep.id"
                    :label="`E${String(ep.episodeNumber).padStart(2, '0')} - ${ep.name || ep.filename || '未命名剧集'}`"
                    :value="ep.id"
                  />
                </el-select>
              </div>

              <div class="match-status">
                <el-icon v-if="match.episode" class="status-icon success"><CircleCheck /></el-icon>
                <el-icon v-else class="status-icon pending"><Warning /></el-icon>
              </div>
            </div>
          </div>
        </div>

        <div class="step-actions">
          <button class="apple-button secondary" @click="prevStep">上一步</button>
          <button class="apple-button" @click="nextStep" :disabled="matchedCount === 0">
            下一步
          </button>
        </div>
      </div>
    </div>

    <!-- 步骤 3: 确认上传 -->
    <div v-if="currentStep === 2" class="step-content">
      <div class="apple-card" style="padding: 24px;">
        <h3 class="step-title">确认上传</h3>
        
        <div class="confirm-summary">
          <div class="summary-item">
            <span class="summary-label">电视剧:</span>
            <span class="summary-value">{{ selectedShowData?.name }}</span>
          </div>
          <div class="summary-item">
            <span class="summary-label">季数:</span>
            <span class="summary-value">第 {{ selectedSeason }} 季</span>
          </div>
          <div class="summary-item">
            <span class="summary-label">待上传字幕:</span>
            <span class="summary-value">{{ matchedCount }} 个文件</span>
          </div>
        </div>

        <div class="confirm-list">
          <h4>上传列表</h4>
          <el-table :data="confirmedMatches" style="width: 100%">
            <el-table-column prop="file.name" label="字幕文件" show-overflow-tooltip />
            <el-table-column label="匹配剧集" width="200">
              <template #default="{ row }">
                <span v-if="row.episode">
                  E{{ String(row.episode.episodeNumber).padStart(2, '0') }} - {{ row.episode.name || row.episode.filename || '未命名剧集' }}
                </span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100">
              <template #default="{ $index }">
                <el-button type="danger" link @click="removeMatch($index)">
                  移除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <div class="upload-progress" v-if="isUploading">
          <h4>上传进度</h4>
          <el-progress 
            :percentage="uploadProgress" 
            :status="uploadStatus"
            :stroke-width="8"
          />
          <p class="progress-text">{{ uploadStatusText }}</p>
        </div>

        <div class="step-actions">
          <button class="apple-button secondary" @click="prevStep" :disabled="isUploading">
            上一步
          </button>
          <button 
            class="apple-button" 
            @click="handleUpload" 
            :disabled="confirmedMatches.length === 0 || isUploading"
          >
            {{ isUploading ? '上传中...' : '开始上传' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useSubtitleStore } from '../stores/subtitle'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Upload, Document, ArrowRight, CircleCheck, Warning
} from '@element-plus/icons-vue'

const store = useSubtitleStore()
const currentStep = ref(0)
const mediaType = ref('tv')
const selectedShow = ref('')
const selectedSeason = ref(null)
const subtitleFiles = ref([])
const fileMatches = ref([])
const isUploading = ref(false)
const uploadProgress = ref(0)
const uploadStatus = ref('')
const uploadStatusText = ref('')

const mediaShows = computed(() => {
  return mediaType.value === 'anime' ? store.anime : store.tvShows
})

const selectedShowData = computed(() => {
  return mediaShows.value.find(s => String(s.id) === String(selectedShow.value))
})

const currentSeason = computed(() => {
  if (!selectedShowData.value || !selectedSeason.value) return null
  return selectedShowData.value.seasons.find(s => s.number === selectedSeason.value)
})

const availableEpisodes = computed(() => {
  return currentSeason.value?.episodes || []
})

const episodesWithSubtitle = computed(() => {
  return currentSeason.value?.episodes.filter(e => e.hasSubtitle).length || 0
})

const episodesWithoutSubtitle = computed(() => {
  return currentSeason.value?.episodes.filter(e => !e.hasSubtitle).length || 0
})

const matchedCount = computed(() => {
  return fileMatches.value.filter(m => m.episode).length
})

const unmatchedCount = computed(() => {
  return fileMatches.value.filter(m => !m.episode).length
})

const confirmedMatches = computed(() => {
  return fileMatches.value.filter(m => m.episode)
})

onMounted(async () => {
  try {
    await Promise.all([
      store.fetchTVShows(),
      store.fetchAnime()
    ])
  } catch (error) {
    ElMessage.error('获取剧集列表失败')
  }
})

function handleLibraryTypeChange() {
  selectedShow.value = ''
  selectedSeason.value = null
  fileMatches.value = []
  subtitleFiles.value = []
}

function handleShowChange() {
  selectedSeason.value = null
  fileMatches.value = []
  subtitleFiles.value = []
}

function handleFileChange(file) {
  const rawFile = file.raw || file
  const parsedInfo = parseSubtitleFilename(rawFile.name)
  const match = {
    uid: rawFile.uid || `${rawFile.name}-${rawFile.size}-${Date.now()}`,
    file: rawFile,
    parsedInfo,
    selectedEpisode: null,
    episode: null
  }

  // 去重更新
  const existingIndex = fileMatches.value.findIndex(m => m.uid === match.uid)
  if (existingIndex !== -1) {
    fileMatches.value.splice(existingIndex, 1)
  }
  
  // 自动匹配
  if (parsedInfo && currentSeason.value) {
    const matchedEpisode = currentSeason.value.episodes.find(
      ep => ep.episodeNumber === parsedInfo.episode && (!parsedInfo.season || selectedSeason.value === parsedInfo.season)
    )
    if (matchedEpisode) {
      match.selectedEpisode = matchedEpisode.id
      match.episode = matchedEpisode
    }
  }
  
  fileMatches.value.push(match)
}

function handleFileRemove(file) {
  const uid = file.uid || file.raw?.uid
  const index = fileMatches.value.findIndex(m => m.uid === uid)
  if (index > -1) {
    fileMatches.value.splice(index, 1)
  }
}

function parseSubtitleFilename(filename) {
  const cleanName = filename.replace(/\.[^.]+$/, '')

  // 优先匹配标准格式
  const seasonEpisodePatterns = [
    /[Ss](\d{1,2})[Ee](\d{1,3})/i,
    /(\d{1,2})x(\d{1,3})/i,
    /第\s*(\d{1,3})\s*[集话話]/,
    /[Ee][Pp]?(\d{1,3})/,
    /\b(\d{1,3})\b(?=\s*(?:END|v\d+)?\s*$)/i,
    /[-_\s]\s*(\d{1,3})\s*[-_\s]/,
    /\[(\d{1,3})\]/,
  ]

  for (const pattern of seasonEpisodePatterns) {
    const match = cleanName.match(pattern)
    if (!match) continue

    if (match[2]) {
      return {
        season: parseInt(match[1]),
        episode: parseInt(match[2])
      }
    }

    return {
      season: selectedSeason.value,
      episode: parseInt(match[1])
    }
  }

  return null
}

function handleEpisodeSelect(match, episodeId) {
  const episode = availableEpisodes.value.find(ep => ep.id === episodeId)
  match.episode = episode || null
}

function removeMatch(index) {
  const match = confirmedMatches.value[index]
  if (!match) return
  const realIndex = fileMatches.value.findIndex(item => item.uid === match.uid)
  if (realIndex > -1) {
    fileMatches.value.splice(realIndex, 1)
  }
}

async function handleUpload() {
  isUploading.value = true
  uploadProgress.value = 0
  uploadStatus.value = ''
  uploadStatusText.value = '准备上传...'

  const formData = new FormData()
  formData.append('showId', selectedShow.value)
  formData.append('seasonNumber', selectedSeason.value)
  formData.append('mediaType', mediaType.value)

  const matches = confirmedMatches.value.map((match, index) => {
    formData.append('files', match.file)
    return {
      fileIndex: index,
      episodeId: match.episode.id,
      episodeNumber: match.episode.episodeNumber,
      filename: match.file.name
    }
  })
  formData.append('matches', JSON.stringify(matches))
  
  try {
    uploadStatusText.value = '正在上传字幕文件...'
    
    const interval = setInterval(() => {
      if (uploadProgress.value < 90) {
        uploadProgress.value += 10
      }
    }, 200)
    
    const response = await store.batchUploadSubtitles(formData)
    
    clearInterval(interval)
    uploadProgress.value = 100
    uploadStatus.value = response.success ? 'success' : 'warning'
    uploadStatusText.value = response.message || '上传完成'

    if (response.errors?.length) {
      ElMessageBox.alert(
        response.errors.map(item => `${item.match?.filename || '未知文件'}：${item.message}`).join('\n'),
        '部分字幕上传失败',
        { type: 'warning' }
      )
    } else {
      ElMessage.success(response.message || '字幕上传成功')
    }
    
    setTimeout(() => {
      currentStep.value = 0
      resetForm()
    }, 1200)
  } catch (error) {
    uploadStatus.value = 'exception'
    uploadStatusText.value = '上传失败'
    ElMessage.error('上传失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    isUploading.value = false
  }
}

function nextStep() {
  if (currentStep.value < 2) {
    currentStep.value++
  }
}

function prevStep() {
  if (currentStep.value > 0) {
    currentStep.value--
  }
}

function resetForm() {
  selectedShow.value = ''
  selectedSeason.value = null
  subtitleFiles.value = []
  fileMatches.value = []
  uploadProgress.value = 0
  uploadStatus.value = ''
  uploadStatusText.value = ''
}
</script>

<style scoped>
.batch-upload {
  max-width: 1000px;
}

.steps-container {
  padding: 32px;
  margin-bottom: 32px;
}

.step-content {
  margin-bottom: 32px;
}

.step-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 20px;
  color: #1d1d1f;
}

.show-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.show-name {
  font-weight: 500;
}

.show-meta {
  font-size: 12px;
  color: #86868b;
}

.show-info {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid rgba(0, 0, 0, 0.06);
}

.info-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}

.info-header h4 {
  font-size: 18px;
  font-weight: 600;
}

.seasons-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.season-tab {
  padding: 8px 16px;
  border-radius: 8px;
  background: rgba(0, 0, 0, 0.04);
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 14px;
}

.season-tab:hover {
  background: rgba(0, 0, 0, 0.08);
}

.season-tab.active {
  background: #0071e3;
  color: white;
}

.episode-count {
  font-size: 12px;
  opacity: 0.7;
  margin-left: 4px;
}

.episodes-list {
  margin-top: 16px;
}

.episodes-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  font-size: 14px;
  color: #86868b;
}

.subtitle-status {
  display: flex;
  gap: 12px;
}

.episode-number {
  font-weight: 600;
  color: #0071e3;
}

.step-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid rgba(0, 0, 0, 0.06);
}

.upload-area {
  margin-bottom: 24px;
}

.upload-area :deep(.el-upload-dragger) {
  background: rgba(0, 113, 227, 0.04);
  border: 2px dashed rgba(0, 113, 227, 0.2);
  border-radius: 16px;
  padding: 40px;
}

.upload-area :deep(.el-upload-dragger:hover) {
  border-color: #0071e3;
  background: rgba(0, 113, 227, 0.08);
}

.upload-icon {
  font-size: 48px;
  color: #0071e3;
  margin-bottom: 16px;
}

.upload-text {
  text-align: center;
}

.upload-text p {
  margin: 0;
  color: #1d1d1f;
}

.upload-hint {
  font-size: 13px;
  color: #86868b;
  margin-top: 8px !important;
}

.matching-section {
  margin-top: 24px;
}

.matching-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.matching-header h4 {
  font-size: 16px;
  font-weight: 600;
}

.matching-stats {
  display: flex;
  gap: 8px;
}

.matching-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.match-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: rgba(0, 0, 0, 0.02);
  border-radius: 12px;
  border: 1px solid transparent;
  transition: all 0.2s ease;
}

.match-item.matched {
  background: rgba(52, 199, 89, 0.04);
  border-color: rgba(52, 199, 89, 0.2);
}

.file-info {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.file-icon {
  font-size: 24px;
  color: #0071e3;
}

.file-details {
  min-width: 0;
}

.filename {
  font-weight: 500;
  color: #1d1d1f;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.parsed-info {
  font-size: 12px;
  color: #0071e3;
  margin-top: 2px;
}

.match-arrow {
  color: #86868b;
}

.match-status {
  width: 24px;
  display: flex;
  justify-content: center;
}

.status-icon {
  font-size: 20px;
}

.status-icon.success {
  color: #34c759;
}

.status-icon.pending {
  color: #ff9500;
}

.confirm-summary {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 24px;
  padding: 20px;
  background: rgba(0, 0, 0, 0.02);
  border-radius: 12px;
}

.summary-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.summary-label {
  font-size: 13px;
  color: #86868b;
}

.summary-value {
  font-size: 16px;
  font-weight: 600;
  color: #1d1d1f;
}

.confirm-list {
  margin-bottom: 24px;
}

.confirm-list h4 {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 12px;
}

.upload-progress {
  margin-bottom: 24px;
  padding: 20px;
  background: rgba(0, 113, 227, 0.04);
  border-radius: 12px;
}

.upload-progress h4 {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 12px;
}

.progress-text {
  text-align: center;
  margin-top: 12px;
  font-size: 14px;
  color: #86868b;
}

@media (max-width: 768px) {
  .confirm-summary {
    grid-template-columns: 1fr;
  }
  
  .match-item {
    flex-wrap: wrap;
  }
  
  .match-arrow {
    display: none;
  }
}
</style>
