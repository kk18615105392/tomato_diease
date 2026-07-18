<script setup lang="ts">
import { computed, ref } from "vue";
import { useRouter } from "vue-router";
import { Search } from "@element-plus/icons-vue";
import { DISEASE_WIKI, type DiseaseWikiEntry } from "../data/diseaseWiki";

const router = useRouter();
const keyword = ref("");
const selectedId = ref(DISEASE_WIKI[0].id);

const filtered = computed(() => {
  const kw = keyword.value.trim();
  if (!kw) return DISEASE_WIKI;
  return DISEASE_WIKI.filter(
    (d) =>
      d.name.includes(kw) ||
      d.pathogen.toLowerCase().includes(kw.toLowerCase()) ||
      d.category.includes(kw),
  );
});

const current = computed(
  () => filtered.value.find((d) => d.id === selectedId.value) ?? filtered.value[0],
);

function severityType(s: DiseaseWikiEntry["severity"]) {
  if (s === "高") return "danger";
  if (s === "中") return "warning";
  return "success";
}

function goDiagnose() {
  router.push("/diagnose");
}
</script>

<template>
  <div class="wiki-page">
    <el-row :gutter="16">
      <el-col :span="7">
        <el-card shadow="never" class="panel wiki-list-card">
          <template #header>
            <div class="card-title">病害检索</div>
          </template>
          <el-input v-model="keyword" placeholder="搜索病害名称/病原..." :prefix-icon="Search" clearable />
          <div class="wiki-list">
            <div
              v-for="item in filtered"
              :key="item.id"
              class="wiki-list-item"
              :class="{ active: current?.id === item.id }"
              @click="selectedId = item.id"
            >
              <span class="wiki-list-name">{{ item.name }}</span>
              <el-tag :type="severityType(item.severity)" size="small" effect="plain">
                {{ item.severity }}危
              </el-tag>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="17">
        <el-card v-if="current" shadow="never" class="panel wiki-detail">
          <div class="wiki-detail-header">
            <div>
              <h2>{{ current.name }}</h2>
              <p class="wiki-pathogen">{{ current.pathogen }} · {{ current.category }}</p>
            </div>
            <el-tag :type="severityType(current.severity)" size="large" effect="dark">
              危害等级：{{ current.severity }}
            </el-tag>
          </div>

          <el-divider />

          <div class="wiki-section">
            <h4>典型症状</h4>
            <ul>
              <li v-for="(s, i) in current.symptoms" :key="i">{{ s }}</li>
            </ul>
          </div>

          <div class="wiki-section">
            <h4>易发条件</h4>
            <p>{{ current.conditions }}</p>
          </div>

          <div class="wiki-section">
            <h4>农业防治</h4>
            <ul>
              <li v-for="(p, i) in current.prevention" :key="i">{{ p }}</li>
            </ul>
          </div>

          <div class="wiki-section">
            <h4>推荐药剂</h4>
            <div class="pesticide-tags">
              <el-tag v-for="(p, i) in current.pesticides" :key="i" type="success" effect="plain">
                {{ p }}
              </el-tag>
            </div>
          </div>

          <el-button type="success" class="wiki-action" @click="goDiagnose">
            上传叶片图片进行 AI 诊断 →
          </el-button>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.wiki-list-card {
  position: sticky;
  top: 0;
}

.wiki-list {
  margin-top: 12px;
  max-height: 520px;
  overflow-y: auto;
}

.wiki-list-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  margin-bottom: 4px;
  transition: background 0.2s;
}

.wiki-list-item:hover {
  background: #f0fdf4;
}

.wiki-list-item.active {
  background: #dcfce7;
  border: 1px solid #86efac;
}

.wiki-list-name {
  font-weight: 600;
  color: #374151;
  font-size: 14px;
}

.wiki-detail-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.wiki-detail h2 {
  margin: 0;
  color: #14532d;
}

.wiki-pathogen {
  margin: 6px 0 0;
  color: #6b7280;
  font-size: 14px;
  font-style: italic;
}

.wiki-section {
  margin-bottom: 20px;
}

.wiki-section h4 {
  margin: 0 0 8px;
  color: #166534;
  font-size: 15px;
  border-left: 3px solid #16a34a;
  padding-left: 8px;
}

.wiki-section ul {
  margin: 0;
  padding-left: 20px;
  color: #4b5563;
  line-height: 1.8;
  font-size: 14px;
}

.wiki-section p {
  margin: 0;
  color: #4b5563;
  line-height: 1.7;
  font-size: 14px;
}

.pesticide-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.wiki-action {
  margin-top: 8px;
}
</style>
