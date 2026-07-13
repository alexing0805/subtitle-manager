<template>
  <el-dialog
    :model-value="visible"
    width="860px"
    top="6vh"
    class="infuse-dialog scan-visualization-dialog"
    :show-close="!status.isScanning"
    @update:model-value="emit('update:visible', $event)"
  >
    <template #header>
      <div class="scan-header">
        <div>
          <div class="scan-kicker">扫描可视化</div>
          <h3>{{ title }}</h3>
          <p>{{ status.message || phaseCopy }}</p>
        </div>
        <div class="scan-progress-chip" :class="phaseClass">
          <span>{{ phaseLabel }}</span>
          <strong>{{ progressLabel }}</strong>
        </div>
      </div>
    </template>

    <div class="scan-visualization">
      <section class="scan-hero" :class="phaseClass">
        <div class="scan-hero-copy">
          <span class="status-label">当前扫描目录</span>
          <strong>{{ status.currentPath || '等待扫描器回传路径…' }}</strong>
          <p>{{ currentDirectoryName }}</p>
        </div>
        <div class="scan-hero-meter">
          <div class="meter-ring" :style="{ '--progress': safeProgress }">
            <div class="meter-ring-inner">
              <span>进度</span>
              <strong>{{ progressLabel }}</strong>
            </div>
          </div>
          <div class="meter-track">
            <div class="meter-fill" :style="{ width: `${safeProgress}%` }"></div>
          </div>
          <div class="meter-copy">{{ progressHint }}</div>
        </div>
      </section>

      <section class="scan-status-grid">
        <div class="scan-status-card primary-card">
          <div class="card-heading">
            <span class="status-label">扫描现场</span>
            <span class="phase-pill" :class="phaseClass">{{ phaseLabel }}</span>
          </div>
          <div class="path-panel">
            <div class="path-name">{{ currentDirectoryName }}</div>
            <div class="path-full">{{ status.currentPath || '等待目录路径…' }}</div>
          </div>
          <div class="pulse-row">
            <span class="pulse-dot"></span>
            <span>{{ progressHint }}</span>
          </div>
        </div>

        <div class="scan-status-card metrics-card">
          <div class="card-heading">
            <span class="status-label">进度反馈</span>
            <span class="metric-total">{{ status.totalDiscoveredMedia || 0 }} 个媒体</span>
          </div>
          <div class="status-stats">
            <div class="status-stat emphasis">
              <span>已发现媒体</span>
              <strong>{{ status.totalDiscoveredMedia || 0 }}</strong>
            </div>
            <div class="status-stat">
              <span>当前目录媒体</span>
              <strong>{{ status.currentPathMediaCount || 0 }}</strong>
            </div>
            <div class="status-stat">
              <span>已扫描目录</span>
              <strong>{{ status.scannedDirectories || 0 }}</strong>
            </div>
            <div class="status-stat">
              <span>已处理文件</span>
              <strong>{{ status.processedFiles || 0 }}</strong>
            </div>
          </div>
        </div>
      </section>

      <section class="scan-feed-card">
        <div class="card-heading">
          <span class="status-label">扫描轨迹</span>
          <span class="feed-caption">最新目录优先</span>
        </div>
        <div class="tree-shell">
          <div v-if="rows.length === 0" class="tree-empty">
            扫描轨迹正在生成…
          </div>
          <div
            v-for="row in rows"
            :key="row.key"
            class="tree-row"
            :class="{ active: row.path === status.currentPath }"
            :style="{ '--depth': row.depth, '--row-delay': `${Math.min(row.depth * 40, 180)}ms` }"
          >
            <div class="tree-branch"></div>
            <div class="tree-node">
              <span class="tree-name">{{ row.name }}</span>
              <span class="tree-path">{{ row.path }}</span>
            </div>
            <div class="tree-counts">
              <span class="count-chip leaf-chip">{{ row.mediaCount }}</span>
              <span class="count-chip total-chip">{{ row.totalCount }}</span>
            </div>
          </div>
        </div>
      </section>
    </div>

    <template #footer>
      <el-button
        class="infuse-btn-default"
        :disabled="status.isScanning"
        @click="emit('update:visible', false)"
      >
        {{ status.isScanning ? '扫描中…' : '关闭' }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  title: {
    type: String,
    default: '扫描可视化'
  },
  status: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update:visible'])

const safeProgress = computed(() => Math.max(0, Math.min(100, Math.round(Number(props.status?.progress || 0)))))
const phaseClass = computed(() => props.status?.phase || 'idle')
const progressLabel = computed(() => `${safeProgress.value}%`)
const phaseLabel = computed(() => {
  const phaseMap = {
    idle: '待命',
    scanning: '扫描中',
    processing: '处理中',
    complete: '已完成'
  }
  return phaseMap[props.status?.phase] || '扫描中'
})
const phaseCopy = computed(() => {
  if (props.status?.phase === 'complete') return '媒体库扫描完成，结果已同步。'
  if (props.status?.phase === 'processing') return '正在整理扫描结果并更新媒体状态。'
  if (props.status?.isScanning) return '正在逐层遍历目录并统计媒体文件。'
  return '正在准备扫描任务'
})
const currentDirectoryName = computed(() => {
  const path = props.status?.currentPath || ''
  if (!path) return '等待目录路径…'
  const parts = path.split('/').filter(Boolean)
  return parts.at(-1) || path
})
const progressHint = computed(() => {
  if (props.status?.phase === 'complete') {
    return `本次共发现 ${props.status?.totalDiscoveredMedia || 0} 个媒体条目`
  }
  return `已扫描 ${props.status?.scannedDirectories || 0} 个目录，发现 ${props.status?.totalDiscoveredMedia || 0} 个媒体`
})

const rows = computed(() => flattenTree(props.status?.tree || []))

function flattenTree(nodes, depth = 0) {
  return nodes.flatMap(node => {
    const current = {
      key: node.key,
      name: node.name,
      path: node.path,
      mediaCount: node.mediaCount || 0,
      totalCount: node.totalCount || 0,
      depth
    }
    const children = flattenTree(node.children || [], depth + 1)
    return [current, ...children]
  })
}
</script>

<style scoped>
.scan-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.scan-kicker {
  margin-bottom: 8px;
  font-size: 11px;
  letter-spacing: 0.22em;
  color: var(--infuse-text-muted);
  text-transform: uppercase;
}

.scan-header h3 {
  font-size: 24px;
  margin-bottom: 6px;
}

.scan-header p {
  color: var(--infuse-text-secondary);
}

.scan-progress-chip {
  min-width: 96px;
  padding: 10px 12px;
  border-radius: 20px;
  text-align: right;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.scan-progress-chip span,
.scan-progress-chip strong {
  display: block;
}

.scan-progress-chip span {
  font-size: 11px;
  letter-spacing: 0.14em;
  color: var(--infuse-text-muted);
  text-transform: uppercase;
}

.scan-progress-chip strong {
  margin-top: 6px;
  font-size: 24px;
}

.scan-progress-chip.scanning,
.scan-progress-chip.processing {
  color: #77f7ff;
  background: linear-gradient(135deg, rgba(34, 246, 255, 0.14), rgba(0, 168, 255, 0.1));
}

.scan-progress-chip.complete {
  color: #34c759;
  background: linear-gradient(135deg, rgba(52, 199, 89, 0.18), rgba(32, 176, 93, 0.08));
}

.scan-visualization {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.scan-hero {
  display: grid;
  grid-template-columns: minmax(0, 1.3fr) minmax(280px, 0.9fr);
  gap: 18px;
  padding: 22px;
  border-radius: 22px;
  background: radial-gradient(circle at top left, rgba(34, 246, 255, 0.16), transparent 38%), var(--infuse-gradient-card);
  border: 1px solid var(--infuse-border);
  box-shadow: var(--infuse-shadow-md);
}

.scan-hero.complete {
  background: radial-gradient(circle at top left, rgba(52, 199, 89, 0.16), transparent 38%), var(--infuse-gradient-card);
}

.scan-hero-copy strong {
  display: block;
  margin-top: 10px;
  font-size: 18px;
  word-break: break-all;
}

.scan-hero-copy p {
  margin-top: 8px;
  color: var(--infuse-text-muted);
}

.scan-hero-meter {
  display: flex;
  flex-direction: column;
  gap: 12px;
  justify-content: center;
}

.meter-ring {
  width: 128px;
  height: 128px;
  margin-left: auto;
  border-radius: 50%;
  padding: 12px;
  background:
    conic-gradient(from 180deg, rgba(34, 246, 255, 0.94) calc(var(--progress, 0) * 1%), rgba(255, 255, 255, 0.06) 0);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.08);
}

.scan-hero.complete .meter-ring {
  background:
    conic-gradient(from 180deg, rgba(52, 199, 89, 0.94) calc(var(--progress, 0) * 1%), rgba(255, 255, 255, 0.06) 0);
}

.meter-ring-inner {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: rgba(8, 12, 28, 0.94);
}

.meter-ring-inner span {
  font-size: 11px;
  letter-spacing: 0.14em;
  color: var(--infuse-text-muted);
  text-transform: uppercase;
}

.meter-ring-inner strong {
  margin-top: 6px;
  font-size: 28px;
}

.meter-track {
  position: relative;
  height: 10px;
  overflow: hidden;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.06);
}

.meter-track::after {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.18), transparent);
  animation: progress-shimmer 1.6s linear infinite;
}

