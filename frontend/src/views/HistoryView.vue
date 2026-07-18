<script setup lang="ts">
import { ref } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { Delete, Download, Share, View } from "@element-plus/icons-vue";
import {
  clearHistory,
  deleteHistoryRecord,
  getHistoryRecords,
  type HistoryRecord,
} from "../services/history";
import { exportReportPdf } from "../services/pdfReport";
import { modeLabel } from "../services/api";
import { getZoneLabel } from "../services/zones";
import QrShareDialog from "../components/QrShareDialog.vue";

const records = ref<HistoryRecord[]>(getHistoryRecords());
const detailVisible = ref(false);
const currentRecord = ref<HistoryRecord | null>(null);
const exporting = ref(false);
const qrVisible = ref(false);
const qrRecord = ref<HistoryRecord | null>(null);

function refresh() {
  records.value = getHistoryRecords();
}

function formatTime(iso: string) {
  return new Date(iso).toLocaleString("zh-CN");
}

function showDetail(record: HistoryRecord) {
  currentRecord.value = record;
  detailVisible.value = true;
}

async function handleDelete(id: string) {
  await ElMessageBox.confirm("确定删除这条检测记录？", "提示", { type: "warning" });
  deleteHistoryRecord(id);
  refresh();
  ElMessage.success("已删除");
}

async function handleClear() {
  await ElMessageBox.confirm("确定清空全部历史记录？", "警告", { type: "warning" });
  clearHistory();
  refresh();
  ElMessage.success("已清空");
}

async function exportPdf(record: HistoryRecord) {
  exporting.value = true;
  try {
    await exportReportPdf(record);
    ElMessage.success("PDF 报告已下载");
  } catch {
    ElMessage.error("PDF 导出失败");
  } finally {
    exporting.value = false;
  }
}

function shareQr(record: HistoryRecord) {
  qrRecord.value = record;
  qrVisible.value = true;
}
</script>

<template>
  <div class="history-page">
    <el-card shadow="never" class="panel">
      <template #header>
        <div class="history-header">
          <span class="card-title">历史检测报告</span>
          <div>
            <el-button size="small" type="danger" plain @click="handleClear">清空全部</el-button>
          </div>
        </div>
      </template>

      <el-table v-if="records.length" :data="records" stripe style="width: 100%">
        <el-table-column label="缩略图" width="90">
          <template #default="{ row }">
            <img v-if="row.thumbnail" :src="row.thumbnail" alt="" class="table-thumb" />
            <span v-else class="no-thumb">—</span>
          </template>
        </el-table-column>
        <el-table-column prop="summary" label="检测结果" min-width="180" />
        <el-table-column label="温室分区" width="140">
          <template #default="{ row }">{{ getZoneLabel(row.zoneId) }}</template>
        </el-table-column>
        <el-table-column label="诊断模式" width="140">
          <template #default="{ row }">{{ modeLabel(row.mode) }}</template>
        </el-table-column>
        <el-table-column label="检测时间" width="180">
          <template #default="{ row }">{{ formatTime(row.timestamp) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button :icon="View" text type="primary" @click="showDetail(row)">详情</el-button>
            <el-button :icon="Share" text type="warning" @click="shareQr(row)" />
            <el-button :icon="Download" text type="success" :loading="exporting" @click="exportPdf(row)" />
            <el-button :icon="Delete" text type="danger" @click="handleDelete(row.id)" />
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-else description="暂无历史记录，完成一次智能诊断后会自动保存" />
    </el-card>

    <el-dialog v-model="detailVisible" title="检测详情" width="520px">
      <template v-if="currentRecord">
        <img
          v-if="currentRecord.thumbnail"
          :src="currentRecord.thumbnail"
          alt=""
          class="detail-img"
        />
        <el-descriptions :column="1" border class="detail-desc">
          <el-descriptions-item label="摘要">{{ currentRecord.summary }}</el-descriptions-item>
          <el-descriptions-item label="模式">{{ modeLabel(currentRecord.mode) }}</el-descriptions-item>
          <el-descriptions-item label="图片 ID">{{ currentRecord.imageId }}</el-descriptions-item>
          <el-descriptions-item label="时间">{{ formatTime(currentRecord.timestamp) }}</el-descriptions-item>
        </el-descriptions>
      </template>
    </el-dialog>
    <QrShareDialog v-model:visible="qrVisible" :record="qrRecord" />
  </div>
</template>
