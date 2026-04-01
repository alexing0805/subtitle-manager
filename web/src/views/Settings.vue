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
          <el-form-item label="电影目录">
            <el-input
              v-model="settings.movieDir"
              placeholder="/movies"
            />
          </el-form-item>

          <el-form-item label="电视剧目录">
            <el-input
              v-model="settings.tvDir"
              placeholder="/tvshows"
            />
          </el-form-item>

          <el-form-item label="动漫目录">
            <el-input
              v-model="settings.animeDir"
              placeholder="/anime"
            />
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
          <el-form-item label="NASTool 路径映射">
            <el-input
              v-model="settings.nastoolPathMappings"
              type="textarea"
              :rows="4"
              placeholder="/downloads=/movies&#10;/media/tv=/tvshows&#10;/media/anime=/anime"
            />
            <div class="form-hint">当 NASTool 和字幕管理器的挂载路径不一致时使用，每行一条 from=to</div>
          </el-form-item>
        </el-form>
      </div>

      <!-- 字幕源设置 -->
      <div class="settings-section apple-card">
        <h3 class="section-title">字幕源</h3>
        
        <el-form :model="settings" label-position="top">
          <el-form-item label="启用的字幕源">
            <el-checkbox-group v-model="settings.subtitleSources">
              <el-checkbox label="shooter">射手网</el-checkbox>
              <el-checkbox label="assrt">Assrt</el-checkbox>
              <el-checkbox label="opensubtitles">OpenSubtitles</el-checkbox>
              <el-checkbox label="subhd">SubHD</el-checkbox>
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

          <el-divider />

          <h4 class="subsection-title">TMDB API 配置</h4>

          <el-form-item label="TMDB API Key">
            <div class="tmdb-api-input">
              <el-input
                v-model="settings.tmdbApiKey"
                placeholder="输入你的 TMDB API Key"
                show-password
                style="flex: 1;"
              />
              <button
                class="apple-button secondary"
                @click="testTMDBApi"
                :disabled="testingTMDB || !settings.tmdbApiKey"
                style="margin-left: 12px;"
              >
                {{ testingTMDB ? '测试中...' : '测试' }}
              </button>
            </div>
            <div class="form-hint">用于获取标准电影信息，可选</div>
          </el-form-item>

          <el-divider />

          <h4 class="subsection-title">NASTool 对接配置</h4>

          <el-form-item>
            <el-checkbox v-model="settings.nastoolEnabled">启用 NASTool 对接</el-checkbox>
            <div class="form-hint">接收 NASTool 的 Webhook 通知自动下载字幕</div>
          </el-form-item>

          <el-form-item label="Webhook 地址">
            <el-input
              v-model="nastoolWebhookUrl"
              readonly
              style="flex: 1;"
            />
            <div class="form-hint">在 NASTool 中配置此 Webhook 地址</div>
          </el-form-item>

          <el-form-item label="安全令牌（可选）">
            <el-input
              v-model="settings.nastoolWebhookToken"
              placeholder="输入安全令牌以增强安全性"
              show-password
            />
            <div class="form-hint">如需验证请求来源，可设置此令牌</div>
          </el-form-item>
        </el-form>
      </div>

      <!-- 高级设置 -->
      <div class="settings-section apple-card">
        <h3 class="section-title">高级设置</h3>
        
        <el-form :model="settings" label-position="top">
          <el-form-item label="主题模式">
            <div class="theme-mode-control">
              <el-radio-group v-model="themeMode" class="theme-mode-toggle">
                <el-radio-button
                  v-for="option in themeOptions"
                  :key="option.value"
                  :label="option.value"
                >
                  {{ option.label }}
                </el-radio-button>
              </el-radio-group>
              <div class="form-hint">当前生效：{{ resolvedTheme === 'oled' ? '真黑色' : '深灰' }}，切换会平滑过渡 300ms</div>
            </div>
          </el-form-item>

          <el-form-item>
            <el-checkbox v-model="settings.plexNamingFormat">使用 PLEX 字幕命名格式</el-checkbox>
            <div class="form-hint">字幕文件命名为: 视频文件名.zh-cn.srt</div>
          </el-form-item>

          <el-form-item label="Plex 服务器地址">
            <el-input
              v-model="settings.plexServerUrl"
              placeholder="例如 http://plex.local:32400"
            />
            <div class="form-hint">用于下载字幕后刷新 Plex 媒体项</div>
          </el-form-item>

          <el-form-item label="X-Plex-Token">
            <el-input
              v-model="settings.plexToken"
              type="password"
              placeholder="输入 Plex Token"
              show-password
            />
          </el-form-item>

          <el-form-item>
            <el-checkbox v-model="settings.plexRefreshAfterDownload">下载后自动刷新 Plex</el-checkbox>
            <div class="form-hint">会先触发媒体目录扫描，再尝试刷新对应媒体项元数据</div>
          </el-form-item>

          <el-form-item label="Plex 路径映射">
            <el-input
              v-model="settings.plexPathMappings"
              type="textarea"
              :rows="4"
              placeholder="/movies=/data/movies&#10;/tvshows=/data/tvshows&#10;/anime=/data/anime"
            />
            <div class="form-hint">当字幕管理器和 Plex 容器挂载路径不一致时使用，每行一条 from=to</div>
          </el-form-item>

          <el-form-item>
            <el-checkbox v-model="settings.autoDownload">自动下载字幕</el-checkbox>
          </el-form-item>

          <el-form-item label="自动下载最小延迟（秒）">
            <el-input-number v-model="settings.autoDownloadDelayMinSeconds" :min="0" :max="120" />
            <div class="form-hint">仅作用于自动扫描/自动下载链路，不影响手动搜索和手动下载</div>
          </el-form-item>

          <el-form-item label="自动下载最大延迟（秒）">
            <el-input-number v-model="settings.autoDownloadDelayMaxSeconds" :min="0" :max="180" />
            <div class="form-hint">系统会在最小值和最大值之间随机抖动，分散对字幕源的请求节奏</div>
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
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { useThemeMode } from '../composables/useThemeMode'

