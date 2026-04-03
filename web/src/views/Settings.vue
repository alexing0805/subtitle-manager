<template>
  <div class="settings">
    <header class="page-header">
      <h1 class="page-title">设置</h1>
      <p class="page-subtitle">配置字幕管理器</p>
    </header>

    <div class="settings-overview">
      <div class="overview-card apple-card">
        <span class="overview-label">媒体库目录</span>
        <strong class="overview-value">3 个</strong>
        <span class="overview-desc">电影 / 电视剧 / 动漫已独立分区</span>
      </div>
      <div class="overview-card apple-card">
        <span class="overview-label">字幕源</span>
        <strong class="overview-value">{{ enabledSourceCount }} / 4</strong>
        <span class="overview-desc">按源站能力与账号配置分组管理</span>
      </div>
      <div class="overview-card apple-card">
        <span class="overview-label">自动化</span>
        <strong class="overview-value">{{ settings.autoDownload ? '开启' : '关闭' }}</strong>
        <span class="overview-desc">扫描、延迟、备份与命名集中配置</span>
      </div>
      <div class="overview-card apple-card">
        <span class="overview-label">外部联动</span>
        <strong class="overview-value">{{ settings.nastoolEnabled ? 'NASTool 已启用' : 'NASTool 未启用' }}</strong>
        <span class="overview-desc">{{ hasPlexConfigured ? 'Plex 已配置' : 'Plex 尚未配置' }}</span>
      </div>
    </div>

    <div class="settings-form">
      <div class="settings-section apple-card">
        <div class="section-header">
          <div class="section-title-wrap">
            <h3 class="section-title">媒体库与扫描</h3>
            <p class="section-description">把目录、扫描频率和并发限制放在一起，专门管“从哪里扫、多久扫一次、一次跑多猛”。</p>
          </div>
          <span class="section-badge">基础运行区</span>
        </div>

        <div class="section-grid">
          <div class="form-card">
            <div class="form-card-title">媒体库目录</div>
            <div class="form-card-desc">分别指定电影、电视剧、动漫的根目录，后续自动识别和页面统计都会基于这里。</div>
            <el-form :model="settings" label-position="top" class="settings-form-block">
              <el-form-item label="电影目录">
                <el-input v-model="settings.movieDir" placeholder="/movies" />
              </el-form-item>
              <el-form-item label="电视剧目录">
                <el-input v-model="settings.tvDir" placeholder="/tvshows" />
              </el-form-item>
              <el-form-item label="动漫目录">
                <el-input v-model="settings.animeDir" placeholder="/anime" />
              </el-form-item>
            </el-form>
          </div>

          <div class="form-card">
            <div class="form-card-title">扫描策略</div>
            <div class="form-card-desc">控制定时扫描节奏、过滤掉过小文件，并限制同时进行的下载任务数量。</div>
            <el-form :model="settings" label-position="top" class="settings-form-block">
              <el-form-item label="扫描间隔（分钟）">
                <el-slider v-model="settings.scanInterval" :min="0" :max="120" :step="5" show-stops />
                <div class="form-hint">设为 0 可关闭定时扫描，只保留手动扫描或外部触发。</div>
              </el-form-item>
              <el-form-item label="文件大小阈值（MB）">
                <el-input-number v-model="settings.minFileSize" :min="10" :max="1000" :step="10" />
                <div class="form-hint">避免把样片、预告和异常小文件误判成正片。</div>
              </el-form-item>
              <el-form-item label="最大并发下载数">
                <el-input-number v-model="settings.maxConcurrent" :min="1" :max="10" />
                <div class="form-hint">如果源站容易限流，建议保持在 2~4 之间。</div>
              </el-form-item>
            </el-form>
          </div>
        </div>
      </div>

      <div class="settings-section apple-card">
        <div class="section-header">
          <div class="section-title-wrap">
            <h3 class="section-title">字幕源与识别</h3>
            <p class="section-description">把字幕源开关、TMDB 识别和 OpenSubtitles 账号信息拆开，哪块有问题一眼能看见。</p>
          </div>
          <span class="section-badge">检索能力区</span>
        </div>

        <div class="section-grid">
          <div class="form-card">
            <div class="form-card-title">字幕源开关</div>
            <div class="form-card-desc">优先启用常用且稳定的源，结合你的账号配置决定搜索范围。</div>
            <el-form :model="settings" label-position="top" class="settings-form-block">
              <el-form-item label="启用的字幕源">
                <el-checkbox-group v-model="settings.subtitleSources" class="checkbox-grid">
                  <el-checkbox label="shooter">射手网</el-checkbox>
                  <el-checkbox label="assrt">Assrt</el-checkbox>
                  <el-checkbox label="opensubtitles">OpenSubtitles</el-checkbox>
                  <el-checkbox label="subhd">SubHD</el-checkbox>
                </el-checkbox-group>
                <div class="form-hint">当前已启用 {{ enabledSourceCount }} 个源；建议至少保留 2 个，以免单站超时影响体验。</div>
              </el-form-item>
            </el-form>
          </div>

          <div class="form-card">
            <div class="form-card-title">TMDB 媒体识别</div>
            <div class="form-card-desc">用于补全电影与剧集元数据，提升匹配精度，尤其是外语片和重名内容。</div>
            <el-form :model="settings" label-position="top" class="settings-form-block">
              <el-form-item label="TMDB API Key">
                <div class="inline-input">
                  <el-input v-model="settings.tmdbApiKey" placeholder="输入你的 TMDB API Key" show-password />
                  <button type="button" class="apple-button secondary compact" @click="testTMDBApi" :disabled="testingTMDB || !settings.tmdbApiKey">
                    {{ testingTMDB ? '测试中...' : '测试连接' }}
                  </button>
                </div>
                <div class="form-hint">建议配置。没有它也能用，但复杂命名的识别稳定性会差一截。</div>
              </el-form-item>
            </el-form>
          </div>

          <div class="form-card full-span">
            <div class="form-card-title">OpenSubtitles 账号</div>
            <div class="form-card-desc">把凭据单独放一个区，避免跟其他源设置搅在一起；没账号也不影响其余源站工作。</div>
            <el-form :model="settings" label-position="top" class="settings-form-block form-grid-3">
              <el-form-item label="API Key">
                <el-input v-model="settings.openSubtitlesApiKey" placeholder="输入 API Key" show-password />
              </el-form-item>
              <el-form-item label="用户名">
                <el-input v-model="settings.openSubtitlesUsername" placeholder="输入用户名" />
              </el-form-item>
              <el-form-item label="密码">
                <el-input v-model="settings.openSubtitlesPassword" type="password" placeholder="输入密码" show-password />
              </el-form-item>
            </el-form>
          </div>
        </div>
      </div>

      <div class="settings-section apple-card">
        <div class="section-header">
          <div class="section-title-wrap">
            <h3 class="section-title">自动化与字幕文件策略</h3>
            <p class="section-description">这里专门管下载节奏、命名格式和备份策略，避免“触发逻辑”和“文件落盘逻辑”混在一起。</p>
          </div>
          <span class="section-badge">下载行为区</span>
        </div>

        <div class="section-grid">
          <div class="form-card">
            <div class="form-card-title">自动下载开关</div>
            <div class="form-card-desc">决定是否在自动扫描、Webhook 触发等链路里自动挑选并下载字幕。</div>
            <el-form :model="settings" label-position="top" class="settings-form-block">
              <el-form-item>
                <el-checkbox v-model="settings.autoDownload">自动下载字幕</el-checkbox>
                <div class="form-hint">关闭后，系统仍可搜索字幕，但需要你手动确认下载。</div>
              </el-form-item>
              <el-form-item label="自动下载最小延迟（秒）">
                <el-input-number v-model="settings.autoDownloadDelayMinSeconds" :min="0" :max="120" />
                <div class="form-hint">仅作用于自动链路，不影响手动搜索和手动下载。</div>
              </el-form-item>
              <el-form-item label="自动下载最大延迟（秒）">
                <el-input-number v-model="settings.autoDownloadDelayMaxSeconds" :min="0" :max="180" />
                <div class="form-hint">系统会在区间内随机抖动，分散对字幕源的请求节奏。</div>
              </el-form-item>
            </el-form>
          </div>

          <div class="form-card">
            <div class="form-card-title">文件命名与备份</div>
            <div class="form-card-desc">控制字幕文件命名是否偏向 Plex 习惯，以及覆盖前是否先备份已有字幕。</div>
            <el-form :model="settings" label-position="top" class="settings-form-block">
              <el-form-item>
                <el-checkbox v-model="settings.plexNamingFormat">使用 Plex 字幕命名格式</el-checkbox>
                <div class="form-hint">字幕文件命名为：视频文件名.zh-cn.srt，更适合 Plex 自动识别。</div>
              </el-form-item>
              <el-form-item>
                <el-checkbox v-model="settings.backupExisting">下载前备份原字幕</el-checkbox>
                <div class="form-hint">适合你还在调试字幕源或路径规则时使用，回滚更安心。</div>
              </el-form-item>
            </el-form>
          </div>
        </div>
      </div>

      <div class="settings-section apple-card">
        <div class="section-header">
          <div class="section-title-wrap">
            <h3 class="section-title">外部联动</h3>
            <p class="section-description">把 NASTool 与 Plex 单独拎出来，路径映射、Webhook、安全令牌和刷新策略都放在这里。</p>
          </div>
          <span class="section-badge">集成联动区</span>
        </div>

        <div class="section-grid">
          <div class="form-card">
            <div class="form-card-title">NASTool Webhook</div>
            <div class="form-card-desc">用于接收下载完成、转移完成等事件并自动尝试补字幕；现在也会兼容更多路径字段。</div>
            <el-form :model="settings" label-position="top" class="settings-form-block">
              <el-form-item>
                <el-checkbox v-model="settings.nastoolEnabled">启用 NASTool 对接</el-checkbox>
                <div class="form-hint">启用后，NASTool 的 Webhook 通知会触发本地字幕任务。</div>
              </el-form-item>
              <el-form-item label="Webhook 地址">
                <div class="inline-input">
                  <el-input :model-value="nastoolWebhookUrl" readonly />
                  <button type="button" class="apple-button secondary compact" @click="copyToClipboard(nastoolWebhookUrl, 'Webhook 地址')">复制</button>
                  <button type="button" class="apple-button secondary compact" @click="testNastoolWebhook" :disabled="testingNastool">
                    {{ testingNastool ? '检测中...' : '接口自检' }}
                  </button>
                </div>
                <div class="form-hint">在 NASTool 中直接填这个地址；如果设置了令牌，地址会自动带上 token 参数。</div>
              </el-form-item>
              <el-form-item label="安全令牌（可选）">
                <el-input v-model="settings.nastoolWebhookToken" placeholder="输入安全令牌以增强安全性" show-password />
                <div class="form-hint">配置后会校验请求来源，避免外部误触发。</div>
              </el-form-item>
              <el-form-item label="NASTool 路径映射">
                <el-input
                  v-model="settings.nastoolPathMappings"
                  type="textarea"
                  :rows="4"
                  placeholder="/downloads=/movies&#10;/media/tv=/tvshows&#10;/media/anime=/anime"
                />
                <div class="form-hint">当 NASTool 与字幕管理器的容器挂载路径不一致时使用，每行一条 from=to。</div>
              </el-form-item>
            </el-form>
            <div class="helper-panel">
              <div class="helper-panel-title">当前建议</div>
              <div class="tag-list">
                <span v-for="event in supportedNastoolEvents" :key="event.value" class="helper-tag">{{ event.label }} · {{ event.value }}</span>
              </div>
              <ul class="helper-list">
                <li>优先让 NASTool 在“下载完成 / 转移完成”后再发 Webhook，路径最稳定。</li>
                <li>如果容器路径不同，优先配好路径映射，再看日志排查。</li>
                <li>现在会额外尝试识别 path / filepath / target_path / media_info.* 这类字段。</li>
              </ul>
            </div>

            <div class="nastool-debug-grid">
              <div class="debug-card">
                <div class="debug-card-header">
                  <div>
                    <div class="debug-card-title">最近一次自检</div>
                    <div class="debug-card-desc">会保存在当前浏览器，方便你回头看上次接口状态。</div>
                  </div>
                  <span class="status-pill" :class="nastoolSelfTestSummary.tone">{{ nastoolSelfTestSummary.title }}</span>
                </div>
                <div class="self-test-panel" :class="nastoolSelfTestSummary.tone">
                  <strong>{{ nastoolSelfTestSummary.detail }}</strong>
                  <span v-if="nastoolSelfTestSummary.time">检查时间：{{ nastoolSelfTestSummary.time }}</span>
                  <span v-else>还没有执行过接口自检</span>
                </div>
              </div>

              <div class="debug-card">
                <div class="debug-card-header">
                  <div>
                    <div class="debug-card-title">路径映射预览</div>
                    <div class="debug-card-desc">不需要真等 NASTool 发请求，先看 from=to 会把路径映射成什么。</div>
                  </div>
                  <span class="status-pill neutral">{{ mappingPreviewRows.length }} 条规则</span>
                </div>
                <div v-if="mappingPreviewRows.length" class="mapping-preview-list">
                  <div v-for="row in mappingPreviewRows" :key="row.id" class="mapping-preview-item">
                    <div class="mapping-pair"><span>源路径</span><code>{{ row.sampleInput }}</code></div>
                    <div class="mapping-arrow">→</div>
                    <div class="mapping-pair"><span>映射结果</span><code>{{ row.sampleOutput }}</code></div>
                  </div>
                </div>
                <div v-else class="empty-state-note">还没配置有效的路径映射；如果两个容器挂载一致，这里可以留空。</div>
              </div>

              <div class="debug-card full-width">
                <div class="debug-card-header">
                  <div>
                    <div class="debug-card-title">示例 Payload</div>
                    <div class="debug-card-desc">可直接对照 NASTool 发来的 JSON 看字段差异，排查时特别省时间。</div>
                  </div>
                  <button type="button" class="apple-button secondary compact" @click="copyToClipboard(exampleNastoolPayload, '示例 Payload')">复制示例</button>
                </div>
                <pre class="code-block">{{ exampleNastoolPayload }}</pre>
              </div>
            </div>
          </div>

          <div class="form-card">
            <div class="form-card-title">Plex 刷新</div>
            <div class="form-card-desc">字幕下载完成后，可以主动通知 Plex 重扫媒体项，减少你手动点刷新的次数。</div>
            <el-form :model="settings" label-position="top" class="settings-form-block">
              <el-form-item label="Plex 服务器地址">
                <el-input v-model="settings.plexServerUrl" placeholder="例如 http://plex.local:32400" />
                <div class="form-hint">用于下载字幕后触发 Plex 刷新或元数据更新。</div>
              </el-form-item>
              <el-form-item label="X-Plex-Token">
                <el-input v-model="settings.plexToken" type="password" placeholder="输入 Plex Token" show-password />
              </el-form-item>
              <el-form-item>
                <el-checkbox v-model="settings.plexRefreshAfterDownload">下载后自动刷新 Plex</el-checkbox>
                <div class="form-hint">会先尝试触发媒体目录扫描，再刷新对应媒体项。</div>
              </el-form-item>
              <el-form-item label="Plex 路径映射">
                <el-input
                  v-model="settings.plexPathMappings"
                  type="textarea"
                  :rows="4"
                  placeholder="/movies=/data/movies&#10;/tvshows=/data/tvshows&#10;/anime=/data/anime"
                />
                <div class="form-hint">当字幕管理器和 Plex 容器挂载路径不一致时使用，每行一条 from=to。</div>
              </el-form-item>
            </el-form>
          </div>
        </div>
      </div>

      <div class="settings-section apple-card">
        <div class="section-header compact">
          <div class="section-title-wrap">
            <h3 class="section-title">界面与安全</h3>
            <p class="section-description">把主题、日志和 API Key 放到最后，属于“系统体验层”和“访问控制层”。</p>
          </div>
          <span class="section-badge">系统体验区</span>
        </div>

        <div class="section-grid">
          <div class="form-card full-span">
            <div class="form-card-title">主题模式</div>
            <div class="form-card-desc">主题切换只保存在本地浏览器；我顺手把浅色模式的文字对比度也整体提了一档。</div>
            <el-form :model="settings" label-position="top" class="settings-form-block">
              <el-form-item label="主题模式">
                <div class="theme-mode-control">
                  <el-radio-group v-model="themeMode" class="theme-mode-toggle">
                    <el-radio-button v-for="option in themeOptions" :key="option.value" :label="option.value">
                      <span class="theme-option-label">{{ option.label }}</span>
                    </el-radio-button>
                  </el-radio-group>
                  <div class="theme-mode-summary">
                    <strong>当前生效：{{ themeResolvedLabel }}</strong>
                    <span>设置会保存到本地浏览器，下次打开继续生效；切换时保留平滑过渡。</span>
                  </div>
                  <div class="theme-option-notes">
                    <div v-for="option in themeOptions" :key="`${option.value}-note`" class="theme-note-card" :class="{ active: themeMode === option.value }">
                      <span>{{ option.label }}</span>
                      <p>{{ option.description }}</p>
                    </div>
                  </div>
                </div>
              </el-form-item>
            </el-form>
          </div>

          <div class="form-card">
            <div class="form-card-title">日志与诊断</div>
            <div class="form-card-desc">调试联动问题时，把日志级别提到 DEBUG 会舒服很多；日常建议保持 INFO。</div>
            <el-form :model="settings" label-position="top" class="settings-form-block">
              <el-form-item label="日志级别">
                <el-select v-model="settings.logLevel" class="full-width-select">
                  <el-option label="DEBUG" value="DEBUG" />
                  <el-option label="INFO" value="INFO" />
                  <el-option label="WARNING" value="WARNING" />
                  <el-option label="ERROR" value="ERROR" />
                </el-select>
              </el-form-item>
            </el-form>
          </div>

          <div class="form-card">
            <div class="form-card-title">API Key</div>
            <div class="form-card-desc">用于保护设置、扫描、下载等接口访问；保存在浏览器本地，不会回显后端里的值。</div>
            <el-form :model="settings" label-position="top" class="settings-form-block">
              <el-form-item label="管理 API Key">
                <el-input v-model="settings.apiKey" type="password" placeholder="留空表示不设置" show-password />
                <div class="form-hint">如果你换了浏览器或设备，需要重新填一次本地缓存的 API Key。</div>
              </el-form-item>
            </el-form>
          </div>
        </div>
      </div>

      <div class="settings-actions">
        <button type="button" class="apple-button secondary" @click="handleReset">重置</button>
        <button type="button" class="apple-button" @click="handleSave" :disabled="saving">
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
const testingNastool = ref(false)
const nastoolSelfTestResult = ref(null)
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

