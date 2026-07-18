<script setup lang="ts">
import { computed } from "vue";
import { useRouter } from "vue-router";
import {
  DataAnalysis,
  Document,
  PictureRounded,
  TrendCharts,
} from "@element-plus/icons-vue";
import { getHistoryStats } from "../services/history";
import { modeLabel } from "../services/api";
import ChinaMapChart from "../components/ChinaMapChart.vue";
import RiskAlertBanner from "../components/RiskAlertBanner.vue";

const router = useRouter();
const stats = computed(() => getHistoryStats());

const statCards = computed(() => [
  { title: "累计检测", value: stats.value.total, unit: "次", color: "#166534" },
  { title: "今日检测", value: stats.value.todayCount, unit: "次", color: "#0d9488" },
  { title: "高频病害", value: stats.value.topDisease, unit: `${stats.value.topDiseaseCount} 次`, color: "#dc2626" },
  { title: "系统状态", value: "运行中", unit: "YOLO 真实推理", color: "#2563eb" },
]);

const maxDayCount = computed(() => Math.max(1, ...stats.value.dayCounts.map((d) => d.count)));

function go(path: string) {
  router.push(path);
}

function formatTime(iso: string) {
  return new Date(iso).toLocaleString("zh-CN");
}
</script>

<template>
  <div class="home-page">
    <RiskAlertBanner />

    <el-row :gutter="16" class="stat-row">
      <el-col v-for="card in statCards" :key="card.title" :xs="12" :sm="6">
        <el-card shadow="never" class="stat-card panel">
          <p class="stat-title">{{ card.title }}</p>
          <p class="stat-value" :style="{ color: card.color }">{{ card.value }}</p>
          <p class="stat-unit">{{ card.unit }}</p>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never" class="panel map-section">
      <template #header>
        <div class="map-section-header">
          <span class="card-title">全国番茄叶片病害分类型监测分布</span>
          <el-tag type="success" effect="plain" size="small">分病害图层 · 中国地图</el-tag>
        </div>
      </template>
      <ChinaMapChart />
    </el-card>

    <el-row :gutter="16" class="section-row">
      <el-col :span="16">
        <el-card shadow="never" class="panel">
          <template #header>
            <div class="card-title">农业智检驾驶舱</div>
          </template>
          <div class="dashboard-banner">
            <div>
              <h3>番茄病虫害智能诊断与专家辅助决策系统</h3>
              <p>支持快速定性 · 精准定位二维诊断，第六章域适应看板展示跨作物泛化，并结合专家处方</p>
            </div>
            <el-button type="success" size="large" @click="go('/diagnose')">
              立即检测
            </el-button>
          </div>

          <el-row :gutter="12" class="quick-actions">
            <el-col :span="8">
              <div class="action-item" @click="go('/diagnose')">
                <el-icon :size="28"><PictureRounded /></el-icon>
                <span>智能诊断</span>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="action-item" @click="go('/compare')">
                <el-icon :size="28"><DataAnalysis /></el-icon>
                <span>多图对比</span>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="action-item" @click="go('/expert')">
                <el-icon :size="28"><Document /></el-icon>
                <span>专家问答</span>
              </div>
            </el-col>
          </el-row>
        </el-card>

        <el-card shadow="never" class="panel section-row">
          <template #header>
            <div class="card-title">近 7 日检测趋势</div>
          </template>
          <div class="trend-chart">
            <div v-for="item in stats.dayCounts" :key="item.label" class="trend-bar-wrap">
              <div
                class="trend-bar"
                :style="{ height: `${Math.max(8, (item.count / maxDayCount) * 96)}px` }"
                :title="`${item.count} 次`"
              />
              <span>{{ item.label }}</span>
              <span class="trend-count">{{ item.count }}</span>
            </div>
          </div>
          <p class="trend-note">
            <el-icon><TrendCharts /></el-icon>
            数据来自本机诊断历史记录
          </p>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card shadow="never" class="panel">
          <template #header>
            <div class="card-title">最近检测记录</div>
          </template>
          <div v-if="stats.recent.length">
            <div
              v-for="item in stats.recent"
              :key="item.id"
              class="recent-item"
            >
              <img v-if="item.thumbnail" :src="item.thumbnail" alt="" class="recent-thumb" />
              <div class="recent-info">
                <p class="recent-summary">{{ item.summary }}</p>
                <p class="recent-meta">
                  {{ modeLabel(item.mode) }} · {{ formatTime(item.timestamp) }}
                </p>
              </div>
            </div>
          </div>
          <el-empty v-else description="暂无检测记录，去智能诊断上传图片吧" />
          <el-button text type="primary" @click="go('/history')">查看全部历史 →</el-button>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>
