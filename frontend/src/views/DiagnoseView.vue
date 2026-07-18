<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { ElMessage } from "element-plus";
import { Camera, Download, Share, UploadFilled } from "@element-plus/icons-vue";
import {
  diagnoseImage,
  fetchDetectionModels,
  fetchGradCam,
  uploadImage,
  MODE_OPTIONS,
  type BBox,
  type DetectionModelInfo,
  type DiagnoseMode,
  type DiagnoseResponse,
  type DetectionItem,
} from "../services/api";
import { fileToDataUrl, saveHistoryRecord, type HistoryRecord } from "../services/history";
import { exportReportPdf } from "../services/pdfReport";
import { getSelectedZoneId, getZones, setSelectedZoneId } from "../services/zones";
import QrShareDialog from "../components/QrShareDialog.vue";

const selectedFile = ref<File | null>(null);
const previewUrl = ref<string>("");
const uploadId = ref<string>("");
const diagnoseMode = ref<DiagnoseMode>("classification");
const diagnosing = ref(false);
const result = ref<DiagnoseResponse | null>(null);
const showGradCam = ref(false);
const gradCamUrl = ref("");
const gradCamMethod = ref("");
const gradCamLoading = ref(false);
const lastThumbnail = ref("");
const cameraInputRef = ref<HTMLInputElement | null>(null);
const exporting = ref(false);
const zones = ref(getZones());
const selectedZoneId = ref(getSelectedZoneId());
const qrVisible = ref(false);
const qrRecord = ref<HistoryRecord | null>(null);
const detectionModels = ref<DetectionModelInfo[]>([]);
const selectedDetectionModel = ref("");

onMounted(async () => {
  try {
    const res = await fetchDetectionModels();
    detectionModels.value = res.models;
    selectedDetectionModel.value =
      res.default ?? res.models.find((m) => m.is_default)?.key ?? res.models[0]?.key ?? "";
  } catch {
    /* 后端未启动时静默失败 */
  }
});

const maskOverlayUrl = computed(() => {
  if (result.value?.mode !== "segmentation") return "";
  return `data:image/svg+xml;base64,${result.value.mask_base64}`;
});

const canShowGradCam = computed(
  () => result.value && (result.value.mode === "classification" || result.value.mode === "detection"),
);

const ablationModels = computed(() =>
  detectionModels.value.filter((m) => m.group !== "legacy"),
);
const legacyModels = computed(() =>
  detectionModels.value.filter((m) => m.group === "legacy"),
);

function modelOptionLabel(m: DetectionModelInfo) {
  const map = m.test_map50 ?? m.map50;
  const mapText = map > 0 ? ` · test ${(map * 100).toFixed(1)}%` : "";
  const tag = m.recommend && m.recommend !== "—" ? ` · ${m.recommend}` : "";
  return `${m.label}${mapText}${tag}`;
}

const selectedModelMeta = computed(() =>
  detectionModels.value.find((m) => m.key === selectedDetectionModel.value),
);

const modelTaskHint = computed(() => selectedModelMeta.value?.task_hint ?? "");
const modelUploadTip = computed(() => selectedModelMeta.value?.upload_tip ?? "");

const detectionList = computed<DetectionItem[]>(() =>
  result.value?.mode === "detection" ? result.value.detections : [],
);

function onFileChange(file: File) {
  selectedFile.value = file;
  previewUrl.value = URL.createObjectURL(file);
  result.value = null;
  showGradCam.value = false;
  gradCamUrl.value = "";
}

function openCamera() {
  cameraInputRef.value?.click();
}

function onCameraCapture(e: Event) {
  const input = e.target as HTMLInputElement;
  const file = input.files?.[0];
  if (file) onFileChange(file);
  input.value = "";
}

function bboxStyle(bbox: BBox) {
  return {
    left: `${bbox.x * 100}%`,
    top: `${bbox.y * 100}%`,
    width: `${bbox.width * 100}%`,
    height: `${bbox.height * 100}%`,
  };
}

function severityTagType(level: string) {
  if (level.includes("轻")) return "success";
  if (level.includes("重")) return "danger";
  return "warning";
}

async function submitDiagnosis() {
  if (!selectedFile.value) {
    ElMessage.warning("请先上传叶片图像");
    return;
  }

  diagnosing.value = true;
  try {
    const uploadRes = await uploadImage(selectedFile.value);
    uploadId.value = uploadRes.image_id;
    result.value = await diagnoseImage(
      uploadRes.image_id,
      diagnoseMode.value,
      selectedDetectionModel.value,
    );
    if (result.value.mode === "detection" && result.value.error) {
      ElMessage.error(result.value.note);
    }
    const thumbnail = await fileToDataUrl(selectedFile.value);
    lastThumbnail.value = thumbnail;
    setSelectedZoneId(selectedZoneId.value);
    const saved = saveHistoryRecord(
      diagnoseMode.value,
      uploadRes.image_id,
      result.value,
      thumbnail,
      selectedZoneId.value,
    );
    qrRecord.value = saved;
    ElMessage.success("检测完成，已写入历史报告");
  } catch (error) {
    ElMessage.error("调用后端接口失败，请检查 Flask 服务是否启动");
    console.error(error);
  } finally {
    diagnosing.value = false;
  }
}

