<template>
  <el-tooltip
    effect="dark"
    placement="top"
    :show-after="120"
    popper-class="subtitle-quality-popper"
  >
    <template #content>
      <div class="badge-tooltip">
        <div class="tooltip-row">
          <span>来源</span>
          <strong>{{ result.source || '未知' }}</strong>
        </div>
        <div class="tooltip-row">
          <span>匹配度</span>
          <strong>{{ scoreLabel }}</strong>
        </div>
        <div class="tooltip-row">
          <span>票数</span>
          <strong>{{ formatMetric(result.votes) }}</strong>
        </div>
        <div class="tooltip-row">
          <span>下载量</span>
          <strong>{{ formatMetric(result.downloadCount) }}</strong>
        </div>
        <div class="tooltip-row" v-if="result.rating !== null && result.rating !== undefined">
          <span>站点评分</span>
          <strong>{{ Number(result.rating).toFixed(1) }}</strong>
        </div>
      </div>
    </template>

    <div class="quality-badges">
      <span class="quality-pill score-pill" :class="toneClass">
        <small>SCORE</small>
        <strong>{{ scoreLabel }}</strong>
      </span>
      <span v-if="result.votes" class="quality-pill metric-pill">
        <small>票</small>
        <strong>{{ compactMetric(result.votes) }}</strong>
      </span>
      <span v-if="result.downloadCount" class="quality-pill metric-pill">
        <small>下</small>
        <strong>{{ compactMetric(result.downloadCount) }}</strong>
      </span>
    </div>
  </el-tooltip>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  result: {
    type: Object,
    required: true
  }
})

const toneClass = computed(() => {
  const score = Number(props.result?.score || 0)
  if (score >= 0.8) return 'tone-high'
  if (score >= 0.6) return 'tone-mid'
  return 'tone-low'
})

const scoreLabel = computed(() => `${Math.round(Number(props.result?.score || 0) * 100)}`)

function compactMetric(value) {
  const numeric = Number(value || 0)
  if (numeric >= 10000) return `${(numeric / 1000).toFixed(1)}k`
  if (numeric >= 1000) return `${Math.round(numeric / 100) / 10}k`
  return `${numeric}`
}

function formatMetric(value) {
  const numeric = Number(value || 0)
  return new Intl.NumberFormat('zh-CN').format(numeric)
}
</script>

<style scoped>
.quality-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
}

.quality-pill {
  display: inline-flex;
  align-items: baseline;
  gap: 6px;
  min-height: 28px;
  padding: 5px 9px;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.04);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
}

.quality-pill small {
  font-size: 10px;
  letter-spacing: 0.12em;
  color: rgba(244, 247, 255, 0.56);
}

.quality-pill strong {
  font-size: 13px;
  line-height: 1;
  color: var(--infuse-text-primary);
}

.score-pill.tone-high {
  background: linear-gradient(135deg, rgba(52, 199, 89, 0.22), rgba(46, 160, 67, 0.14));
  border-color: rgba(52, 199, 89, 0.35);
}

.score-pill.tone-mid {
  background: linear-gradient(135deg, rgba(255, 204, 0, 0.22), rgba(255, 149, 0, 0.14));
  border-color: rgba(255, 204, 0, 0.34);
}

.score-pill.tone-low {
  background: linear-gradient(135deg, rgba(255, 69, 58, 0.24), rgba(255, 59, 48, 0.16));
  border-color: rgba(255, 69, 58, 0.34);
}

.metric-pill {
  background: rgba(255, 255, 255, 0.05);
}

.badge-tooltip {
  min-width: 180px;
}

.tooltip-row {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  font-size: 12px;
}

.tooltip-row + .tooltip-row {
  margin-top: 6px;
}

@media (max-width: 768px) {
  .quality-badges {
    gap: 6px;
  }

  .quality-pill {
    padding: 4px 8px;
  }
}
</style>
