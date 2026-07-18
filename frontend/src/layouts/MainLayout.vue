<script setup lang="ts">
import { onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import {
  ChatDotRound,
  DataAnalysis,
  DataBoard,
  Files,
  Grid,
  House,
  PictureRounded,
  Reading,
  TrendCharts,
  Sunny,
  Moon,
  Iphone,
  SwitchButton,
  User,
} from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import { useTheme } from "../composables/useTheme";
import { useAuth } from "../composables/useAuth";

const route = useRoute();
const router = useRouter();
const { isDark, toggleDark } = useTheme();
const { user, logout, bootstrap } = useAuth();

type MenuItem = {
  index: string;
  label: string;
  icon: unknown;
};

const menuItems: MenuItem[] = [
  { index: "/home", label: "首页大屏", icon: House },
  { index: "/diagnose", label: "智能诊断", icon: PictureRounded },
  { index: "/compare", label: "多图对比", icon: DataAnalysis },
  { index: "/reference", label: "叶片对照库", icon: Reading },
  { index: "/wiki", label: "病害百科", icon: Reading },
  { index: "/zones", label: "温室分区", icon: Grid },
  { index: "/metrics", label: "模型看板", icon: DataBoard },
  { index: "/enhancement-dashboard", label: "域适应看板(Ch6)", icon: TrendCharts },
  { index: "/history", label: "历史报告", icon: Files },
  { index: "/expert", label: "专家问答", icon: ChatDotRound },
  { index: "/miniprogram", label: "田间小程序", icon: Iphone },
];

onMounted(() => {
  void bootstrap();
});

function handleLogout() {
  logout();
  ElMessage.success("已退出登录");
  void router.push("/login");
}
</script>

<template>
  <el-container class="app-shell">
    <el-aside width="240px" class="side">
      <div class="brand">
        <h1>Tomato AI</h1>
        <p>病虫害智能决策平台</p>
      </div>
      <el-menu
        router
        :default-active="route.path"
        class="menu"
        background-color="transparent"
        text-color="#d6f5de"
        active-text-color="#ffffff"
      >
        <el-menu-item v-for="item in menuItems" :key="item.index" :index="item.index">
          <el-icon><component :is="item.icon" /></el-icon>
          <span>{{ item.label }}</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="header">
        <h2>番茄病虫害智能诊断与专家辅助决策系统</h2>
        <div class="header-actions">
          <div v-if="user" class="user-chip">
            <el-icon><User /></el-icon>
            <span>{{ user.display_name || user.username }}</span>
          </div>
          <el-button circle :title="isDark ? '切换亮色' : '切换暗色大屏'" @click="toggleDark">
            <el-icon><Moon v-if="!isDark" /><Sunny v-else /></el-icon>
          </el-button>
          <el-button circle title="退出登录" @click="handleLogout">
            <el-icon><SwitchButton /></el-icon>
          </el-button>
        </div>
      </el-header>
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.user-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 999px;
  background: #ecfdf5;
  color: #166534;
  font-size: 13px;
  font-weight: 600;
}
</style>