async function exportPdf() {
  if (!result.value) return;
  exporting.value = true;
  try {
    const record: HistoryRecord = {
      id: crypto.randomUUID(),
      timestamp: new Date().toISOString(),
      mode: diagnoseMode.value,
      imageId: uploadId.value,
      thumbnail: lastThumbnail.value,
      summary: result.value.mode === "detection"
        ? `检测到 ${result.value.detections.length} 个目标`
        : result.value.mode === "segmentation"
          ? `${result.value.disease_name} · DSI ${result.value.dsi}%`
          : `${result.value.disease_name} · ${Math.round(result.value.confidence * 100)}%`,
      result: result.value,
    };
    await exportReportPdf(record);
    ElMessage.success("PDF 报告已下载");
  } catch {
    ElMessage.error("PDF 导出失败");
  } finally {
    exporting.value = false;
  }
}

async function loadGradCam() {
  if (!uploadId.value) return;
  gradCamLoading.value = true;
  try {
    const res = await fetchGradCam(uploadId.value);
    gradCamUrl.value = `data:image/png;base64,${res.heatmap_base64}`;
    gradCamMethod.value = res.method;
    showGradCam.value = true;
  } catch {
    ElMessage.error("Grad-CAM 生成失败");
  } finally {
    gradCamLoading.value = false;
  }
}

function shareQr() {
  if (qrRecord.value) qrVisible.value = true;
}

watch(showGradCam, (v) => {
  if (v && !gradCamUrl.value && uploadId.value) loadGradCam();
});

function buildCurrentRecord(): HistoryRecord | null {
  if (!result.value) return null;
  return qrRecord.value ?? {
    id: crypto.randomUUID(),
    timestamp: new Date().toISOString(),
    mode: diagnoseMode.value,
    imageId: uploadId.value,
    zoneId: selectedZoneId.value,
    thumbnail: lastThumbnail.value,
    summary: "",
    result: result.value,
  };
}
</script>

