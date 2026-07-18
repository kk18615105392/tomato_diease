<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from "vue";
import * as echarts from "echarts/core";
import { LineChart, RadarChart, BarChart } from "echarts/charts";
import {
  GridComponent,
  LegendComponent,
  MarkPointComponent,
  TooltipComponent,
  RadarComponent,
} from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";
import { fetchHeterogeneousStats, type HeterogeneousStats } from "../services/heterogeneousStats";

echarts.use([
  LineChart,
  RadarChart,
  BarChart,
  GridComponent,
  LegendComponent,
  MarkPointComponent,
  TooltipComponent,
  RadarComponent,
  CanvasRenderer,
]);

const loading = ref(true);
const stats = ref<HeterogeneousStats | null>(null);
const lineRef = ref<HTMLDivElement | null>(null);
const radarRef = ref<HTMLDivElement | null>(null);
const ablationRef = ref<HTMLDivElement | null>(null);
let lineChart: echarts.ECharts | null = null;
let radarChart: echarts.ECharts | null = null;
let ablationChart: echarts.ECharts | null = null;

function pct(v: number | null | undefined) {
  if (v == null) return "—";
  return `${v.toFixed(1)}%`;
}

async function load() {
  loading.value = true;
  try {
    stats.value = await fetchHeterogeneousStats();
    renderCharts();
  } finally {
    loading.value = false;
  }
}

function renderCharts() {
  if (!stats.value || !lineRef.value || !radarRef.value || !ablationRef.value) return;

  const ec = stats.value.epoch_comparison;
  const epochs = ec.baseline.data.map((d) => `Epoch ${d.epoch}`);

  lineChart?.dispose();
  lineChart = echarts.init(lineRef.value);
  lineChart.setOption({
    title: {
      text: "PlantDoc 田间测试 · Source-Only vs Full Model",
      left: "center",
      textStyle: { fontSize: 15, color: "#14532d", fontWeight: 600 },
    },
    tooltip: { trigger: "axis" },
    legend: { data: [ec.baseline.name, ec.enhanced.name], bottom: 0 },
    grid: { left: 55, right: 30, top: 50, bottom: 50 },
    xAxis: {
      type: "category",
      data: epochs,
      axisLabel: { interval: 4, fontSize: 10, rotate: 30 },
      name: ec.x_label,
      nameLocation: "middle",
      nameGap: 35,
    },
    yAxis: {
      type: "value",
      min: 40,
      max: 75,
      name: ec.y_label,
      axisLabel: { formatter: "{value}%" },
    },
    series: [
      {
        name: ec.baseline.name,
        type: "line",
        smooth: true,
        symbolSize: 3,
        lineStyle: { color: ec.baseline.color, width: 2 },
        itemStyle: { color: ec.baseline.color },
        data: ec.baseline.data.map((d) => d.accuracy),
      },
      {
        name: ec.enhanced.name,
        type: "line",
        smooth: true,
        symbolSize: 3,
        lineStyle: { color: ec.enhanced.color, width: 3 },
        itemStyle: { color: ec.enhanced.color },
        data: ec.enhanced.data.map((d) => d.accuracy),
        markPoint: {
          data: [{
            coord: [epochs.length - 1, ec.enhanced.final_accuracy],
            value: `+${ec.improvement_abs}%`,
            itemStyle: { color: "#16a34a" },
          }],
        },
      },
    ],
  });

  const radar = stats.value.robustness_radar;
  radarChart?.dispose();
  radarChart = echarts.init(radarRef.value);
  radarChart.setOption({
    title: {
      text: "复杂干扰场景鲁棒性",
      left: "center",
      textStyle: { fontSize: 15, color: "#14532d", fontWeight: 600 },
    },
    tooltip: {},
    legend: { data: [radar.baseline.name, radar.enhanced.name], bottom: 0 },
    radar: {
      indicator: radar.indicators,
      radius: "60%",
      axisName: { color: "#374151", fontSize: 12 },
    },
    series: [{
      type: "radar",
      data: [
        {
          value: radar.baseline.values,
          name: radar.baseline.name,
          areaStyle: { color: "rgba(156,163,175,0.25)" },
          lineStyle: { color: "#9ca3af" },
        },
        {
          value: radar.enhanced.values,
          name: radar.enhanced.name,
          areaStyle: { color: "rgba(34,197,94,0.28)" },
          lineStyle: { color: "#22c55e" },
        },
      ],
    }],
  });

  const rows = stats.value.exp4_ablation || [];
  ablationChart?.dispose();
  ablationChart = echarts.init(ablationRef.value);
  ablationChart.setOption({
    title: {
      text: "实验四 · 消融与跨域泛化 Acc (%)",
      left: "center",
      textStyle: { fontSize: 15, color: "#14532d", fontWeight: 600 },
    },
    tooltip: { trigger: "axis" },
    legend: { data: ["番茄测试", "热带水果测试", "跨域测试"], bottom: 0 },
    grid: { left: 50, right: 20, top: 50, bottom: 50 },
    xAxis: { type: "category", data: rows.map((r) => `${r.group} ${r.method}`), axisLabel: { rotate: 28, fontSize: 11 } },
    yAxis: { type: "value", min: 30, max: 100, axisLabel: { formatter: "{value}%" } },
    series: [
      { name: "番茄测试", type: "bar", data: rows.map((r) => r.tomato_test), itemStyle: { color: "#dc2626" } },
      { name: "热带水果测试", type: "bar", data: rows.map((r) => r.fruit_test), itemStyle: { color: "#f59e0b" } },
      { name: "跨域测试", type: "bar", data: rows.map((r) => r.cross_test), itemStyle: { color: "#16a34a" } },
    ],
  });
}

