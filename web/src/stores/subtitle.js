import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

// API 基础 URL - 在 Docker 环境中使用相对路径
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || '/api'

const api = axios.create({
  baseURL: apiBaseUrl,
  timeout: 30000
})

export const useSubtitleStore = defineStore('subtitle', () => {
  // State
  const movies = ref([])
  const tvShows = ref([])
  const stats = ref({
    total: 0,
    withSubtitle: 0,
    withoutSubtitle: 0,
    processing: 0
  })
  const loading = ref(false)
  const currentTask = ref(null)

  // Getters
  const moviesWithoutSubtitle = computed(() => 
    movies.value.filter(m => !m.hasSubtitle)
  )
  
  const tvEpisodesWithoutSubtitle = computed(() => {
    const episodes = []
    tvShows.value.forEach(show => {
      show.seasons?.forEach(season => {
        season.episodes?.forEach(ep => {
          if (!ep.hasSubtitle) {
            episodes.push({
              ...ep,
              showName: show.name,
              seasonNumber: season.number
            })
          }
        })
      })
    })
    return episodes
  })

  // Actions
  async function fetchMovies() {
    loading.value = true
    try {
      const response = await api.get('/movies')
      movies.value = response.data
      return response.data
    } catch (error) {
      console.error('获取电影列表失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  async function fetchTVShows() {
    loading.value = true
    try {
      const response = await api.get('/tvshows')
      tvShows.value = response.data
      return response.data
    } catch (error) {
      console.error('获取电视剧列表失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  async function fetchStats() {
    try {
      const response = await api.get('/stats')
      stats.value = response.data
      return response.data
    } catch (error) {
      console.error('获取统计信息失败:', error)
      throw error
    }
  }

  async function searchSubtitle(videoId, type = 'movie') {
    try {
      const response = await api.post(`/search-subtitle`, {
        videoId,
        type
      })
      return response.data
    } catch (error) {
      console.error('搜索字幕失败:', error)
      throw error
    }
  }

  async function downloadSubtitle(videoId, subtitleId, type = 'movie') {
    try {
      const response = await api.post(`/download-subtitle`, {
        videoId,
        subtitleId,
        type
      })
      return response.data
    } catch (error) {
      console.error('下载字幕失败:', error)
      throw error
    }
  }

  async function uploadSubtitle(videoId, formData, type = 'movie') {
    try {
      const response = await api.post(`/upload-subtitle`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        params: { videoId, type }
      })
      return response.data
    } catch (error) {
      console.error('上传字幕失败:', error)
      throw error
    }
  }

  async function batchUploadSubtitles(formData) {
    try {
      const response = await api.post(`/batch-upload-subtitles`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
      return response.data
    } catch (error) {
      console.error('批量上传字幕失败:', error)
      throw error
    }
  }

  async function scanLibrary() {
    try {
      const response = await api.post('/scan')
      return response.data
    } catch (error) {
      console.error('扫描库失败:', error)
      throw error
    }
  }

  async function processVideo(videoId, type = 'movie') {
    try {
      const response = await api.post(`/process`, { videoId, type })
      return response.data
    } catch (error) {
      console.error('处理视频失败:', error)
      throw error
    }
  }

  return {
    movies,
    tvShows,
    stats,
    loading,
    currentTask,
    moviesWithoutSubtitle,
    tvEpisodesWithoutSubtitle,
    fetchMovies,
    fetchTVShows,
    fetchStats,
    searchSubtitle,
    downloadSubtitle,
    uploadSubtitle,
    batchUploadSubtitles,
    scanLibrary,
    processVideo
  }
})