const enabledSourceCount = computed(() => settings.value.subtitleSources.length)
const hasPlexConfigured = computed(() => Boolean(settings.value.plexServerUrl?.trim() && settings.value.plexToken?.trim()))
const themeResolvedLabel = computed(() => (
  resolvedTheme.value === 'oled' ? '真黑' : resolvedTheme.value === 'light' ? '浅色' : '深灰'
))
const supportedNastoolEvents = [
  { value: 'download.completed', label: '下载完成' },
  { value: 'media.scraped', label: '媒体刮削完成' },
  { value: 'transfer.completed', label: '文件转移完成' },
  { value: 'subtitle.missing', label: '字幕缺失' }
]

const parsedNastoolMappings = computed(() => {
  return (settings.value.nastoolPathMappings || '')
    .split('\n')
    .map(line => line.trim())
    .filter(Boolean)
    .map((line, index) => {
      const [from, to] = line.split('=', 2).map(part => (part || '').trim())
      return {
        id: `${index}-${from}-${to}`,
        from,
        to,
        valid: Boolean(from && to)
      }
    })
})

const sampleNastoolInputPath = computed(() => {
  const firstValidMapping = parsedNastoolMappings.value.find(item => item.valid)
  const base = firstValidMapping?.from || '/downloads'
  return `${base.replace(/[\\/]$/, '')}/电视剧/3 Body Problem/Season 1/3.Body.Problem.S01E01.2160p.WEB-DL.mkv`
})