.meter-fill {
  position: relative;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #22f6ff, #00a8ff 55%, #77f7ff);
  box-shadow: 0 0 20px rgba(34, 246, 255, 0.28);
  transition: width 0.45s ease;
}

.scan-hero.complete .meter-fill {
  background: linear-gradient(90deg, #34c759, #77d970);
  box-shadow: 0 0 20px rgba(52, 199, 89, 0.24);
}

.meter-copy {
  color: var(--infuse-text-secondary);
  font-size: 13px;
}

.scan-status-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.scan-status-card,
.scan-feed-card {
  padding: 18px;
  border-radius: 18px;
  border: 1px solid var(--infuse-border);
  background: rgba(255, 255, 255, 0.03);
}

.card-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.status-label {
  display: block;
  font-size: 11px;
  letter-spacing: 0.16em;
  color: var(--infuse-text-muted);
  text-transform: uppercase;
}

.phase-pill,
.metric-total,
.feed-caption {
  font-size: 12px;
  color: var(--infuse-text-secondary);
}

.phase-pill {
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.06);
}

.phase-pill.scanning,
.phase-pill.processing {
  color: #77f7ff;
  background: rgba(34, 246, 255, 0.12);
}

.phase-pill.complete {
  color: #34c759;
  background: rgba(52, 199, 89, 0.12);
}