const saving = ref(false)
const testingTMDB = ref(false)
const { themeMode, resolvedTheme, themeOptions } = useThemeMode()

const settings = ref({
  movieDir: '/movies',
  tvDir: '/tvshows',
  animeDir: '/anime',
  scanInterval: 30,
  minFileSize: 100,
  maxConcurrent: 3,
  subtitleSources: ['shooter', 'assrt', 'opensubtitles', 'subhd'],
  openSubtitlesApiKey: '',
  openSubtitlesUsername: '',
  openSubtitlesPassword: '',
  tmdbApiKey: '',
  plexNamingFormat: true,
  plexServerUrl: '',
  plexToken: '',
  plexRefreshAfterDownload: true,
  plexPathMappings: '',
  autoDownloadDelayMinSeconds: 6,
  autoDownloadDelayMaxSeconds: 14,
  autoDownload: true,
  backupExisting: false,
  logLevel: 'INFO',
  nastoolEnabled: false,
  nastoolWebhookToken: '',
  nastoolPathMappings: '',
  apiKey: ''
})

function fetchWithApiKey(url, options = {}) {
  const apiKey = localStorage.getItem('apiKey')
  const headers = { 'Content-Type': 'application/json' }
  if (apiKey) headers['X-API-Key'] = apiKey
  return fetch(url, { ...options, headers: { ...headers, ...options.headers } })
}

// 计算 Webhook URL
const nastoolWebhookUrl = computed(() => {
  const baseUrl = window.location.origin
  const token = settings.value.nastoolWebhookToken?.trim()
  if (!token) {
    return `${baseUrl}/api/webhook/nastool`
  }
  return `${baseUrl}/api/webhook/nastool?token=${encodeURIComponent(token)}`
})

onMounted(async () => {
  // 加载设置
  try {
    const response = await fetchWithApiKey('/api/settings')
    const data = await response.json()
    // 转换数组为逗号分隔的字符串
    settings.value = {
      ...data,
      subtitleSources: Array.isArray(data.subtitleSources) ? data.subtitleSources : data.subtitleSources.split(',')
    }
    // apiKey 不从服务器返回，从本地存储读取
    settings.value.apiKey = localStorage.getItem('apiKey') || ''
  } catch (error) {
    // 如果 401 且本地有缓存的 Key，先用本地数据填充
    const cachedKey = localStorage.getItem('apiKey')
    if (error.message.includes('401') && cachedKey) {
      settings.value.apiKey = cachedKey
      ElMessage.warning('已加载本地 API Key，请确认与后台设置一致')
    } else if (error.message.includes('401')) {
      ElMessage.warning('请先在下方填写 API Key 才能管理设置')
      settings.value.apiKey = localStorage.getItem('apiKey') || ''
    } else {
      console.error('加载设置失败:', error)
      ElMessage.error('加载设置失败')
    }
  }
})