const sampleMappedOutputPath = computed(() => applyPathMappings(sampleNastoolInputPath.value, parsedNastoolMappings.value))

const mappingPreviewRows = computed(() => {
  return parsedNastoolMappings.value
    .filter(item => item.valid)
    .map(item => {
      const sampleInput = `${item.from.replace(/[\\/]$/, '')}/示例媒体/Season 1/Demo.S01E01.mkv`
      return {
        ...item,
        sampleInput,
        sampleOutput: applyPathMappings(sampleInput, [item])
      }
    })
})

const exampleNastoolPayload = computed(() => JSON.stringify({
  event: 'transfer.completed',
  type: 'tv',
  title: '3 Body Problem',
  year: 2024,
  file_path: sampleNastoolInputPath.value,
  file_name: '3.Body.Problem.S01E01.2160p.WEB-DL.mkv',
  tmdb_id: '42009',
  season: 1,
  episode: 1,
  quality: '2160p WEB-DL',
  media_info: {
    path: sampleNastoolInputPath.value,
    target_path: sampleMappedOutputPath.value,
    media_type: 'tv',
    title: '3 Body Problem',
    season_number: 1,
    episode_number: 1,
    year: 2024
  }
}, null, 2))

const nastoolSelfTestSummary = computed(() => {
  const result = nastoolSelfTestResult.value
  if (!result) {
    return {
      tone: 'idle',
      title: '还没有自检记录',
      detail: '点一次“接口自检”后，这里会保留最近结果，方便你回头排查。',
      time: ''
    }
  }

  return {
    tone: result.ok ? 'success' : 'danger',
    title: result.ok ? '最近一次自检通过' : '最近一次自检失败',
    detail: result.message,
    time: result.timeLabel
  }
})

