<script setup lang="ts">
import { ref } from "vue";
import { ElMessage } from "element-plus";
import { Plus, UploadFilled } from "@element-plus/icons-vue";
import {
  compareImages,
  predictDsi,
  uploadImage,
  type CompareItem,
  type CompareResponse,
  type DiagnoseMode,
  type DsiForecastResponse,
} from "../services/api";
import DsiForecastChart from "../components/DsiForecastChart.vue";

type SlotItem = {
  id: number;
  label: string;
  file: File | null;
  preview: string;
  imageId: string;
};

const DEFAULT_LABELS = ["第 1 天", "第 3 天", "第 5 天", "第 7 天"];
const slots = ref<SlotItem[]>([
  { id: 1, label: DEFAULT_LABELS[0], file: null, preview: "", imageId: "" },
  { id: 2, label: DEFAULT_LABELS[1], file: null, preview: "", imageId: "" },
]);
const compareMode = ref<DiagnoseMode>("detection");
const comparing = ref(false);
const compareResult = ref<CompareResponse | null>(null);
const dsiForecast = ref<DsiForecastResponse | null>(null);
const forecasting = ref(false);

function addSlot() {
  if (slots.value.length >= 4) {
    ElMessage.warning("最多支持 4 张图片对比");
    return;
  }
  const idx = slots.value.length;
  slots.value.push({
    id: Date.now(),
    label: DEFAULT_LABELS[idx] ?? `样本 ${idx + 1}`,
    file: null,
    preview: "",
    imageId: "",
  });
}

function removeSlot(id: number) {
  if (slots.value.length <= 2) {
    ElMessage.warning("至少保留 2 张图片");
    return;
  }
  slots.value = slots.value.filter((s) => s.id !== id);
  compareResult.value = null;
  dsiForecast.value = null;
}

function onSlotFile(slot: SlotItem, file: File) {
  slot.file = file;
  slot.preview = URL.createObjectURL(file);
  slot.imageId = "";
  compareResult.value = null;
  dsiForecast.value = null;
}

function resultSummary(item: CompareItem): string {
  const r = item.result;
  if (r.mode === "classification") {
    return `${r.disease_name} (${Math.round(r.confidence * 100)}%)`;
  }
  if (r.mode === "detection") {
    return `${r.detections.length} 个目标`;
  }
  return `DSI ${r.dsi}% · ${r.severity_level}`;
}

function resultTagType(item: CompareItem): "success" | "warning" | "danger" {
  const r = item.result;
  if (r.mode === "segmentation") {
    if (r.severity_level.includes("轻")) return "success";
    if (r.severity_level.includes("重")) return "danger";
    return "warning";
  }
  return "danger";
}

async function startCompare() {
  const filled = slots.value.filter((s) => s.file);
  if (filled.length < 2) {
    ElMessage.warning("请至少上传 2 张图片");
    return;
  }

  comparing.value = true;
  try {
    for (const slot of filled) {
      if (!slot.imageId && slot.file) {
        const res = await uploadImage(slot.file);
        slot.imageId = res.image_id;
      }
    }

    const imageIds = filled.map((s) => s.imageId);
    const labels = filled.map((s) => s.label);
    compareResult.value = await compareImages(imageIds, compareMode.value, labels);
    compareResult.value.items.forEach((item, idx) => {
      filled[idx].label = item.label;
    });

    if (compareMode.value === "segmentation") {
      forecasting.value = true;
      try {
        const history = compareResult.value.items
          .filter((it) => it.result.mode === "segmentation")
          .map((it) => ({
            label: it.label,
            dsi: (it.result as { dsi: number }).dsi,
          }));
        if (history.length >= 2) {
          dsiForecast.value = await predictDsi(history);
        }
      } finally {
        forecasting.value = false;
      }
    }

    ElMessage.success("多图对比完成");
  } catch (error) {
    ElMessage.error("对比失败，请确认后端已启动");
    console.error(error);
  } finally {
    comparing.value = false;
  }
}
</script>

<template>
  <div class="compare-page">
    <el-card shadow="never" class="panel">
      <template #header>
        <div class="card-title">多图对比分析</div>
      </template>
      <p class="page-desc">
        上传同一植株不同时间点的 2～4 张叶片图像，并排对比病斑扩展趋势（如第 1 天 / 第 3 天 / 第 5 天）
      </p>

      <div class="compare-toolbar">
        <span class="toolbar-label">对比模式：</span>
        <el-radio-group v-model="compareMode" size="small">
          <el-radio-button label="classification">定性</el-radio-button>
          <el-radio-button label="detection">定位</el-radio-button>
        </el-radio-group>
        <el-button
          v-if="slots.length < 4"
          :icon="Plus"
          size="small"
          class="add-slot-btn"
          @click="addSlot"
        >
          添加图片位
        </el-button>
      </div>

      <el-row :gutter="16">
        <el-col
          v-for="slot in slots"
          :key="slot.id"
          :xs="24"
          :sm="12"
          :md="24 / Math.min(slots.length, 4)"
        >
          <el-card shadow="never" class="compare-slot panel">
            <div class="slot-header">
              <el-input v-model="slot.label" size="small" class="slot-label-input" />
              <el-button
                v-if="slots.length > 2"
                text
                type="danger"
                size="small"
                @click="removeSlot(slot.id)"
              >
                移除
              </el-button>
            </div>

            <el-upload
              drag
              :auto-upload="false"
              :show-file-list="false"
              accept="image/*"
              class="slot-upload"
              :on-change="(f) => f.raw && onSlotFile(slot, f.raw)"
            >
              <template v-if="slot.preview">
                <img :src="slot.preview" alt="" class="slot-preview" />
              </template>
              <template v-else>
                <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
                <div class="el-upload__text">上传 {{ slot.label }} 图像</div>
              </template>
            </el-upload>
          </el-card>
        </el-col>
      </el-row>

      <el-button
        type="success"
        size="large"
        :loading="comparing"
        class="compare-btn"
        @click="startCompare"
      >
        开始对比分析
      </el-button>
    </el-card>

    <el-card v-if="compareResult" shadow="never" class="panel result-section">
      <template #header>
        <div class="card-title">对比结果</div>
      </template>
      <el-alert :title="compareResult.trend_summary" type="warning" show-icon :closable="false" />

      <el-row :gutter="16" class="compare-grid">
        <el-col
          v-for="(item, idx) in compareResult.items"
          :key="item.image_id"
          :xs="24"
          :sm="12"
          :md="24 / compareResult.items.length"
        >
          <el-card shadow="never" class="compare-result-card">
            <img
              v-if="slots[idx]?.preview"
              :src="slots[idx].preview"
              alt=""
              class="compare-result-img"
            />
            <p class="compare-result-label">{{ item.label }}</p>
            <el-tag :type="resultTagType(item)" effect="dark">
              {{ resultSummary(item) }}
            </el-tag>
          </el-card>
        </el-col>
      </el-row>

      <el-card v-if="compareMode === 'segmentation' && dsiForecast" shadow="never" class="panel forecast-section" v-loading="forecasting">
        <template #header>
          <div class="card-title">DSI 时序预测 · 未来 7 天（线性回归）</div>
        </template>
        <DsiForecastChart :forecast="dsiForecast" />
      </el-card>
    </el-card>
  </div>
</template>
