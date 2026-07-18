<script setup lang="ts">
import { computed, ref } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { Plus } from "@element-plus/icons-vue";
import {
  addZone,
  deleteZone,
  getZones,
  getZoneLabel,
  type GreenhouseZone,
} from "../services/zones";
import { getHistoryRecords } from "../services/history";

const zones = ref<GreenhouseZone[]>(getZones());
const records = ref(getHistoryRecords());
const dialogVisible = ref(false);
const form = ref({ code: "", name: "", area: "", crop: "番茄" });

const zoneStats = computed(() => {
  const map: Record<string, number> = {};
  for (const r of records.value) {
    if (r.zoneId) map[r.zoneId] = (map[r.zoneId] ?? 0) + 1;
  }
  return zones.value.map((z) => ({
    ...z,
    count: map[z.id] ?? 0,
  }));
});

function refresh() {
  zones.value = getZones();
  records.value = getHistoryRecords();
}

function openAdd() {
  form.value = { code: "", name: "", area: "", crop: "番茄" };
  dialogVisible.value = true;
}

function submitAdd() {
  if (!form.value.code || !form.value.name) {
    ElMessage.warning("请填写编号和名称");
    return;
  }
  addZone(form.value);
  refresh();
  dialogVisible.value = false;
  ElMessage.success("分区已添加");
}

async function handleDelete(id: string) {
  await ElMessageBox.confirm("确定删除该温室分区？", "提示", { type: "warning" });
  deleteZone(id);
  refresh();
  ElMessage.success("已删除");
}
</script>

<template>
  <div class="zone-page">
    <el-card shadow="never" class="panel">
      <template #header>
        <div class="zone-header">
          <span class="card-title">温室分区管理</span>
          <el-button type="success" :icon="Plus" size="small" @click="openAdd">新增分区</el-button>
        </div>
      </template>

      <el-row :gutter="16">
        <el-col v-for="z in zoneStats" :key="z.id" :xs="24" :sm="12" :md="8">
          <el-card shadow="never" class="zone-card">
            <div class="zone-card-head">
              <el-tag type="success" effect="dark">{{ z.code }}</el-tag>
              <el-button text type="danger" size="small" @click="handleDelete(z.id)">删除</el-button>
            </div>
            <h3>{{ z.name }}</h3>
            <p>{{ z.area }} · {{ z.crop }}</p>
            <div class="zone-count">
              累计检测 <strong>{{ z.count }}</strong> 次
            </div>
          </el-card>
        </el-col>
      </el-row>
    </el-card>

    <el-card shadow="never" class="panel section-row">
      <template #header><span class="card-title">分区检测记录</span></template>
      <el-table :data="records.filter((r) => r.zoneId)" stripe>
        <el-table-column label="分区" width="160">
          <template #default="{ row }">{{ getZoneLabel(row.zoneId) }}</template>
        </el-table-column>
        <el-table-column prop="summary" label="结果" />
        <el-table-column label="时间" width="180">
          <template #default="{ row }">{{ new Date(row.timestamp).toLocaleString("zh-CN") }}</template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!records.some((r) => r.zoneId)" description="在智能诊断页选择分区后，记录将按区域统计" />
    </el-card>

    <el-dialog v-model="dialogVisible" title="新增温室分区" width="420px">
      <el-form label-width="80px">
        <el-form-item label="编号"><el-input v-model="form.code" placeholder="如 C-03" /></el-form-item>
        <el-form-item label="名称"><el-input v-model="form.name" placeholder="如 5号连栋大棚" /></el-form-item>
        <el-form-item label="区域"><el-input v-model="form.area" placeholder="如 东区" /></el-form-item>
        <el-form-item label="作物"><el-input v-model="form.crop" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="success" @click="submitAdd">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.zone-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.zone-card {
  margin-bottom: 12px;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
}

.zone-card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.zone-card h3 {
  margin: 8px 0 4px;
  color: #14532d;
}

.zone-card p {
  margin: 0;
  font-size: 13px;
  color: #6b7280;
}

.zone-count {
  margin-top: 12px;
  font-size: 14px;
  color: #374151;
}

.zone-count strong {
  color: #16a34a;
  font-size: 20px;
}

.section-row {
  margin-top: 16px;
}
</style>