<template>
  <el-row :gutter="20">
    <el-col :span="14">
      <el-card class="panel" shadow="never">
        <template #header>
          <div class="card-title">图像上传</div>
        </template>
        <el-upload
          drag
          :auto-upload="false"
          :show-file-list="false"
          :on-change="(uploadFile) => uploadFile.raw && onFileChange(uploadFile.raw)"
          accept="image/*"
        >
          <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
          <div class="el-upload__text">拖拽图片到此处，或 <em>点击上传</em></div>
        </el-upload>

        <div class="zone-select">
          <span class="mode-label">温室分区</span>
          <el-select v-model="selectedZoneId" placeholder="选择分区" style="width: 100%">
            <el-option v-for="z in zones" :key="z.id" :label="`${z.code} · ${z.name}`" :value="z.id" />
          </el-select>
        </div>

        <div v-if="detectionModels.length" class="model-select">
          <span class="mode-label">推理模型（定性 / 定位均基于 YOLO）</span>
          <el-select v-model="selectedDetectionModel" placeholder="选择改进方案" style="width: 100%">
            <el-option-group v-if="ablationModels.length" label="YOLOv8 消融实验">
              <el-option
                v-for="m in ablationModels"
                :key="m.key"
                :label="modelOptionLabel(m)"
                :value="m.key"
              />
            </el-option-group>
            <el-option-group v-if="legacyModels.length" label="YOLOv5 历史模型">
              <el-option
                v-for="m in legacyModels"
                :key="m.key"
                :label="`${m.label} · mAP ${(m.map50 * 100).toFixed(1)}%`"
                :value="m.key"
              />
            </el-option-group>
          </el-select>
          <el-alert
            v-if="modelTaskHint"
            class="task-hint"
            :title="selectedModelMeta?.task_label || '任务说明'"
            type="info"
            :closable="false"
            show-icon
          >
            <p>{{ modelTaskHint }}</p>
            <p v-if="modelUploadTip" class="upload-tip">{{ modelUploadTip }}</p>
            <p v-if="selectedModelMeta?.dataset === 'v2'" class="upload-tip">
              若要<strong>小病斑多框定位</strong>，请改选带「小病斑m9」的模型（如 E1·E6·merged9）。
            </p>
          </el-alert>
        </div>

        <div class="mode-switch">
          <p class="mode-label">诊断模式（定性筛查 · 目标定位）</p>
          <el-tabs v-model="diagnoseMode" type="border-card" class="mode-tabs">
            <el-tab-pane
              v-for="opt in MODE_OPTIONS"
              :key="opt.value"
              :name="opt.value"
            >
              <template #label>
                <span class="tab-label">{{ opt.label }}</span>
                <span class="tab-desc">{{ opt.desc }}</span>
              </template>
            </el-tab-pane>
          </el-tabs>
        </div>

        <div v-if="previewUrl" class="preview-box">
          <div class="overlay-wrap">
            <img :src="previewUrl" alt="叶片预览图" class="base-image" />
            <template v-if="result?.mode === 'detection'">
              <div
                v-for="(det, idx) in detectionList"
                :key="idx"
                class="bbox"
                :style="bboxStyle(det.bbox)"
              >
                <span class="bbox-label">{{ det.label }} {{ Math.round(det.confidence * 100) }}%</span>
              </div>
            </template>
            <img
              v-if="result?.mode === 'segmentation' && maskOverlayUrl"
              :src="maskOverlayUrl"
              alt="病斑掩码"
              class="mask-layer"
            />
            <img
              v-if="showGradCam && gradCamUrl"
              :src="gradCamUrl"
              alt="Grad-CAM 热力图"
              class="gradcam-layer"
            />
          </div>
        </div>

        <div v-if="canShowGradCam && result" class="gradcam-toggle">
          <el-switch v-model="showGradCam" active-text="Grad-CAM 可解释性热力图" />
          <el-button size="small" :loading="gradCamLoading" @click="loadGradCam">重新生成</el-button>
          <span class="gradcam-hint">{{ gradCamMethod || "PyTorch Grad-CAM 真实热力图" }}</span>
        </div>

        <input
          ref="cameraInputRef"
          type="file"
          accept="image/*"
          capture="environment"
          class="hidden-input"
          @change="onCameraCapture"
        />

        <div class="action-row">
          <el-button type="success" :loading="diagnosing" @click="submitDiagnosis">
            开始检测
          </el-button>
          <el-button :icon="Camera" @click="openCamera">拍照采集</el-button>
        </div>
      </el-card>
    </el-col>

    <el-col :span="10">
      <el-card class="panel result-panel" shadow="never" v-loading="diagnosing">
        <template #header>
          <div class="result-header">
            <span class="card-title">诊断结果</span>
            <div class="result-actions">
              <el-button size="small" :icon="Download" :loading="exporting" @click="exportPdf">PDF</el-button>
              <el-button size="small" :icon="Share" @click="shareQr">扫码分享</el-button>
            </div>
          </div>
        </template>

        <!-- 模式一：分类 -->
        <div v-if="result?.mode === 'classification'" class="result-body">
          <el-tag type="danger" size="large" effect="dark">{{ result.disease_name }}</el-tag>
          <p class="result-sub">快速定性筛查 · 图像分类</p>
          <el-progress
            type="circle"
            :percentage="Math.round(result.confidence * 100)"
            :stroke-width="10"
            color="#16a34a"
            class="result-progress"
          >
            <template #default="{ percentage }">
              <span class="progress-inner">{{ percentage }}%</span>
              <span class="progress-caption">置信度</span>
            </template>
          </el-progress>
          <p class="result-text">图片 ID：{{ uploadId }}</p>
          <p class="result-text muted">{{ result.note }}</p>
        </div>

        <!-- 模式二：检测 -->
        <div v-else-if="result?.mode === 'detection'" class="result-body">
          <p class="result-sub">精准目标定位 · 目标检测</p>
          <p v-if="result.model_label" class="model-badge">{{ result.model_label }}</p>
          <p class="detect-count">
            共检测到 <strong>{{ result.detections.length }}</strong> 个目标
            <span v-if="result.infer_ms" class="infer-ms">· {{ result.infer_ms }}ms</span>
          </p>
          <el-scrollbar max-height="320px">
            <div
              v-for="(det, idx) in result.detections"
              :key="idx"
              class="detect-item"
            >
              <div class="detect-item-head">
                <el-tag size="small" type="danger">{{ det.label }}</el-tag>
                <span class="detect-conf">{{ Math.round(det.confidence * 100) }}%</span>
              </div>
              <p class="detect-coord">
                位置 x={{ (det.bbox.x * 100).toFixed(1) }}%,
                y={{ (det.bbox.y * 100).toFixed(1) }}%,
                w={{ (det.bbox.width * 100).toFixed(1) }}%,
                h={{ (det.bbox.height * 100).toFixed(1) }}%
              </p>
            </div>
          </el-scrollbar>
          <p class="result-text muted">{{ result.note }}</p>
        </div>

        <!-- 模式三：分割 -->
        <div v-else-if="result?.mode === 'segmentation'" class="result-body">
          <el-tag type="danger" size="large" effect="dark">{{ result.disease_name }}</el-tag>
          <p class="result-sub">（历史记录）严重度定量 · 分割模式已停用</p>
          <div class="dsi-block">
            <p class="dsi-value">{{ result.dsi }}<span class="dsi-unit">%</span></p>
            <p class="dsi-label">病情指数 (DSI)</p>
          </div>
          <el-tag :type="severityTagType(result.severity_level)" size="large" effect="plain">
            {{ result.severity_level }}
          </el-tag>
          <p class="result-text">图片 ID：{{ uploadId }}</p>
          <p class="result-text muted">{{ result.note }}</p>
        </div>

        <el-empty v-else description="上传图像并选择诊断模式后，点击「开始检测」" />
      </el-card>
    </el-col>
  </el-row>
  <QrShareDialog v-model:visible="qrVisible" :record="buildCurrentRecord()" />
</template>
