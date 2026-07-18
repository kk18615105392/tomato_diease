<script setup lang="ts">
import { ref } from "vue";
import { UploadFilled } from "@element-plus/icons-vue";
import { REFERENCE_LEAVES, type ReferenceLeaf } from "../data/referenceLeaves";

const userPreview = ref("");
const selectedRef = ref<ReferenceLeaf>(REFERENCE_LEAVES[0]);
const similarity = ref<number | null>(null);
const comparing = ref(false);

function onUpload(file: File) {
  userPreview.value = URL.createObjectURL(file);
  similarity.value = null;
  void calcSimilarity();
}

function selectRef(item: ReferenceLeaf) {
  selectedRef.value = item;
  if (userPreview.value) void calcSimilarity();
}

function loadImage(src: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.crossOrigin = "anonymous";
    img.onload = () => resolve(img);
    img.onerror = reject;
    img.src = src;
  });
}

/** RGB 直方图余弦相似度（0–100） */
async function histogramSimilarity(srcA: string, srcB: string): Promise<number> {
  const size = 64;
  const bins = 16;
  const hist = async (src: string) => {
    const img = await loadImage(src);
    const canvas = document.createElement("canvas");
    canvas.width = size;
    canvas.height = size;
    const ctx = canvas.getContext("2d")!;
    ctx.drawImage(img, 0, 0, size, size);
    const data = ctx.getImageData(0, 0, size, size).data;
    const h = new Float32Array(bins * 3);
    const step = 256 / bins;
    for (let i = 0; i < data.length; i += 4) {
      h[Math.min(bins - 1, Math.floor(data[i] / step))] += 1;
      h[bins + Math.min(bins - 1, Math.floor(data[i + 1] / step))] += 1;
      h[bins * 2 + Math.min(bins - 1, Math.floor(data[i + 2] / step))] += 1;
    }
    const norm = Math.sqrt(h.reduce((s, v) => s + v * v, 0)) || 1;
    return h.map((v) => v / norm);
  };

  const [a, b] = await Promise.all([hist(srcA), hist(srcB)]);
  let dot = 0;
  for (let i = 0; i < a.length; i++) dot += a[i] * b[i];
  return Math.round(Math.max(0, Math.min(100, dot * 100)));
}

async function calcSimilarity() {
  if (!userPreview.value) return;
  comparing.value = true;
  try {
    similarity.value = await histogramSimilarity(userPreview.value, selectedRef.value.imageUrl);
  } catch {
    similarity.value = null;
  } finally {
    comparing.value = false;
  }
}
</script>

<template>
  <div class="ref-page">
    <el-card shadow="never" class="panel">
      <template #header><span class="card-title">健康叶片对照库</span></template>
      <p class="page-desc">上传待检叶片，与标准健康叶 / 典型病斑参考图并排对比，辅助人工复核</p>

      <el-row :gutter="20">
        <el-col :span="12">
          <h4 class="compare-title">您的上传图</h4>
          <el-upload drag :auto-upload="false" :show-file-list="false" accept="image/*"
            :on-change="(f) => f.raw && onUpload(f.raw)">
            <img v-if="userPreview" :src="userPreview" class="ref-preview" alt="" />
            <template v-else>
              <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
              <div class="el-upload__text">上传待对比叶片</div>
            </template>
          </el-upload>
        </el-col>
        <el-col :span="12">
          <h4 class="compare-title">标准参考：{{ selectedRef.name }}</h4>
          <img :src="selectedRef.imageUrl" class="ref-preview" alt="" />
          <p class="ref-desc">{{ selectedRef.description }}</p>
        </el-col>
      </el-row>

      <div v-if="comparing" class="similarity-block muted">正在计算颜色直方图相似度…</div>
      <div v-else-if="similarity !== null" class="similarity-block">
        <p>视觉特征相似度（RGB 直方图）</p>
        <el-progress
          :percentage="similarity"
          :color="similarity > 70 ? '#dc2626' : similarity > 50 ? '#f59e0b' : '#16a34a'"
          :stroke-width="16"
          striped
        />
        <p class="sim-hint">
          {{ similarity > 70 ? "与参考图颜色分布较接近，建议结合 AI 诊断复核" : similarity > 50 ? "部分特征相似，建议专家复核" : "与参考图差异较大，可能为其他类型" }}
        </p>
      </div>
    </el-card>

    <el-card shadow="never" class="panel section-row">
      <template #header><span class="card-title">参考图库</span></template>
      <el-row :gutter="12">
        <el-col v-for="item in REFERENCE_LEAVES" :key="item.id" :xs="12" :sm="8" :md="4">
          <div class="ref-thumb" :class="{ active: selectedRef.id === item.id }" @click="selectRef(item)">
            <img :src="item.imageUrl" alt="" />
            <span>{{ item.name }}</span>
            <el-tag v-if="item.type === 'healthy'" size="small" type="success">健康</el-tag>
            <el-tag v-else size="small" type="danger">病斑</el-tag>
          </div>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>