onMounted(async () => {
  const cachedSelfTest = localStorage.getItem('nastoolSelfTestResult')
  if (cachedSelfTest) {
    try {
      nastoolSelfTestResult.value = JSON.parse(cachedSelfTest)
    } catch {
      localStorage.removeItem('nastoolSelfTestResult')
    }
  }

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

    const data = await response.json().catch(() => ({}))

    if (!response.ok || data?.success === false) {
      throw new Error(data?.detail || data?.message || '保存失败')
    }

    // API Key 保存到本地
    if (settings.value.apiKey) {
      localStorage.setItem('apiKey', settings.value.apiKey)
    } else {
      localStorage.removeItem('apiKey')
    }

    ElMessage.success(data?.message || '设置已保存')
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
      ElMessage.success('测试成功')
    } else {
      ElMessage.error('测试失败')
    }
  } catch (error) {
    ElMessage.error('测试失败')
  } finally {
    testingTMDB.value = false
  }
}

async function copyToClipboard(value, label = '内容') {
  if (!value) {
    ElMessage.warning(`${label}为空`)
    return
  }

  try {
    await navigator.clipboard.writeText(value)
    ElMessage.success(`${label}已复制`)
  } catch (error) {
    ElMessage.error(`复制${label}失败`)
  }
}

function applyPathMappings(inputPath, mappings) {
  const normalizedInput = (inputPath || '').trim().replace(/\\\\/g, '/')
  for (const mapping of mappings) {
    if (!mapping?.valid) continue
    const from = mapping.from.replace(/\\\\/g, '/').replace(/\/$/, '')
    const to = mapping.to.replace(/\\\\/g, '/').replace(/\/$/, '')
    if (normalizedInput === from || normalizedInput.startsWith(`${from}/`)) {
      const suffix = normalizedInput.slice(from.length).replace(/^\//, '')
      return suffix ? `${to}/${suffix}` : to
    }
  }
  return normalizedInput
}

function formatDateTime(date = new Date()) {
  return new Intl.DateTimeFormat('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  }).format(date)
}

function persistNastoolSelfTest(result) {
  nastoolSelfTestResult.value = result
  localStorage.setItem('nastoolSelfTestResult', JSON.stringify(result))
}

async function testNastoolWebhook() {
  testingNastool.value = true
  try {
    const response = await fetchWithApiKey('/api/webhook/nastool/test')
    const data = await response.json()
    if (!response.ok || data.status !== 'ok') {
      throw new Error(data?.message || 'NASTool Webhook 自检失败')
    }

    const result = {
      ok: true,
      message: `接口正常，当前支持 ${data.supported_events?.length || 0} 种事件`,
      endpoint: data.endpoint,
      checkedAt: new Date().toISOString(),
      timeLabel: formatDateTime(new Date())
    }
    persistNastoolSelfTest(result)
    ElMessage.success(`NASTool Webhook 正常，支持 ${data.supported_events?.length || 0} 种事件`)
  } catch (error) {
    const result = {
      ok: false,
      message: error.message || 'NASTool Webhook 自检失败',
      endpoint: '/api/webhook/nastool/test',
      checkedAt: new Date().toISOString(),
      timeLabel: formatDateTime(new Date())
    }
    persistNastoolSelfTest(result)
    ElMessage.error(error.message || 'NASTool Webhook 自检失败')
  } finally {
    testingNastool.value = false
  }
}
</script>

<style scoped>
.settings {
  max-width: 1120px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.settings-overview {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
}

.overview-card {
  padding: 18px 20px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  border: 1px solid var(--infuse-border);
  background: var(--infuse-gradient-card);
  box-shadow: var(--infuse-shadow-sm);
}

.overview-label {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--infuse-text-secondary);
}

.overview-value {
  font-size: 24px;
  line-height: 1.1;
  color: var(--infuse-text-primary);
}

.overview-desc {
  font-size: 13px;
  line-height: 1.5;
  color: var(--infuse-text-tertiary);
}

.settings-form {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.settings-section {
  padding: 28px;
  border: 1px solid var(--infuse-border);
  box-shadow: var(--infuse-shadow-sm);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 22px;
}

.section-header.compact {
  margin-bottom: 18px;
}

.section-title-wrap {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.section-title {
  margin: 0;
  font-size: 20px;
  font-weight: 700;
  color: var(--infuse-text-primary);
}

.section-description {
  margin: 0;
  max-width: 760px;
  font-size: 14px;
  line-height: 1.65;
  color: var(--infuse-text-secondary);
}

.section-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 8px 12px;
  border-radius: 999px;
  border: 1px solid var(--infuse-border);
  background: var(--infuse-bg-tertiary);
  color: var(--infuse-text-secondary);
  font-size: 12px;
  font-weight: 700;
  white-space: nowrap;
}

.section-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.form-card {
  padding: 20px;
  border-radius: 20px;
  border: 1px solid var(--infuse-border);
  background: var(--infuse-bg-secondary);
}

.form-card.full-span {
  grid-column: 1 / -1;
}

.form-card-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--infuse-text-primary);
}

.form-card-desc {
  margin-top: 6px;
  margin-bottom: 18px;
  font-size: 13px;
  line-height: 1.6;
  color: var(--infuse-text-secondary);
}

.settings-form-block :deep(.el-form-item) {
  margin-bottom: 18px;
}

.settings-form-block :deep(.el-form-item:last-child) {
  margin-bottom: 0;
}

.form-grid-3 {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0 14px;
}

.checkbox-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px 16px;
}

