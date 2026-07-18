<script setup lang="ts">
import { WarningFilled } from "@element-plus/icons-vue";
import { getSeasonalRiskAlerts } from "../data/diseaseWiki";

const alerts = getSeasonalRiskAlerts();
</script>

<template>
  <div v-if="alerts.length" class="risk-banner">
    <el-carousel height="48px" direction="vertical" :autoplay="true" indicator-position="none">
      <el-carousel-item v-for="(alert, idx) in alerts" :key="idx">
        <div class="risk-item" :class="alert.level">
          <el-icon><WarningFilled /></el-icon>
          <span class="risk-disease">【{{ alert.disease }}】</span>
          <span>{{ alert.message }}</span>
        </div>
      </el-carousel-item>
    </el-carousel>
  </div>
</template>

<style scoped>
.risk-banner {
  margin-bottom: 16px;
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid #fde68a;
}

.risk-item {
  display: flex;
  align-items: center;
  gap: 8px;
  height: 48px;
  padding: 0 16px;
  font-size: 13px;
}

.risk-item.warning {
  background: linear-gradient(90deg, #fffbeb, #fef3c7);
  color: #92400e;
}

.risk-item.danger {
  background: linear-gradient(90deg, #fef2f2, #fecaca);
  color: #991b1b;
}

.risk-disease {
  font-weight: 700;
}
</style>
