<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import * as echarts from "echarts/core";
import { BarChart, RadarChart } from "echarts/charts";
import { GridComponent, LegendComponent, TooltipComponent, RadarComponent } from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";
import { fetchModelMetrics, type ModelMetricsBundle } from "../services/api";

echarts.use([BarChart, RadarChart, GridComponent, LegendComponent, TooltipComponent, RadarComponent, CanvasRenderer]);

const metrics = ref<ModelMetricsBundle | null>(null);
const loading = ref(true);
const detectionFilter = ref<"all" | "ablation" | "legacy">("ablation");
const rankDataset = ref<"all" | "v2" | "merged9">("all");
const barRef = ref<HTMLDivElement | null>(null);
const radarRef = ref<HTMLDivElement | null>(null);
const ablationRef = ref<HTMLDivElement | null>(null);
let barChart: echarts.ECharts | null = null;
let radarChart: echarts.ECharts | null = null;
let ablationChart: echarts.ECharts | null = null;

const modeCards = [
  { key: "classification" as const, label: "快速定性（YOLO 代理）" },
  { key: "detection" as const, label: "目标检测（YOLO）" },
];

const detection = computed(() => metrics.value?.detection ?? null);

function testScore(row: { test_score?: number; test_map50?: number | null; map50?: number }) {
  if (row.test_score != null && !Number.isNaN(row.test_score)) return row.test_score;
  if (row.test_map50 != null && !Number.isNaN(row.test_map50)) return row.test_map50;
  return row.map50 ?? 0;
}

const filteredVariants = computed(() => {
  const list = detection.value?.variants ?? [];
  let filtered = list;
  if (detectionFilter.value === "ablation") {
    filtered = list.filter((m) => m.group === "ablation");
  } else if (detectionFilter.value === "legacy") {
    filtered = list.filter((m) => m.group === "legacy");
  }
  if (rankDataset.value === "v2") {
    filtered = filtered.filter((m) => m.dataset === "v2");
  } else if (rankDataset.value === "merged9") {
    filtered = filtered.filter((m) => m.dataset === "merged9");
  }
  return [...filtered]
    .sort((a, b) => testScore(b) - testScore(a))
    .map((item, idx) => ({ ...item, rank: idx + 1, test_score: testScore(item) }));
});

function pct(v: number | null | undefined, digits = 1) {
  if (v == null || Number.isNaN(v)) return "—";
  return `${(v * 100).toFixed(digits)}%`;
}

function engineLabel(engine: string) {
  if (engine === "ultralytics") return "YOLOv8";
  if (engine === "yolov5") return "YOLOv5";
  return engine || "—";
}

async function load() {
  loading.value = true;
  try {
    metrics.value = await fetchModelMetrics();
    renderCharts();
  } finally {
    loading.value = false;
  }
}

function renderCharts() {
  if (!metrics.value || !barRef.value || !radarRef.value || !ablationRef.value) return;

  const modes = ["classification", "detection"] as const;
  const labels = ["定性", "检测"];

  barChart?.dispose();
  barChart = echarts.init(barRef.value);
  barChart.setOption({
    tooltip: { trigger: "axis" },
    legend: { data: ["Precision", "Recall", "F1"] },
    grid: { left: 50, right: 20, bottom: 30, top: 40 },
    xAxis: { type: "category", data: labels },
    yAxis: { type: "value", max: 1, axisLabel: { formatter: (v: number) => `${(v * 100).toFixed(0)}%` } },
    series: ["precision", "recall", "f1"].map((key, i) => ({
      name: ["Precision", "Recall", "F1"][i],
      type: "bar",
      data: modes.map((m) => metrics.value![m][key as "precision"]),
      itemStyle: { color: ["#16a34a", "#2563eb", "#dc2626"][i] },
    })),
  });

  const perClass = metrics.value.classification.per_class;
  radarChart?.dispose();
  radarChart = echarts.init(radarRef.value);
  radarChart.setOption({
    tooltip: {},
    radar: {
      indicator: perClass.map((c) => ({ name: c.name, max: 1 })),
    },
    series: [{
      type: "radar",
      data: [{
        value: perClass.map((c) => c.f1),
        name: "分类 F1",
        areaStyle: { color: "rgba(22,163,74,0.2)" },
        lineStyle: { color: "#16a34a" },
      }],
    }],
  });

  const ranking = metrics.value.detection.test_ranking;
  ablationChart?.dispose();
  ablationChart = echarts.init(ablationRef.value);
  ablationChart.setOption({
    tooltip: {
      trigger: "axis",
      axisPointer: { type: "shadow" },
      valueFormatter: (v: number) => `${(v * 100).toFixed(2)}%`,
    },
    grid: { left: 140, right: 30, bottom: 20, top: 20 },
    xAxis: {
      type: "value",
      min: 0.88,
      max: 1,
      axisLabel: { formatter: (v: number) => `${(v * 100).toFixed(0)}%` },
    },
    yAxis: {
      type: "category",
      data: [...ranking.labels].reverse().map((label, i) => {
        const rank = ranking.labels.length - i;
        return `${rank}. ${label}`;
      }),
      axisLabel: { fontSize: 11, width: 140, overflow: "truncate" },
    },
    series: [{
      type: "bar",
      data: [...ranking.test_map50].reverse().map((v, i) => ({
        value: v,
        itemStyle: {
          color: ranking.datasets[ranking.datasets.length - 1 - i] === "v2" ? "#16a34a" : "#2563eb",
        },
      })),
      label: {
        show: true,
        position: "right",
        formatter: (p: { value: number }) => `${(p.value * 100).toFixed(2)}%`,
        fontSize: 11,
      },
    }],
  });
}