.inline-input {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.inline-input :deep(.el-input) {
  flex: 1;
}

.full-width-select {
  width: 100%;
}

.helper-panel {
  margin-top: 16px;
  padding: 16px 18px;
  border-radius: 18px;
  border: 1px solid var(--infuse-border);
  background: var(--infuse-gradient-neon);
}

.helper-panel-title {
  font-size: 13px;
  font-weight: 700;
  color: var(--infuse-text-primary);
  margin-bottom: 10px;
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}

.helper-tag {
  display: inline-flex;
  align-items: center;
  padding: 6px 10px;
  border-radius: 999px;
  background: var(--infuse-bg-card);
  border: 1px solid var(--infuse-border);
  color: var(--infuse-text-secondary);
  font-size: 12px;
  font-weight: 600;
}

.helper-list {
  margin: 0;
  padding-left: 18px;
  display: grid;
  gap: 8px;
  color: var(--infuse-text-secondary);
  line-height: 1.6;
}

.nastool-debug-grid {
  margin-top: 18px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.debug-card {
  padding: 18px;
  border-radius: 18px;
  border: 1px solid var(--infuse-border);
  background: var(--infuse-bg-card);
  box-shadow: var(--infuse-shadow-sm);
}

.debug-card.full-width {
  grid-column: 1 / -1;
}

.debug-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 14px;
}

.debug-card-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--infuse-text-primary);
}

