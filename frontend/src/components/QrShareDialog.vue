<script setup lang="ts">
import { ref, watch } from "vue";
import QRCode from "qrcode";
import type { HistoryRecord } from "../services/history";
import { modeLabel } from "../services/api";

const props = defineProps<{ record: HistoryRecord | null; visible: boolean }>();
const emit = defineEmits<{ (e: "update:visible", v: boolean): void }>();

const qrUrl = ref("");
const shareText = ref("");

watch(
  () => [props.record, props.visible] as const,
  async ([rec, vis]) => {
    if (!vis || !rec) return;
    const reportId = rec.cloudId || rec.id;
    const payload = {
      system: "Tomato AI",
      report_id: reportId,
      path: `/pages/report/report?id=${reportId}`,
      time: rec.timestamp,
      mode: modeLabel(rec.mode),
      summary: rec.summary,
      hint: "请用 Tomato AI 小程序「扫码看报告」打开",
    };
    shareText.value = JSON.stringify(payload, null, 2);
    qrUrl.value = await QRCode.toDataURL(JSON.stringify(payload), {
      width: 220,
      margin: 2,
      color: { dark: "#14532d", light: "#ffffff" },
    });
  },
  { immediate: true },
);

function close() {
  emit("update:visible", false);
}
</script>

<template>
  <el-dialog :model-value="visible" title="扫码分享检测报告" width="420px" @update:model-value="close">
    <div v-if="record" class="qr-dialog">
      <img v-if="qrUrl" :src="qrUrl" alt="报告 QR 码" class="qr-img" />
      <p class="qr-hint">用微信开发者工具 / Tomato AI 小程序「扫码看报告」打开详情</p>
      <el-input type="textarea" :rows="6" :model-value="shareText" readonly />
      <p class="qr-note">二维码含 report_id，与小程序云端报告库关联；未同步云端时仍可显示本地摘要</p>
    </div>
  </el-dialog>
</template>

<style scoped>
.qr-dialog {
  text-align: center;
}

.qr-img {
  width: 220px;
  height: 220px;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  margin-bottom: 12px;
}

.qr-hint {
  font-size: 13px;
  color: #374151;
  margin: 0 0 12px;
}

.qr-note {
  font-size: 11px;
  color: #9ca3af;
  margin-top: 8px;
}
</style>
