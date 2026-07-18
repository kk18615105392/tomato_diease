<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from "vue";
import * as echarts from "echarts/core";
import { LineChart } from "echarts/charts";
import { GridComponent, LegendComponent, TooltipComponent, MarkLineComponent } from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";
import type { DsiForecastResponse } from "../services/api";

echarts.use([LineChart, GridComponent, LegendComponent, TooltipComponent, MarkLineComponent, CanvasRenderer]);

const props = defineProps<{ forecast: DsiForecastResponse | null }>();

const chartRef = ref<HTMLDivElement | null>(null);
let chart: echarts.ECharts | null = null;

function render() {
  if (!chartRef.value || !props.forecast) return;

  if (!chart) chart = echarts.init(chartRef.value);

  const hist = props.forecast.history;
  const pred = props.forecast.forecast;
  const labels = [...hist.map((h) => h.label), ...pred.map((f) => f.label)];
  const histData = [...hist.map((h) => h.dsi), ...pred.map(() => null)];
  const predData = [...hist.map(() => null), ...pred.map((f) => f.dsi)];

  chart.setOption({
    tooltip: { trigger: "axis" },
    legend: { data: ["历史 DSI", "预测 DSI"], bottom: 0 },
    grid: { left: 50, right: 20, top: 30, bottom: 50 },
    xAxis: { type: "category", data: labels, axisLabel: { rotate: 30, fontSize: 10 } },
    yAxis: { type: "value", name: "DSI (%)", max: 100 },
    series: [
      {
        name: "历史 DSI",
        type: "line",
        data: histData,
        smooth: true,
        symbol: "circle",
        symbolSize: 8,
        lineStyle: { color: "#16a34a", width: 3 },
        itemStyle: { color: "#16a34a" },
      },
      {
        name: "预测 DSI",
        type: "line",
        data: predData,
        smooth: true,
        symbol: "diamond",
        symbolSize: 8,
        lineStyle: { color: "#dc2626", width: 2, type: "dashed" },
        itemStyle: { color: "#dc2626" },
        markLine: {
          silent: true,
          data: [{ yAxis: 25, label: { formatter: "重度预警线" }, lineStyle: { color: "#f59e0b" } }],
        },
      },
    ],
  });
}

watch(() => props.forecast, () => render(), { deep: true });
onMounted(() => {
  render();
  window.addEventListener("resize", () => chart?.resize());
});
onBeforeUnmount(() => {
  chart?.dispose();
});
</script>

<template>
  <div v-if="forecast" class="dsi-forecast">
    <div class="forecast-meta">
      <el-tag :type="forecast.risk_level === '高' ? 'danger' : forecast.risk_level === '中' ? 'warning' : 'success'">
        风险：{{ forecast.risk_level }}
      </el-tag>
      <span>模型：{{ forecast.model }}</span>
      <span>趋势：{{ forecast.trend }}（{{ forecast.slope_per_day }}%/天）</span>
    </div>
    <p class="forecast-summary">{{ forecast.summary }}</p>
    <div ref="chartRef" class="forecast-chart" />
  </div>
</template>

<style scoped>
.dsi-forecast {
  margin-top: 16px;
}

.forecast-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
  font-size: 13px;
  color: #6b7280;
  margin-bottom: 8px;
}

.forecast-summary {
  font-size: 13px;
  color: #374151;
  margin: 0 0 12px;
}

.forecast-chart {
  height: 320px;
  width: 100%;
}
</style>