.debug-card-desc {
  margin-top: 4px;
  font-size: 12px;
  line-height: 1.55;
  color: var(--infuse-text-secondary);
}

.status-pill {
  display: inline-flex;
  align-items: center;
  padding: 6px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
  white-space: nowrap;
  border: 1px solid var(--infuse-border);
}

.status-pill.success {
  background: rgba(52, 199, 89, 0.12);
  color: #15803d;
  border-color: rgba(52, 199, 89, 0.28);
}

.status-pill.danger {
  background: rgba(239, 68, 68, 0.12);
  color: #b91c1c;
  border-color: rgba(239, 68, 68, 0.24);
}

.status-pill.idle,
.status-pill.neutral {
  background: var(--infuse-bg-tertiary);
  color: var(--infuse-text-secondary);
}

.self-test-panel {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 14px 16px;
  border-radius: 16px;
  border: 1px solid var(--infuse-border);
  color: var(--infuse-text-secondary);
}

.self-test-panel strong {
  color: var(--infuse-text-primary);
}

.self-test-panel.success {
  background: rgba(52, 199, 89, 0.08);
  border-color: rgba(52, 199, 89, 0.22);
}

.self-test-panel.danger {
  background: rgba(239, 68, 68, 0.08);
  border-color: rgba(239, 68, 68, 0.22);
}

