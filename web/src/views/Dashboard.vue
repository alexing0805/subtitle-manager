<template>
  <div class="dashboard">
    <header class="page-header">
      <h1 class="page-title">仪表盘</h1>
      <p class="page-subtitle">概览你的字幕管理状态</p>
    </header>

    <!-- 统计卡片 -->
    <div class="stats-grid">
      <div class="stat-card apple-card">
        <div class="stat-icon" style="background: linear-gradient(135deg, #0071e3 0%, #42a5f5 100%);">
          <el-icon><Film /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.total }}</div>
          <div class="stat-label">总视频数</div>
        </div>
      </div>

      <div class="stat-card apple-card">
        <div class="stat-icon" style="background: linear-gradient(135deg, #34c759 0%, #30d158 100%);">
          <el-icon><Check /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.withSubtitle }}</div>
          <div class="stat-label">已有字幕</div>
        </div>
      </div>

      <div class="stat-card apple-card">
        <div class="stat-icon" style="background: linear-gradient(135deg, #ff9500 0%, #ffcc00 100%);">
          <el-icon><Warning /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.withoutSubtitle }}</div>
          <div class="stat-label">缺少字幕</div>
        </div>
      </div>

      <div class="stat-card apple-card">
        <div class="stat-icon" style="background: linear-gradient(135deg, #af52de 0%, #bf5af2 100%);">
          <el-icon><Loading /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.processing }}</div>
          <div class="stat-label">处理中</div>
        </div>
      </div>
    </div>

    <!-- 快捷操作 -->
    <div class="quick-actions">
      <h2 class="section-title">快捷操作</h2>
      <div class="actions-grid">
        <button class="action-card apple-card" @click="handleScan">
          <el-icon class="action-icon"><Search /></el-icon>
          <span class="action-text">扫描库</span>
        </button>
        
        <button class="action-card apple-card" @click="$router.push('/batch-upload')">
          <el-icon class="action-icon"><Upload /></el-icon>
          <span class="action-text">批量上传</span>
        </button>
        
        <button class="action-card apple-card" @click="handleAutoDownload">
          <el-icon class="action-icon"><Download /></el-icon>
          <span class="action-text">自动下载</span>
        </button>
        
        <button class="action-card apple-card" @click="$router.push('/settings')">
          <el-icon class="action-icon"><Setting /></el-icon>
          <span class="action-text">设置</span>
        </button>
      </div>
    </div>

    <!-- 最近活动 -->
    <div class="recent-activity">
      <h2 class="section-title">最近活动</h2>
      <div class="activity-list apple-card">
        <div v-if="activities.length === 0" class="empty-state">
          <el-icon class="empty-icon"><InfoFilled /></el-icon>
          <p>暂无活动记录</p>
        </div>
        <div 
          v-for="activity in activities" 
          :key="activity.id"
          class="activity-item"
        >
          <div class="activity-icon" :class="activity.type">
            <el-icon>
              <component :is="getActivityIcon(activity.type)" />
            </el-icon>
          </div>
          <div class="activity-content">
            <div class="activity-title">{{ activity.title }}</div>
            <div class="activity-time">{{ formatTime(activity.time) }}</div>
          </div>
          <el-tag :type="getActivityTagType(activity.status)" size="small">
            {{ activity.status }}
          </el-tag>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useSubtitleStore } from '../stores/subtitle'
import { ElMessage } from 'element-plus'
import {
  Film, Check, Warning, Loading, Search, Upload, Download, Setting, InfoFilled
} from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/zh-cn'

dayjs.extend(relativeTime)
dayjs.locale('zh-cn')

const store = useSubtitleStore()
const stats = ref({
  total: 0,
  withSubtitle: 0,
  withoutSubtitle: 0,
  processing: 0
})
const activities = ref([])

onMounted(async () => {
  try {
    const data = await store.fetchStats()
    stats.value = data
    // 这里可以从后端获取活动记录
    activities.value = []
  } catch (error) {
    ElMessage.error('获取统计信息失败')
  }
})

async function handleScan() {
  try {
    ElMessage.info('开始扫描库...')
    await store.scanLibrary()
    ElMessage.success('扫描完成')
    const data = await store.fetchStats()
    stats.value = data
  } catch (error) {
    ElMessage.error('扫描失败')
  }
}

async function handleAutoDownload() {
  try {
    ElMessage.info('开始自动下载字幕...')
    // 调用批量处理API
    ElMessage.success('任务已提交')
  } catch (error) {
    ElMessage.error('提交失败')
  }
}

function formatTime(time) {
  return dayjs(time).fromNow()
}

function getActivityIcon(type) {
  const icons = {
    scan: 'Search',
    download: 'Download',
    upload: 'Upload',
    process: 'Loading'
  }
  return icons[type] || 'InfoFilled'
}

function getActivityTagType(status) {
  const types = {
    success: 'success',
    failed: 'danger',
    processing: 'warning'
  }
  return types[status] || 'info'
}
</script>

<style scoped>
.dashboard {
  max-width: 1200px;
}

.page-header {
  margin-bottom: 32px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 40px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 24px;
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
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: #1d1d1f;
  line-height: 1;
}

.stat-label {
  font-size: 14px;
  color: #86868b;
  margin-top: 4px;
}

.section-title {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 16px;
  color: #1d1d1f;
}

.quick-actions {
  margin-bottom: 40px;
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
  gap: 12px;
  padding: 32px 24px;
  cursor: pointer;
  border: none;
  background: rgba(255, 255, 255, 0.8);
}

.action-icon {
  font-size: 32px;
  color: #0071e3;
}

.action-text {
  font-size: 15px;
  font-weight: 500;
  color: #1d1d1f;
}

.recent-activity {
  margin-bottom: 40px;
}

.activity-list {
  padding: 8px 0;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: #86868b;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.activity-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 24px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.activity-item:last-child {
  border-bottom: none;
}

.activity-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 113, 227, 0.1);
  color: #0071e3;
}

.activity-icon.download {
  background: rgba(52, 199, 89, 0.1);
  color: #34c759;
}

.activity-icon.upload {
  background: rgba(175, 82, 222, 0.1);
  color: #af52de;
}

.activity-content {
  flex: 1;
}

.activity-title {
  font-size: 15px;
  font-weight: 500;
  color: #1d1d1f;
}

.activity-time {
  font-size: 13px;
  color: #86868b;
  margin-top: 2px;
}

@media (max-width: 1024px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .actions-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 640px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .actions-grid {
    grid-template-columns: 1fr;
  }
}
</style>