.path-panel {
  padding: 14px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.04);
}

.path-name {
  font-size: 17px;
  font-weight: 700;
}

.path-full {
  margin-top: 6px;
  font-size: 13px;
  color: var(--infuse-text-muted);
  word-break: break-all;
}

.pulse-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 14px;
  color: var(--infuse-text-secondary);
  font-size: 13px;
}

.pulse-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #22f6ff;
  box-shadow: 0 0 0 0 rgba(34, 246, 255, 0.35);
  animation: pulse-dot 1.8s ease infinite;
}

.status-stats {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.status-stat {
  padding: 14px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.04);
}

.status-stat.emphasis {
  background: linear-gradient(145deg, rgba(34, 246, 255, 0.14), rgba(0, 168, 255, 0.08));
}

.status-stat span {
  display: block;
  color: var(--infuse-text-muted);
  font-size: 12px;
}

.status-stat strong {
  display: block;
  margin-top: 8px;
  font-size: 26px;
}

.tree-shell {
  max-height: 44vh;
  overflow: auto;
  padding-right: 4px;
}

.tree-row {
  display: grid;
  grid-template-columns: 20px minmax(0, 1fr) auto;
  align-items: center;
  gap: 12px;
  margin-left: calc(var(--depth) * 18px);
  padding: 12px 0;
  animation: reveal-row 0.35s ease both;
  animation-delay: var(--row-delay);
}

.tree-row + .tree-row {
  border-top: 1px solid rgba(255, 255, 255, 0.04);
}

.tree-row.active {
  background: linear-gradient(90deg, rgba(34, 246, 255, 0.08), transparent 72%);
}

.tree-branch {
  width: 12px;
  height: 12px;
  border-left: 1px solid rgba(119, 247, 255, 0.35);
  border-bottom: 1px solid rgba(119, 247, 255, 0.35);
  border-bottom-left-radius: 8px;
}

.tree-node {
  min-width: 0;
}

.tree-name {
  display: block;
  font-weight: 600;
}

.tree-path {
  display: block;
  color: var(--infuse-text-muted);
  font-size: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tree-counts {
  display: flex;
  gap: 8px;
}

.count-chip {
  min-width: 48px;
  padding: 6px 10px;
  border-radius: 999px;
  text-align: center;
  font-weight: 700;
}

.leaf-chip {
  background: rgba(34, 246, 255, 0.14);
  color: #77f7ff;
}

.total-chip {
  background: rgba(255, 216, 77, 0.16);
  color: #ffd84d;
}

.tree-empty {
  padding: 24px 0;
  color: var(--infuse-text-muted);
  text-align: center;
}

@keyframes reveal-row {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes progress-shimmer {
  from {
    transform: translateX(-100%);
  }
  to {
    transform: translateX(100%);
  }
}

@keyframes pulse-dot {
  0% {
    box-shadow: 0 0 0 0 rgba(34, 246, 255, 0.35);
  }
  70% {
    box-shadow: 0 0 0 10px rgba(34, 246, 255, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(34, 246, 255, 0);
  }
}

@media (max-width: 768px) {
  .scan-hero,
  .scan-status-grid {
    grid-template-columns: 1fr;
  }

  .meter-ring {
    margin-left: 0;
  }

  .status-stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .tree-row {
    grid-template-columns: 16px minmax(0, 1fr);
  }

  .tree-counts {
    grid-column: 2;
  }
}
</style>