function handleResize() {
  lineChart?.resize();
  radarChart?.resize();
  ablationChart?.resize();
}

onMounted(() => {
  load();
  window.addEventListener("resize", handleResize);
});
onBeforeUnmount(() => {
  window.removeEventListener("resize", handleResize);
  lineChart?.dispose();
  radarChart?.dispose();
  ablationChart?.dispose();
});
</script>

<template>
  <div v-loading="loading" class="enhance-page">
    <el-alert
      v-if="stats"
      :title="stats.summary"
      type="success"
      show-icon
      :closable="false"
      class="summary-alert"
    />

    <el-card v-if="stats?.meta" shadow="never" class="panel meta-card">
      <h2>{{ stats.meta.title }}</h2>
      <p class="hypo">{{ stats.meta.hypothesis }}</p>
      <div class="pipeline">
        <el-tag v-for="(step, i) in stats.meta.pipeline" :key="step" type="success" effect="plain">
          {{ i + 1 }}. {{ step }}
        </el-tag>
      </div>
      <p class="best">
        最优：{{ stats.meta.best_method }} · 跨域 Acc
        <strong>{{ stats.meta.best_cross_acc }}%</strong>
      </p>
    </el-card>

    <el-row v-if="stats" :gutter="16" class="stat-row">
      <el-col :xs="24" :sm="8">
        <el-card shadow="never" class="stat-card panel tomato-card">
          <p class="stat-label">{{ stats.dataset.tomato_label }}</p>
          <p class="stat-num">{{ stats.dataset.tomato_base.toLocaleString() }}</p>
          <p class="stat-unit">张 · 源域</p>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="8">
        <el-card shadow="never" class="stat-card panel tropical-card">
          <p class="stat-label">{{ stats.dataset.tropical_label }}</p>
          <p class="stat-num">{{ stats.dataset.tropical_fruit.toLocaleString() }}</p>
          <p class="stat-unit">张 · 目标域</p>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="8">
        <el-card shadow="never" class="stat-card panel mixed-card">
          <p class="stat-label">{{ stats.dataset.mixed_label }}</p>
          <p class="stat-num">{{ stats.dataset.mixed_total.toLocaleString() }}</p>
          <p class="stat-unit">张</p>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never" class="panel chart-card">
      <div ref="lineRef" class="chart-box line-chart" />
    </el-card>

    <el-row :gutter="16" class="section-row">
      <el-col :span="12">
        <el-card shadow="never" class="panel">
          <div ref="radarRef" class="chart-box radar-chart" />
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="never" class="panel">
          <div ref="ablationRef" class="chart-box radar-chart" />
        </el-card>
      </el-col>
    </el-row>

    <el-card v-if="stats?.exp1_mix_ratio" shadow="never" class="panel section-row">
      <template #header><span class="card-title">实验一 · 多任务混合比例与不确定性加权</span></template>
      <el-table :data="stats.exp1_mix_ratio" size="small" stripe>
        <el-table-column prop="group" label="组别" width="110">
          <template #default="{ row }">
            {{ row.group }}
            <el-tag v-if="row.best" size="small" type="success">最佳</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="mix_ratio" label="混合比例" width="90" />
        <el-table-column label="不确定性加权" width="110">
          <template #default="{ row }">{{ row.uncertainty ? "是" : "否" }}</template>
        </el-table-column>
        <el-table-column label="番茄 Acc" width="90" align="right">
          <template #default="{ row }">{{ pct(row.tomato_acc) }}</template>
        </el-table-column>
        <el-table-column label="番茄 F1" width="90" align="right">
          <template #default="{ row }">{{ pct(row.tomato_f1) }}</template>
        </el-table-column>
        <el-table-column label="热带水果 Acc" width="110" align="right">
          <template #default="{ row }">{{ pct(row.fruit_acc) }}</template>
        </el-table-column>
        <el-table-column label="热带水果 F1" width="110" align="right">
          <template #default="{ row }">{{ pct(row.fruit_f1) }}</template>
        </el-table-column>
        <el-table-column prop="note" label="说明" min-width="120" />
      </el-table>
    </el-card>

    <el-row :gutter="16" class="section-row">
      <el-col :span="12">
        <el-card v-if="stats?.exp2_mmd" shadow="never" class="panel">
          <template #header><span class="card-title">实验二 · MMD 特征对齐</span></template>
          <el-table :data="stats.exp2_mmd" size="small" stripe>
            <el-table-column prop="group" label="组别" width="100">
              <template #default="{ row }">
                {{ row.group }}
                <el-tag v-if="row.best" size="small" type="success">最佳</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="method" label="对齐方法" min-width="120" />
            <el-table-column label="跨域 Acc" width="90" align="right">
              <template #default="{ row }">{{ pct(row.cross_acc) }}</template>
            </el-table-column>
            <el-table-column label="MMD↓" width="80" align="right">
              <template #default="{ row }">{{ row.mmd.toFixed(3) }}</template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card v-if="stats?.exp3_adversarial" shadow="never" class="panel">
          <template #header><span class="card-title">实验三 · GRL 对抗域适应</span></template>
          <el-table :data="stats.exp3_adversarial" size="small" stripe>
            <el-table-column prop="group" label="组别" width="100">
              <template #default="{ row }">
                {{ row.group }}
                <el-tag v-if="row.best" size="small" type="success">最佳</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="method" label="方法" min-width="130" />
            <el-table-column label="域判别 Acc" width="100" align="right">
              <template #default="{ row }">{{ pct(row.domain_disc_acc) }}</template>
            </el-table-column>
            <el-table-column label="跨域 Acc" width="90" align="right">
              <template #default="{ row }">{{ pct(row.cross_acc) }}</template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <p v-if="stats?.note" class="foot-note">{{ stats.note }}</p>
  </div>