onMounted(load);
onBeforeUnmount(() => {
  barChart?.dispose();
  radarChart?.dispose();
  ablationChart?.dispose();
});
</script>

<template>
  <div v-loading="loading" class="metrics-page">
    <el-row :gutter="16">
      <el-col v-for="item in modeCards" :key="item.key" :span="12">
        <el-card v-if="metrics" shadow="never" class="panel metric-card">
          <h3>{{ item.label }}</h3>
          <p class="model-name">{{ metrics[item.key].model_name }}</p>
          <p class="model-weights">权重：{{ metrics[item.key].weights }}</p>
          <p v-if="item.key === 'detection'" class="model-dataset">{{ detection?.dataset }}</p>
          <div class="metric-row">
            <div><span>Precision</span><strong>{{ pct(metrics[item.key].precision) }}</strong></div>
            <div><span>Recall</span><strong>{{ pct(metrics[item.key].recall) }}</strong></div>
            <div><span>F1</span><strong>{{ pct(metrics[item.key].f1) }}</strong></div>
          </div>
          <template v-if="item.key === 'detection' && detection">
            <div class="metric-row detection-extra">
              <div><span>mAP@0.5</span><strong>{{ pct(detection.map50) }}</strong></div>
              <div><span>mAP@0.5:0.95</span><strong>{{ pct(detection.map50_95) }}</strong></div>
              <div><span>test mAP@0.5</span><strong>{{ pct(detection.test_map50) }}</strong></div>
            </div>
            <p class="detection-summary">
              已接入 <strong>{{ detection.summary.total }}</strong> 个检测权重
              · 消融 {{ detection.summary.ablation }} · YOLOv5 {{ detection.summary.legacy }}
            </p>
          </template>
          <p class="infer-time">
            {{ item.key === "detection" && detection ? engineLabel(detection.engine) : "" }}
            推理 {{ metrics[item.key].inference_ms }}ms · {{ metrics[item.key].params_m }}M 参数
          </p>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="section-row">
      <el-col :span="14">
        <el-card shadow="never" class="panel">
          <template #header>
            <span class="card-title">检测模型 test mAP@0.5 排名（消融实验）</span>
          </template>
          <div ref="ablationRef" class="chart-box chart-box--tall" />
          <p v-if="detection" class="chart-note">
            绿色=整叶v2 · 蓝色=小病斑m9
            <span v-if="detection.summary.best_v2"> · test 第1（v2）：{{ detection.summary.best_v2 }} {{ pct(detection.summary.best_v2_test) }}</span>
            <span v-if="detection.summary.best_merged9"> · test 第1（m9）：{{ detection.summary.best_merged9 }} {{ pct(detection.summary.best_merged9_test) }}</span>
          </p>
        </el-card>
      </el-col>
      <el-col :span="10">
        <el-card shadow="never" class="panel">
          <template #header><span class="card-title">三模型 Precision / Recall / F1 对比</span></template>
          <div ref="barRef" class="chart-box" />
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="section-row">
      <el-col :span="10">
        <el-card shadow="never" class="panel">
          <template #header><span class="card-title">分类模型各类别 F1 雷达图</span></template>
          <div ref="radarRef" class="chart-box" />
        </el-card>
      </el-col>
      <el-col :span="14">
        <el-card shadow="never" class="panel">
          <template #header>
            <div class="table-header">
              <span class="card-title">检测模型 test 排名榜</span>
              <div class="table-filters">
                <el-radio-group v-model="rankDataset" size="small">
                  <el-radio-button label="all">全部排名</el-radio-button>
                  <el-radio-button label="v2">整叶 v2</el-radio-button>
                  <el-radio-button label="merged9">小病斑 m9</el-radio-button>
                </el-radio-group>
                <el-radio-group v-model="detectionFilter" size="small">
                  <el-radio-button label="ablation">消融 E1–E11</el-radio-button>
                  <el-radio-button label="legacy">YOLOv5 历史</el-radio-button>
                  <el-radio-button label="all">全部模型</el-radio-button>
                </el-radio-group>
              </div>
            </div>
          </template>
          <p class="table-hint">按 test mAP@0.5 从高到低 · 共 {{ filteredVariants.length }} 个模型</p>
          <el-table
            v-if="detection"
            :data="filteredVariants"
            size="small"
            stripe
            max-height="360"
            empty-text="暂无检测模型"
            row-key="key"
          >
            <el-table-column label="排名" width="72" align="center" fixed>
              <template #default="{ row }">
                <span v-if="row.rank === 1" class="rank-badge rank-1">🥇 {{ row.rank }}</span>
                <span v-else-if="row.rank === 2" class="rank-badge rank-2">🥈 {{ row.rank }}</span>
                <span v-else-if="row.rank === 3" class="rank-badge rank-3">🥉 {{ row.rank }}</span>
                <span v-else class="rank-badge">第 {{ row.rank }} 名</span>
              </template>
            </el-table-column>
            <el-table-column label="模型" min-width="200">
              <template #default="{ row }">
                <span>{{ row.label }}</span>
                <el-tag v-if="row.is_default" size="small" type="success" class="default-tag">默认</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="dataset" label="数据集" width="88">
              <template #default="{ row }">
                {{ row.dataset === "v2" ? "整叶v2" : row.dataset === "merged9" ? "小病斑m9" : "v1" }}
              </template>
            </el-table-column>
            <el-table-column label="test mAP@0.5" width="110" align="right">
              <template #default="{ row }">
                <strong class="test-score">{{ pct(testScore(row)) }}</strong>
              </template>
            </el-table-column>
            <el-table-column label="val@0.5" width="88" align="right">
              <template #default="{ row }">{{ pct(row.map50) }}</template>
            </el-table-column>
            <el-table-column label="mAP@0.5:0.95" width="108" align="right">
              <template #default="{ row }">{{ pct(row.map50_95) }}</template>
            </el-table-column>
            <el-table-column label="P / R / F1" width="130" align="right">
              <template #default="{ row }">
                {{ pct(row.precision, 0) }} / {{ pct(row.recall, 0) }} / {{ pct(row.f1, 0) }}
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.metric-card h3 { margin: 0; color: #14532d; }
.model-name { font-size: 13px; color: #6b7280; margin: 4px 0; }
.model-weights { font-size: 11px; color: #9ca3af; margin: 0 0 4px; }
.model-dataset { font-size: 12px; color: #166534; margin: 0 0 12px; }
.metric-row { display: flex; gap: 12px; }
.metric-row div { flex: 1; text-align: center; background: #f9fafb; padding: 10px; border-radius: 8px; }
.metric-row span { display: block; font-size: 11px; color: #9ca3af; }
.metric-row strong { font-size: 18px; color: #166534; }
.detection-extra { margin-top: 10px; }
.detection-extra strong { font-size: 15px; }
.detection-summary { font-size: 12px; color: #6b7280; margin: 10px 0 0; }
.extra-metric { font-size: 13px; color: #dc2626; margin: 8px 0 0; font-weight: 600; }
.infer-time { font-size: 11px; color: #9ca3af; margin-top: 8px; }
.section-row { margin-top: 16px; }
.chart-box { height: 320px; }
.chart-box--tall { height: 360px; }
.chart-note { font-size: 12px; color: #6b7280; margin: 8px 0 0; }
.table-header { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; }
.table-filters { display: flex; flex-wrap: wrap; gap: 8px; justify-content: flex-end; }
.table-hint { font-size: 12px; color: #6b7280; margin: 0 0 10px; }
.default-tag { margin-left: 6px; vertical-align: middle; }
.rank-badge { display: inline-block; font-weight: 700; color: #374151; white-space: nowrap; }
.rank-badge.rank-1 { color: #ca8a04; font-size: 13px; }
.rank-badge.rank-2 { color: #64748b; font-size: 13px; }
.rank-badge.rank-3 { color: #b45309; font-size: 13px; }
.test-score { color: #166534; font-size: 14px; }
</style>