.mapping-preview-list {
  display: grid;
  gap: 12px;
}

.mapping-preview-item {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  gap: 12px;
  align-items: center;
  padding: 14px;
  border-radius: 16px;
  border: 1px solid var(--infuse-border);
  background: var(--infuse-bg-secondary);
}

.mapping-pair {
  display: grid;
  gap: 8px;
}

.mapping-pair span {
  font-size: 12px;
  font-weight: 700;
  color: var(--infuse-text-secondary);
}

.mapping-arrow {
  font-size: 18px;
  font-weight: 700;
  color: var(--infuse-accent);
}

.code-block,
.mapping-pair code {
  display: block;
  margin: 0;
  padding: 12px 14px;
  border-radius: 14px;
  background: rgba(15, 23, 42, 0.06);
  color: var(--infuse-text-primary);
  font-family: 'SFMono-Regular', 'JetBrains Mono', ui-monospace, monospace;
  font-size: 12px;
  line-height: 1.65;
  white-space: pre-wrap;
  word-break: break-all;
}

.code-block {
  max-height: 360px;
  overflow: auto;
}

.empty-state-note {
  padding: 14px 16px;
  border-radius: 16px;
  background: var(--infuse-bg-secondary);
  border: 1px dashed var(--infuse-border);
  color: var(--infuse-text-secondary);
  font-size: 13px;
  line-height: 1.6;
}