</template>

<style scoped>
.enhance-page { min-height: 400px; }
.summary-alert { margin-bottom: 16px; border-radius: 10px; }
.meta-card h2 { margin: 0 0 8px; color: #14532d; font-size: 20px; }
.hypo { margin: 0 0 12px; color: #4b5563; line-height: 1.6; }
.pipeline { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 12px; }
.best { margin: 0; color: #166534; font-size: 14px; }
.stat-row { margin-bottom: 16px; }
.stat-card { text-align: center; padding: 8px 0; border-radius: 14px; }
.stat-label { margin: 0; font-size: 13px; font-weight: 600; color: #6b7280; }
.stat-num { margin: 12px 0 4px; font-size: 36px; font-weight: 800; line-height: 1; }
.stat-unit { margin: 0; font-size: 13px; color: #9ca3af; }
.tomato-card .stat-num { color: #dc2626; }
.tropical-card .stat-num { color: #f59e0b; }
.mixed-card .stat-num { color: #16a34a; }
.chart-card { margin-bottom: 16px; border-radius: 14px; }
.chart-box { width: 100%; }
.line-chart { height: 400px; }
.radar-chart { height: 360px; }
.section-row { margin-top: 16px; }
.foot-note { margin-top: 12px; font-size: 12px; color: #9ca3af; }
</style>
