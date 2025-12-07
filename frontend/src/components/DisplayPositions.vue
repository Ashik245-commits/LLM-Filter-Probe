<template>
  <n-tooltip trigger="hover" :show-arrow="true">
    <template #trigger>
      <span class="positions-display">{{ displayText }}</span>
    </template>
    <div class="positions-tooltip">
      <div
        v-for="(loc, index) in locations"
        :key="`${loc.start}-${loc.end}-${index}`"
        class="position-item"
      >
        {{ loc.start }}-{{ loc.end }}
      </div>
    </div>
  </n-tooltip>
</template>

<script setup>
/**
 * @file DisplayPositions.vue
 * @description 一个用于显示敏感词位置列表的组件。
 *
 * 当位置数量较多时，它会截断列表并显示一个摘要（例如 "1-3, 5-7 ... (+3 more)"）。
 * 完整的列表会在鼠标悬停时通过工具提示显示。
 */
import { computed } from 'vue';
import { NTooltip } from 'naive-ui';

const props = defineProps({
  /**
   * 敏感词位置的数组。
   * @type {Array<{start: number, end: number}>}
   * @example [{start: 3, end: 5}, {start: 103, end: 105}]
   */
  locations: {
    type: Array,
    required: true,
    default: () => [],
  },
  /**
   * 在主视图中显示的位置数量的截断阈值。
   * 超过此数量的其余位置将在工具提示中显示。
   * @type {number}
   */
  truncateAt: {
    type: Number,
    default: 5,
  },
});

/**
 * 计算用于显示的截断后的位置字符串。
 * 如果位置数量超过 `truncateAt` 阈值，则显示摘要信息（例如 "1-3, 5-7 ... (+3 more)"）。
 * @returns {string} 格式化后的位置字符串。
 */
const displayText = computed(() => {
  if (!props.locations || props.locations.length === 0) {
    return '无';
  }

  const displayedLocations = props.locations.slice(0, props.truncateAt);
  const positionStrings = displayedLocations.map((loc) => `${loc.start}-${loc.end}`);
  const mainText = positionStrings.join(', ');

  if (props.locations.length > props.truncateAt) {
    const moreCount = props.locations.length - props.truncateAt;
    return `${mainText} ... (+${moreCount} more)`;
  }

  return mainText;
});
</script>

<style scoped>
.positions-display {
  color: #666;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 12px;
  cursor: help;
  padding: 2px 4px;
  border-radius: 3px;
  transition: background-color 0.2s;
}

.positions-display:hover {
  background-color: #f0f0f0;
}

.positions-tooltip {
  max-height: 200px;
  overflow-y: auto;
  padding: 8px;
  background: #fff;
  border-radius: 4px;
}

.position-item {
  padding: 4px 0;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 12px;
  color: #333;
  line-height: 1.5;
}

.position-item:not(:last-child) {
  border-bottom: 1px solid #f0f0f0;
}
</style>