async function handleSave() {
  saving.value = true
  try {
    if (settings.value.autoDownloadDelayMaxSeconds < settings.value.autoDownloadDelayMinSeconds) {
      settings.value.autoDownloadDelayMaxSeconds = settings.value.autoDownloadDelayMinSeconds
    }

    const response = await fetchWithApiKey('/api/settings', {
      method: 'POST',
      body: JSON.stringify(settings.value)
    })

    if (!response.ok) {
      throw new Error('保存失败')
    }

    // API Key 保存到本地
    if (settings.value.apiKey) {
      localStorage.setItem('apiKey', settings.value.apiKey)
    }

    ElMessage.success('设置已保存')
  } catch (error) {
    ElMessage.error('保存失败: ' + error.message)
  } finally {
    saving.value = false
  }
}

function handleReset() {
  settings.value = {
    movieDir: '/movies',
    tvDir: '/tvshows',
    animeDir: '/anime',
    scanInterval: 30,
    minFileSize: 100,
    maxConcurrent: 3,
    subtitleSources: ['shooter', 'assrt', 'opensubtitles', 'subhd'],
    openSubtitlesApiKey: '',
    openSubtitlesUsername: '',
    openSubtitlesPassword: '',
    tmdbApiKey: '',
    plexNamingFormat: true,
    plexServerUrl: '',
    plexToken: '',
    plexRefreshAfterDownload: true,
    plexPathMappings: '',
    autoDownloadDelayMinSeconds: 6,
    autoDownloadDelayMaxSeconds: 14,
    autoDownload: true,
    backupExisting: false,
    logLevel: 'INFO',
    nastoolEnabled: false,
    nastoolWebhookToken: '',
    nastoolPathMappings: '',
    apiKey: localStorage.getItem('apiKey') || ''
  }
  ElMessage.info('设置已重置')
}

async function testTMDBApi() {
  if (!settings.value.tmdbApiKey) {
    ElMessage.warning('请先输入 TMDB API Key')
    return
  }

  testingTMDB.value = true
  try {
    const response = await fetch('/api/test-tmdb', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ api_key: settings.value.tmdbApiKey })
    })

    const data = await response.json()

    if (data.success) {
      ElMessage.success(`${data.message}\n测试电影: ${data.data.test_movie} (${data.data.year})`)
    } else {
      ElMessage.error(data.message)
    }
  } catch (error) {
    ElMessage.error('测试失败: ' + error.message)
  } finally {
    testingTMDB.value = false
  }
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
  color: var(--infuse-text-primary);
}

.subsection-title {
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 16px;
  color: var(--infuse-text-primary);
}

.form-hint {
  font-size: 12px;
  color: var(--infuse-text-muted);
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
  color: var(--infuse-text-primary);
}

:deep(.el-checkbox__label) {
  color: var(--infuse-text-primary);
}

.tmdb-api-input {
  display: flex;
  align-items: flex-start;
}

.theme-mode-control {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.theme-mode-toggle {
  width: fit-content;
}

.theme-mode-toggle :deep(.el-radio-button__inner) {
  min-width: 108px;
  background: rgba(255, 255, 255, 0.04);
  border-color: rgba(255, 255, 255, 0.08);
  color: var(--infuse-text-secondary);
}

.theme-mode-toggle :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background: linear-gradient(135deg, rgba(34, 246, 255, 0.88), rgba(255, 43, 214, 0.8));
  color: #04111c;
  border-color: transparent;
}

@media (max-width: 768px) {
  .settings-section {
    padding: 18px;
    margin-bottom: 18px;
  }

  .settings-actions {
    flex-direction: column-reverse;
  }

  .settings-actions .apple-button,
  .tmdb-api-input .apple-button {
    width: 100%;
  }

  .tmdb-api-input {
    flex-direction: column;
    gap: 10px;
  }

  .theme-mode-toggle {
    width: 100%;
  }
}
</style>
