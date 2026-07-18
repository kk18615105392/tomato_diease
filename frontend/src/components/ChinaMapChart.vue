<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import * as echarts from "echarts/core";
import { MapChart, EffectScatterChart } from "echarts/charts";
import {
  GeoComponent,
  TooltipComponent,
  VisualMapComponent,
} from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";
import {
  DISEASE_MAP_PROFILES,
  getAffectedProvinceCount,
  getDiseaseProfile,
  getMaxValue,
  getTopProvinces,
  getTotalCases,
  type DiseaseMapProfile,
} from "../data/diseaseMapData";

echarts.use([
  MapChart,
  EffectScatterChart,
  GeoComponent,
  TooltipComponent,
  VisualMapComponent,
  CanvasRenderer,
]);

const CHINA_GEO_URL = "/maps/china.json";

const selectedDiseaseId = ref(DISEASE_MAP_PROFILES[0].id);
const chartRef = ref<HTMLDivElement | null>(null);
const loading = ref(true);
const loadError = ref("");
const mapReady = ref(false);

let chart: echarts.ECharts | null = null;

const currentProfile = computed(() => getDiseaseProfile(selectedDiseaseId.value));
const topProvinces = computed(() => getTopProvinces(currentProfile.value));
const maxValue = computed(() => getMaxValue(currentProfile.value));
const totalCases = computed(() => getTotalCases(currentProfile.value));
const affectedCount = computed(() => getAffectedProvinceCount(currentProfile.value));

function shortProvince(name: string) {
  return name.replace(/省|市|自治区|特别行政区|壮族|维吾尔|回族/g, "");
}

function buildOption(profile: DiseaseMapProfile): echarts.EChartsCoreOption {
  const max = getMaxValue(profile);
  return {
    backgroundColor: "transparent",
    tooltip: {
      trigger: "item",
      backgroundColor: "rgba(15, 81, 50, 0.92)",
      borderColor: profile.colorScale[profile.colorScale.length - 2] ?? "#86efac",
      textStyle: { color: "#fff", fontSize: 13 },
      formatter(params: unknown) {
        const p = params as { seriesType?: string; name?: string; value?: number | number[]; seriesName?: string };
        if (p.seriesType === "effectScatter") {
          const v = p.value as number[];
          return `${profile.name} · ${p.name}<br/>暴发指数：<b>${v[2]}</b>`;
        }
        const val = typeof p.value === "number" ? p.value : 0;
        if (val === 0) {
          return `${p.name}<br/>暂无 ${profile.name} 集中报告`;
        }
        return `${p.name}<br/>${profile.name} 检出：<b>${val}</b> 例<br/>占该病害总量 <b>${((val / getTotalCases(profile)) * 100).toFixed(1)}%</b>`;
      },
    },
    visualMap: {
      min: 0,
      max,
      left: 16,
      bottom: 16,
      text: ["集中高发", "低发/无"],
      calculable: true,
      inRange: { color: profile.colorScale },
      textStyle: { color: "#374151", fontSize: 11 },
    },
    geo: {
      map: "china",
      roam: true,
      scaleLimit: { min: 0.8, max: 3 },
      zoom: 1.15,
      label: { show: false },
      emphasis: {
        label: { show: true, color: "#fff", fontSize: 11 },
        itemStyle: {
          areaColor: profile.emphasisColor,
          borderColor: "#fff",
          borderWidth: 1.5,
        },
      },
      itemStyle: {
        areaColor: "#f3f4f6",
        borderColor: "#ffffff",
        borderWidth: 1,
      },
    },
    series: [
      {
        name: profile.name,
        type: "map",
        map: "china",
        geoIndex: 0,
        data: profile.provinces,
      },
      {
        name: "集中暴发点",
        type: "effectScatter",
        coordinateSystem: "geo",
        data: profile.hotSpots,
        symbolSize(val: number[]) {
          return Math.max(10, (val[2] ?? 0) / (max / 15));
        },
        showEffectOn: "render",
        rippleEffect: { brushType: "stroke", scale: 3.5, period: 4 },
        label: {
          show: true,
          formatter: "{b}",
          position: "right",
          color: profile.emphasisColor,
          fontSize: 11,
          fontWeight: 600,
        },
        itemStyle: {
          color: profile.scatterColor,
          shadowBlur: 10,
          shadowColor: `${profile.scatterColor}88`,
        },
        zlevel: 2,
      },
    ],
  };
}

function updateMap(profile: DiseaseMapProfile) {
  if (!chart) return;
  chart.setOption(buildOption(profile), { notMerge: true });
}

async function initChart() {
  if (!chartRef.value) return;

  loading.value = true;
  loadError.value = "";

  try {
    const res = await fetch(CHINA_GEO_URL);
    if (!res.ok) throw new Error("地图数据加载失败");
    const chinaJson = await res.json();
    echarts.registerMap("china", chinaJson);

    chart = echarts.init(chartRef.value);
    updateMap(currentProfile.value);
    mapReady.value = true;
  } catch (err) {
    loadError.value = err instanceof Error ? err.message : "地图初始化失败";
  } finally {
    loading.value = false;
  }
}

