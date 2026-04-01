<template>
  <el-tooltip
    effect="dark"
    placement="top"
    :show-after="120"
    popper-class="subtitle-quality-popper"
  >
    <template #content>
      <div class="badge-tooltip">
        <div class="tooltip-head">
          <span class="tooltip-tone" :class="toneClass">{{ scoreTierLabel }}</span>
          <strong>{{ scorePercent }}% 匹配</strong>
        </div>
        <div class="tooltip-row">
          <span>来源</span>
          <strong>{{ result.source || '未知' }}</strong>
        </div>
        <div class="tooltip-row">
          <span>票数</span>
          <strong>{{ formatMetric(result.votes) }}</strong>
        </div>
        <div class="tooltip-row">
          <span>下载量</span>
          <strong>{{ formatMetric(downloadCount) }}</strong>
        </div>
        <div class="tooltip-row" v-if="result.rating !== null && result.rating !== undefined">
          <span>站点评分</span>
          <strong>{{ Number(result.rating).toFixed(1) }}</strong>
        </div>
      </div>
    </template>

    <div class="quality-badges" :class="{ compact }">
      <div class="quality-score-card" :class="toneClass">
        <div class="score-head">
          <small>匹配度</small>
          <span>{{ scoreTierLabel }}</span>
        </div>
        <div class="score-main">
          <strong>{{ scorePercent }}</strong>
          <span>%</span>
        </div>
        <div class="score-track">
          <div class="score-fill" :style="{ width: `${scorePercent}%` }"></div>
        </div>
      </div>

      <div class="quality-metrics">
        <span class="metric-pill">
          <small>票数</small>
          <strong>{{ compactMetric(result.votes) }}</strong>
        </span>
        <span class="metric-pill">
          <small>下载</small>
          <strong>{{ compactMetric(downloadCount) }}</strong>
        </span>
      </div>
    </div>
  </el-tooltip>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  result: {
    type: Object,
    required: true
  },
  compact: {
    type: Boolean,
    default: false
  }
})

const normalizedScore = computed(() => Number(props.result?.score || 0))
const scorePercent = computed(() => Math.max(0, Math.min(100, Math.round(normalizedScore.value * 100))))
const downloadCount = computed(() => props.result?.downloadCount ?? props.result?.download_count ?? 0)

const toneClass = computed(() => {
  if (normalizedScore.value >= 0.8) return 'tone-high'
  if (normalizedScore.value >= 0.6) return 'tone-mid'
  return 'tone-low'
})

const scoreTierLabel = computed(() => {
  if (normalizedScore.value >= 0.8) return '高'
  if (normalizedScore.value >= 0.6) return '中'
  return '低'
})

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
  align-items: stretch;
  gap: 10px;
  margin-top: 12px;
}

.quality-badges.compact {
  gap: 8px;
  margin-top: 10px;
}

.quality-score-card {
  min-width: 138px;
  padding: 10px 12px;
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.04);
}

.quality-badges.compact .quality-score-card {
  min-width: 122px;
  padding: 8px 10px;
}

.score-head,
.quality-metrics {
  display: flex;
}

.score-head {
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.score-head small,
.metric-pill small {
  font-size: 10px;
  letter-spacing: 0.12em;
  color: rgba(244, 247, 255, 0.56);
  text-transform: uppercase;
}

.score-head span {
  font-size: 11px;
  font-weight: 700;
}

.score-main {
  display: flex;
  align-items: baseline;
  gap: 2px;
  margin-top: 6px;
}

.score-main strong {
  font-size: 24px;
  line-height: 1;
}

.quality-badges.compact .score-main strong {
  font-size: 20px;
}

.score-main span {
  font-size: 12px;
  color: var(--infuse-text-secondary);
}

.score-track {
  height: 6px;
  margin-top: 10px;
  overflow: hidden;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
}

.score-fill {
  height: 100%;
  border-radius: inherit;
}

.quality-metrics {
  flex-wrap: wrap;
  gap: 8px;
  align-items: stretch;
}

.metric-pill {
  display: inline-flex;
  flex-direction: column;
  justify-content: center;
  min-width: 72px;
  padding: 8px 10px;
  border-radius: 14px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.04);
}

.quality-badges.compact .metric-pill {
  min-width: 64px;
  padding: 7px 9px;
}

.metric-pill strong {
  margin-top: 4px;
  font-size: 15px;
  line-height: 1.1;
  color: var(--infuse-text-primary);
}

.quality-score-card.tone-high {
  background: linear-gradient(135deg, rgba(52, 199, 89, 0.22), rgba(46, 160, 67, 0.12));
  border-color: rgba(52, 199, 89, 0.34);
  color: #d8ffe4;
}

.quality-score-card.tone-high .score-fill,
.tooltip-tone.tone-high {
  background: linear-gradient(90deg, #34c759, #7cd992);
}

.quality-score-card.tone-mid {
  background: linear-gradient(135deg, rgba(255, 204, 0, 0.22), rgba(255, 149, 0, 0.12));
  border-color: rgba(255, 204, 0, 0.34);
  color: #fff2c0;
}

.quality-score-card.tone-mid .score-fill,
.tooltip-tone.tone-mid {
  background: linear-gradient(90deg, #ffcc00, #ff9500);
}

.quality-score-card.tone-low {
  background: linear-gradient(135deg, rgba(255, 69, 58, 0.24), rgba(255, 59, 48, 0.14));
  border-color: rgba(255, 69, 58, 0.34);
  color: #ffd4cf;
}

.quality-score-card.tone-low .score-fill,
.tooltip-tone.tone-low {
  background: linear-gradient(90deg, #ff453a, #ff8a7a);
}

.badge-tooltip {
  min-width: 190px;
}

.tooltip-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
}

.tooltip-tone {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 40px;
  height: 22px;
  border-radius: 999px;
  color: #06111b;
  font-size: 11px;
  font-weight: 800;
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
  .quality-badges,
  .quality-badges.compact {
    flex-direction: column;
    align-items: stretch;
  }

  .quality-score-card,
  .quality-badges.compact .quality-score-card {
    min-width: 0;
  }

  .quality-metrics {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
