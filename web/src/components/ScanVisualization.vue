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
          <h3>{{ title }}</h3>
          <p>{{ status.message || '正在准备扫描任务' }}</p>
        </div>
        <div class="scan-progress-chip" :class="status.phase">
          {{ Math.round(status.progress || 0) }}%
        </div>
      </div>
    </template>

    <div class="scan-visualization">
      <div class="scan-status-card">
        <div class="status-copy">
          <span class="status-label">当前目录</span>
          <strong>{{ status.currentPath || '等待扫描器回传路径…' }}</strong>
        </div>
        <div class="status-stats">
          <div class="status-stat">
            <span>当前目录媒体</span>
            <strong>{{ status.currentPathMediaCount || 0 }}</strong>
          </div>
          <div class="status-stat">
            <span>已扫描目录</span>
            <strong>{{ status.scannedDirectories || 0 }}</strong>
          </div>
          <div class="status-stat">
            <span>已发现媒体</span>
            <strong>{{ status.totalDiscoveredMedia || 0 }}</strong>
          </div>
        </div>
      </div>

      <div class="tree-shell">
        <div v-if="rows.length === 0" class="tree-empty">
          扫描树正在生成…
        </div>
        <div
          v-for="row in rows"
          :key="row.key"
          class="tree-row"
          :style="{ '--depth': row.depth }"
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

.scan-header h3 {
  font-size: 22px;
  margin-bottom: 6px;
}

.scan-header p {
  color: var(--infuse-text-secondary);
}

.scan-progress-chip {
  min-width: 76px;
  padding: 10px 12px;
  border-radius: 999px;
  text-align: center;
  font-weight: 700;
  background: rgba(255, 255, 255, 0.06);
}

.scan-progress-chip.scanning,
.scan-progress-chip.processing {
  color: #77f7ff;
  background: rgba(34, 246, 255, 0.14);
}

.scan-progress-chip.complete {
  color: #34c759;
  background: rgba(52, 199, 89, 0.16);
}

.scan-visualization {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.scan-status-card {
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(0, 1fr);
  gap: 16px;
  padding: 18px;
  border-radius: 18px;
  background: linear-gradient(145deg, rgba(12, 20, 48, 0.84), rgba(4, 8, 22, 0.92));
  border: 1px solid var(--infuse-border);
}

.status-label {
  display: block;
  margin-bottom: 8px;
  font-size: 12px;
  color: var(--infuse-text-muted);
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.status-copy strong {
  display: block;
  font-size: 14px;
  word-break: break-all;
}

.status-stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.status-stat {
  padding: 12px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.04);
}

.status-stat span {
  display: block;
  color: var(--infuse-text-muted);
  font-size: 12px;
}

.status-stat strong {
  display: block;
  margin-top: 6px;
  font-size: 22px;
}

.tree-shell {
  max-height: 52vh;
  overflow: auto;
  padding: 14px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.tree-row {
  display: grid;
  grid-template-columns: 20px minmax(0, 1fr) auto;
  align-items: center;
  gap: 12px;
  margin-left: calc(var(--depth) * 18px);
  padding: 10px 0;
  animation: reveal-row 0.3s ease both;
}

.tree-row + .tree-row {
  border-top: 1px solid rgba(255, 255, 255, 0.04);
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
  transition: transform 0.25s ease, background-color 0.25s ease;
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

@media (max-width: 768px) {
  .scan-status-card {
    grid-template-columns: 1fr;
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