.form-hint {
  margin-top: 6px;
  font-size: 12px;
  line-height: 1.6;
  color: var(--infuse-text-secondary);
}

.settings-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 8px;
}

.compact {
  min-width: 108px;
}

:deep(.el-form-item__label) {
  font-weight: 600;
  color: var(--infuse-text-primary);
}

:deep(.el-checkbox__label) {
  color: var(--infuse-text-primary);
}

:deep(.el-input__wrapper),
:deep(.el-textarea__inner),
:deep(.el-select__wrapper) {
  background: var(--infuse-bg-card);
  color: var(--infuse-text-primary);
  box-shadow: 0 0 0 1px var(--infuse-border) inset;
}

:deep(.el-input__inner),
:deep(.el-textarea__inner) {
  color: var(--infuse-text-primary);
}

:deep(.el-input__inner::placeholder),
:deep(.el-textarea__inner::placeholder) {
  color: var(--infuse-text-muted);
}

:deep(.el-input-number),
:deep(.el-input-number .el-input__wrapper) {
  width: 100%;
}

.theme-mode-control {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.theme-mode-toggle {
  width: fit-content;
  max-width: 100%;
}

.theme-mode-toggle :deep(.el-radio-button__inner) {
  min-width: 108px;
  background: var(--infuse-bg-card);
  border-color: var(--infuse-border);
  color: var(--infuse-text-primary);
}

.theme-mode-toggle :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background: linear-gradient(135deg, rgba(34, 246, 255, 0.9), rgba(255, 43, 214, 0.82));
  color: #04111c;
  border-color: transparent;
}

.theme-option-label {
  font-weight: 700;
}

.theme-mode-summary {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 13px;
  color: var(--infuse-text-secondary);
}

.theme-mode-summary strong {
  color: var(--infuse-text-primary);
}

.theme-option-notes {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.theme-note-card {
  padding: 14px;
  border-radius: 16px;
  border: 1px solid var(--infuse-border);
  background: var(--infuse-bg-card);
  transition: all 0.25s ease;
}

.theme-note-card span {
  display: block;
  font-weight: 700;
  margin-bottom: 6px;
  color: var(--infuse-text-primary);
}

.theme-note-card p {
  margin: 0;
  font-size: 12px;
  line-height: 1.55;
  color: var(--infuse-text-secondary);
}

.theme-note-card.active {
  border-color: rgba(34, 246, 255, 0.32);
  background: linear-gradient(135deg, rgba(34, 246, 255, 0.12), rgba(255, 43, 214, 0.08));
  box-shadow: var(--infuse-shadow-sm);
}

@media (max-width: 1024px) {
  .settings-overview,
  .section-grid,
  .form-grid-3,
  .theme-option-notes {
    grid-template-columns: 1fr 1fr;
  }

  .form-grid-3 :deep(.el-form-item:last-child) {
    grid-column: 1 / -1;
  }
}

@media (max-width: 768px) {
  .settings-overview,
  .section-grid,
  .form-grid-3,
  .theme-option-notes,
  .checkbox-grid,
  .nastool-debug-grid {
    grid-template-columns: 1fr;
  }

  .settings-section {
    padding: 20px;
  }

  .section-header,
  .debug-card-header,
  .mapping-preview-item {
    flex-direction: column;
  }

  .mapping-preview-item {
    display: flex;
    align-items: stretch;
  }

  .mapping-arrow {
    align-self: center;
    transform: rotate(90deg);
  }

  .inline-input,
  .settings-actions {
    flex-direction: column;
  }

  .settings-actions {
    flex-direction: column-reverse;
  }

  .settings-actions .apple-button,
  .inline-input .apple-button,
  .theme-mode-toggle,
  .debug-card-header .apple-button,
  .status-pill {
    width: 100%;
  }

  .theme-mode-toggle :deep(.el-radio-button__inner) {
    min-width: 0;
  }
}
</style>
