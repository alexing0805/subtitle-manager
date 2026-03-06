<template>
  <div class="settings">
    <header class="page-header">
      <h1 class="page-title">设置</h1>
      <p class="page-subtitle">配置字幕管理器</p>
    </header>

    <div class="settings-form">
      <!-- 基本设置 -->
      <div class="settings-section apple-card">
        <h3 class="section-title">基本设置</h3>
        
        <el-form :model="settings" label-position="top">
          <el-form-item label="监控目录">
            <el-input
              v-model="settings.watchDirs"
              placeholder="/movies, /tvshows"
              type="textarea"
              :rows="2"
            />
            <div class="form-hint">多个目录用逗号分隔</div>
          </el-form-item>

          <el-form-item label="扫描间隔（分钟）">
            <el-slider v-model="settings.scanInterval" :min="0" :max="120" :step="5" show-stops />
            <div class="form-hint">设为0禁用定时扫描</div>
          </el-form-item>

          <el-form-item label="文件大小阈值（MB）">
            <el-input-number v-model="settings.minFileSize" :min="10" :max="1000" :step="10" />
          </el-form-item>

          <el-form-item label="最大并发下载数">
            <el-input-number v-model="settings.maxConcurrent" :min="1" :max="10" />
          </el-form-item>
        </el-form>
      </div>

      <!-- 字幕源设置 -->
      <div class="settings-section apple-card">
        <h3 class="section-title">字幕源</h3>
        
        <el-form :model="settings" label-position="top">
          <el-form-item label="启用的字幕源">
            <el-checkbox-group v-model="settings.subtitleSources">
              <el-checkbox label="subhd">SubHD</el-checkbox>
              <el-checkbox label="zimuku">字幕库</el-checkbox>
              <el-checkbox label="opensubtitles">OpenSubtitles</el-checkbox>
            </el-checkbox-group>
          </el-form-item>

          <el-divider />

          <h4 class="subsection-title">OpenSubtitles API 配置</h4>
          
          <el-form-item label="API Key">
            <el-input v-model="settings.openSubtitlesApiKey" placeholder="输入你的 API Key" show-password />
          </el-form-item>

          <el-form-item label="用户名">
            <el-input v-model="settings.openSubtitlesUsername" placeholder="输入用户名" />
          </el-form-item>

          <el-form-item label="密码">
            <el-input v-model="settings.openSubtitlesPassword" type="password" placeholder="输入密码" show-password />
          </el-form-item>
        </el-form>
      </div>

      <!-- 高级设置 -->
      <div class="settings-section apple-card">
        <h3 class="section-title">高级设置</h3>
        
        <el-form :model="settings" label-position="top">
          <el-form-item>
            <el-checkbox v-model="settings.autoDownload">自动下载字幕</el-checkbox>
          </el-form-item>

          <el-form-item>
            <el-checkbox v-model="settings.backupExisting">下载前备份原字幕</el-checkbox>
          </el-form-item>

          <el-form-item label="日志级别">
            <el-select v-model="settings.logLevel" style="width: 200px;">
              <el-option label="DEBUG" value="DEBUG" />
              <el-option label="INFO" value="INFO" />
              <el-option label="WARNING" value="WARNING" />
              <el-option label="ERROR" value="ERROR" />
            </el-select>
          </el-form-item>
        </el-form>
      </div>

      <!-- 保存按钮 -->
      <div class="settings-actions">
        <button class="apple-button secondary" @click="handleReset">重置</button>
        <button class="apple-button" @click="handleSave" :disabled="saving">
          {{ saving ? '保存中...' : '保存设置' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'

const saving = ref(false)

const settings = ref({
  watchDirs: '/movies',
  scanInterval: 30,
  minFileSize: 100,
  maxConcurrent: 3,
  subtitleSources: ['subhd', 'zimuku'],
  openSubtitlesApiKey: '',
  openSubtitlesUsername: '',
  openSubtitlesPassword: '',
  autoDownload: true,
  backupExisting: false,
  logLevel: 'INFO'
})

onMounted(async () => {
  // 加载设置
  try {
    // const response = await fetch('/api/settings')
    // settings.value = await response.json()
  } catch (error) {
    console.error('加载设置失败:', error)
  }
})

async function handleSave() {
  saving.value = true
  try {
    // await fetch('/api/settings', {
    //   method: 'POST',
    //   headers: { 'Content-Type': 'application/json' },
    //   body: JSON.stringify(settings.value)
    // })
    
    // 模拟保存
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    ElMessage.success('设置已保存')
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

function handleReset() {
  settings.value = {
    watchDirs: '/movies',
    scanInterval: 30,
    minFileSize: 100,
    maxConcurrent: 3,
    subtitleSources: ['subhd', 'zimuku'],
    openSubtitlesApiKey: '',
    openSubtitlesUsername: '',
    openSubtitlesPassword: '',
    autoDownload: true,
    backupExisting: false,
    logLevel: 'INFO'
  }
  ElMessage.info('设置已重置')
}
</script>

<style scoped>
.settings {
  max-width: 800px;
}

.settings-section {
  padding: 24px;
  margin-bottom: 24px;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 20px;
  color: #1d1d1f;
}

.subsection-title {
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 16px;
  color: #1d1d1f;
}

.form-hint {
  font-size: 12px;
  color: #86868b;
  margin-top: 4px;
}

.settings-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid rgba(0, 0, 0, 0.06);
}

:deep(.el-form-item__label) {
  font-weight: 500;
  color: #1d1d1f;
}

:deep(.el-checkbox__label) {
  color: #1d1d1f;
}
</style>