function handleResize() {
  chart?.resize();
}

watch(selectedDiseaseId, (id) => {
  if (mapReady.value) updateMap(getDiseaseProfile(id));
});

onMounted(() => {
  initChart();
  window.addEventListener("resize", handleResize);
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", handleResize);
  chart?.dispose();
  chart = null;
});
</script>

<template>
  <div class="china-map-module">
    <div class="disease-toolbar">
      <div class="toolbar-left">
        <span class="toolbar-label">选择叶片病害类型</span>
        <el-radio-group v-model="selectedDiseaseId" size="small" class="disease-radio">
          <el-radio-button
            v-for="d in DISEASE_MAP_PROFILES"
            :key="d.id"
            :label="d.id"
          >
            {{ d.name }}
          </el-radio-button>
        </el-radio-group>
      </div>
      <div class="toolbar-stats">
        <el-tag effect="plain" type="info">{{ currentProfile.alias }}</el-tag>
        <span>涉及省份 <b>{{ affectedCount }}</b> 个</span>
        <span>累计报告 <b>{{ totalCases.toLocaleString() }}</b> 例</span>
      </div>
    </div>

    <el-alert
      :title="`【${currentProfile.name}】${currentProfile.clusterDesc}`"
      type="warning"
      :closable="false"
      show-icon
      class="cluster-alert"
    />

    <div class="map-layout">
      <div ref="chartRef" class="map-chart" v-loading="loading" />
      <div v-if="loadError" class="map-error">
        <p>{{ loadError }}</p>
        <el-button size="small" type="primary" @click="initChart">重新加载</el-button>
      </div>

      <div class="map-rank">
        <h4>{{ currentProfile.name }} · 省份 TOP {{ topProvinces.length }}</h4>
        <div v-for="(item, idx) in topProvinces" :key="item.name" class="rank-item">
          <span class="rank-no" :class="{ top3: idx < 3 }">{{ idx + 1 }}</span>
          <span class="rank-name">{{ shortProvince(item.name) }}</span>
          <span class="rank-bar-wrap">
            <span
              class="rank-bar"
              :style="{
                width: `${(item.value / maxValue) * 100}%`,
                background: `linear-gradient(90deg, ${currentProfile.colorScale[2]}, ${currentProfile.emphasisColor})`,
              }"
            />
          </span>
          <span class="rank-val">{{ item.value }}</span>
        </div>
        <p class="map-note">各省集中暴发指数（示意分布，可用于答辩演示）</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.china-map-module {
  width: 100%;
}

.disease-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.toolbar-left {
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex: 1;
  min-width: 280px;
}

.toolbar-label {
  font-size: 13px;
  font-weight: 600;
  color: #166534;
}

.disease-radio {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.disease-radio :deep(.el-radio-button__inner) {
  border-radius: 6px !important;
  margin: 2px;
  border: 1px solid #e5e7eb !important;
  box-shadow: none !important;
}

.toolbar-stats {
  display: flex;
  align-items: center;
  gap: 16px;
  font-size: 13px;
  color: #6b7280;
  flex-shrink: 0;
}

.toolbar-stats b {
  color: #166534;
  font-size: 15px;
}

.cluster-alert {
  margin-bottom: 12px;
  border-radius: 10px;
}

.map-layout {
  display: flex;
  gap: 16px;
  min-height: 480px;
  position: relative;
}

.map-chart {
  flex: 1;
  min-height: 480px;
  border-radius: 12px;
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
  border: 1px solid #e2e8f0;
}

.map-error {
  position: absolute;
  left: 0;
  right: 220px;
  top: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.92);
  border-radius: 12px;
  z-index: 2;
}

.map-rank {
  width: 230px;
  flex-shrink: 0;
  padding: 12px;
  border-radius: 12px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
}

.map-rank h4 {
  margin: 0 0 12px;
  font-size: 13px;
  color: #166534;
  line-height: 1.4;
}

.rank-item {
  display: grid;
  grid-template-columns: 22px 44px 1fr 32px;
  align-items: center;
  gap: 5px;
  margin-bottom: 9px;
  font-size: 12px;
}

.rank-no {
  width: 18px;
  height: 18px;
  line-height: 18px;
  text-align: center;
  border-radius: 4px;
  background: #e5e7eb;
  color: #6b7280;
  font-weight: 700;
  font-size: 10px;
}

.rank-no.top3 {
  background: #166534;
  color: #fff;
}

.rank-name {
  color: #374151;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.rank-bar-wrap {
  height: 6px;
  background: #e5e7eb;
  border-radius: 3px;
  overflow: hidden;
}

.rank-bar {
  display: block;
  height: 100%;
  border-radius: 3px;
  transition: width 0.5s ease, background 0.5s ease;
}

.rank-val {
  text-align: right;
  color: #374151;
  font-weight: 600;
  font-size: 11px;
}

.map-note {
  margin: 10px 0 0;
  font-size: 10px;
  color: #9ca3af;
  line-height: 1.4;
}
</style>
