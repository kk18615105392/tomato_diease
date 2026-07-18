<script setup lang="ts">
import { nextTick, onMounted, ref, watch } from "vue";
import { ElMessage } from "element-plus";
import { Microphone, Promotion } from "@element-plus/icons-vue";
import { getLatestRecord } from "../services/history";
import {
  streamExpertChat,
  type ChatMessage,
  type ExpertDiagnosisContext,
} from "../services/expert";
import { modeLabel } from "../services/api";
import { useSpeech } from "../composables/useSpeech";

const messages = ref<ChatMessage[]>([]);
const inputText = ref("");
const sending = ref(false);
const chatBoxRef = ref<HTMLElement | null>(null);
const diagnosisContext = ref<ExpertDiagnosisContext>({});

const { listening, supported, startListen, stopListen } = useSpeech((text) => {
  inputText.value = text;
  ElMessage.success("语音识别完成");
});

function scrollToBottom() {
  nextTick(() => {
    if (chatBoxRef.value) {
      chatBoxRef.value.scrollTop = chatBoxRef.value.scrollHeight;
    }
  });
}

function initFromLatestDiagnosis() {
  const latest = getLatestRecord();
  if (!latest) return;

  const r = latest.result;
  let diseaseName = "未知病害";
  let confidence: number | undefined;
  let dsi: number | undefined;
  let severity: string | undefined;

  if (r.mode === "classification") {
    diseaseName = r.disease_name;
    confidence = r.confidence;
  } else if (r.mode === "segmentation") {
    diseaseName = r.disease_name;
    dsi = r.dsi;
    severity = r.severity_level;
  } else if (r.mode === "detection") {
    diseaseName = r.detections?.[0]?.label || "未检出目标";
    confidence = r.detections?.[0]?.confidence;
  }

  diagnosisContext.value = {
    mode: modeLabel(latest.mode),
    disease_name: diseaseName,
    confidence,
    dsi,
    severity_level: severity,
  };

  messages.value.push({
    id: crypto.randomUUID(),
    role: "system",
    content: `📋 已载入最新诊断结果：${latest.summary}`,
    time: new Date().toLocaleTimeString("zh-CN"),
  });
}

async function sendMessage() {
  const text = inputText.value.trim();
  if (!text || sending.value) return;

  messages.value.push({
    id: crypto.randomUUID(),
    role: "user",
    content: text,
    time: new Date().toLocaleTimeString("zh-CN"),
  });
  inputText.value = "";
  scrollToBottom();

  const assistantId = crypto.randomUUID();
  messages.value.push({
    id: assistantId,
    role: "assistant",
    content: "",
    time: new Date().toLocaleTimeString("zh-CN"),
  });

  sending.value = true;
  await streamExpertChat(
    text,
    diagnosisContext.value,
    (chunk) => {
      const msg = messages.value.find((m) => m.id === assistantId);
      if (msg) msg.content += chunk;
      scrollToBottom();
    },
    () => {
      sending.value = false;
    },
    (err) => {
      sending.value = false;
      ElMessage.error(err.message);
    },
  );
}

function requestPrescription() {
  inputText.value = "请根据以上诊断结果，给出详细的防治处方和温湿度调控建议";
  sendMessage();
}

onMounted(() => {
  initFromLatestDiagnosis();
  if (messages.value.length === 0) {
    messages.value.push({
      id: crypto.randomUUID(),
      role: "system",
      content: "👋 你好！我是 AI 植保专家。请先在「智能诊断」完成检测，或直接向我提问。",
      time: new Date().toLocaleTimeString("zh-CN"),
    });
  }
});
</script>

<template>
  <div class="expert-page">
    <el-card shadow="never" class="panel chat-card">
      <template #header>
        <div class="chat-header">
          <span class="card-title">专家问答与植保处方</span>
          <el-button
            v-if="diagnosisContext.disease_name"
            size="small"
            type="success"
            plain
            :disabled="sending"
            @click="requestPrescription"
          >
            一键生成防治处方
          </el-button>
        </div>
      </template>

      <div v-if="diagnosisContext.disease_name" class="diagnosis-card">
        <el-tag type="danger" effect="dark">{{ diagnosisContext.disease_name }}</el-tag>
        <span v-if="diagnosisContext.dsi"> · DSI {{ diagnosisContext.dsi }}%</span>
        <span v-if="diagnosisContext.severity_level"> · {{ diagnosisContext.severity_level }}</span>
        <span v-if="diagnosisContext.confidence">
          · 置信度 {{ Math.round(diagnosisContext.confidence * 100) }}%
        </span>
      </div>

      <div ref="chatBoxRef" class="chat-box">
        <div
          v-for="msg in messages"
          :key="msg.id"
          class="chat-msg"
          :class="`chat-msg--${msg.role}`"
        >
          <div class="chat-bubble">
            <pre class="chat-content">{{ msg.content }}<span v-if="sending && msg.role === 'assistant' && !msg.content" class="cursor-blink">|</span></pre>
            <span class="chat-time">{{ msg.time }}</span>
          </div>
        </div>
      </div>

      <div class="chat-input-bar">
        <el-button
          :type="listening ? 'danger' : 'default'"
          :icon="Microphone"
          circle
          :disabled="!supported || sending"
          :title="listening ? '停止录音' : '语音输入'"
          @click="listening ? stopListen() : startListen()"
        />
        <el-input
          v-model="inputText"
          placeholder="输入追问，或点击麦克风语音提问"
          :disabled="sending"
          @keyup.enter="sendMessage"
        />
        <el-button
          type="success"
          :icon="Promotion"
          :loading="sending"
          @click="sendMessage"
        >
          发送
        </el-button>
      </div>
    </el-card>
  </div>
</template>
