<script setup lang="ts">
const steps = [
  { title: "导入工程", desc: "用微信开发者工具打开项目根目录下的 miniprogram/ 文件夹" },
  { title: "联调设置", desc: "详情 → 勾选「不校验合法域名」；真机调试把 utils/config.js 的 API_BASE 改成电脑局域网 IP" },
  { title: "同账号登录", desc: "小程序与 Web 使用同一用户名密码，报告自动互通" },
  { title: "扫码看报告", desc: "Web 诊断后点「扫码分享」，小程序首页点「扫码看报告」即可打开云端详情" },
];

const features = [
  { name: "拍叶诊断", link: "调用 /api/upload + /api/diagnose（detection）" },
  { name: "我的报告", link: "GET /api/reports，与 Web 同账号" },
  { name: "病害百科", link: "GET /api/wiki/diseases" },
  { name: "扫码看报告", link: "GET /api/reports/:id" },
];
</script>

<template>
  <div class="mp-page">
    <el-card shadow="never" class="panel hero">
      <h2>Tomato AI 田间小程序</h2>
      <p>面向农技员田间拍叶场景，与本 Web 系统共用账号、检测模型与报告库。</p>
      <el-tag type="success">工程目录：miniprogram/</el-tag>
    </el-card>

    <el-row :gutter="16" class="section-row">
      <el-col :span="12">
        <el-card shadow="never" class="panel">
          <template #header><span class="card-title">接入步骤</span></template>
          <el-steps direction="vertical" :active="4">
            <el-step v-for="s in steps" :key="s.title" :title="s.title" :description="s.desc" />
          </el-steps>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="never" class="panel">
          <template #header><span class="card-title">功能与后端关联</span></template>
          <el-table :data="features" size="small">
            <el-table-column prop="name" label="小程序模块" width="120" />
            <el-table-column prop="link" label="关联接口" />
          </el-table>
          <p class="note">
            说明文档：<code>miniprogram/README.md</code>
          </p>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.hero h2 { margin: 0 0 8px; color: #14532d; }
.hero p { margin: 0 0 12px; color: #6b7280; }
.section-row { margin-top: 16px; }
.note { margin-top: 16px; font-size: 13px; color: #6b7280; }
code { background: #ecfdf5; padding: 2px 6px; border-radius: 4px; color: #166534; }
</style>
