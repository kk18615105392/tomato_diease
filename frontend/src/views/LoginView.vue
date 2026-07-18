<script setup lang="ts">
import { reactive, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { useAuth } from "../composables/useAuth";

const router = useRouter();
const route = useRoute();
const { login, register } = useAuth();

const mode = ref<"login" | "register">("login");
const loading = ref(false);

const form = reactive({
  username: "",
  password: "",
  confirm: "",
  display_name: "",
});

async function submit() {
  if (!form.username.trim() || !form.password) {
    ElMessage.warning("请输入用户名和密码");
    return;
  }
  if (mode.value === "register") {
    if (form.password.length < 6) {
      ElMessage.warning("密码至少 6 位");
      return;
    }
    if (form.password !== form.confirm) {
      ElMessage.warning("两次输入的密码不一致");
      return;
    }
  }

  loading.value = true;
  try {
    if (mode.value === "login") {
      await login(form.username.trim(), form.password);
      ElMessage.success("登录成功");
    } else {
      await register(form.username.trim(), form.password, form.display_name.trim() || undefined);
      ElMessage.success("注册成功，已自动登录");
    }
    const redirect = typeof route.query.redirect === "string" ? route.query.redirect : "/home";
    await router.replace(redirect || "/home");
  } catch (err: unknown) {
    const msg =
      (err as { response?: { data?: { error?: string } } })?.response?.data?.error ||
      (mode.value === "login" ? "登录失败" : "注册失败");
    ElMessage.error(msg);
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="auth-page">
    <div class="auth-panel">
      <div class="auth-brand">
        <h1>Tomato AI</h1>
        <p>番茄病虫害智能诊断与专家辅助决策系统</p>
      </div>

      <el-tabs v-model="mode" class="auth-tabs" stretch>
        <el-tab-pane label="登录" name="login" />
        <el-tab-pane label="注册" name="register" />
      </el-tabs>

      <el-form label-position="top" @submit.prevent="submit">
        <el-form-item label="用户名">
          <el-input
            v-model="form.username"
            placeholder="2–32 位字母/数字/中文"
            maxlength="32"
            autocomplete="username"
          />
        </el-form-item>

        <el-form-item v-if="mode === 'register'" label="显示名称（可选）">
          <el-input v-model="form.display_name" placeholder="例如：张农技员" maxlength="32" />
        </el-form-item>

        <el-form-item label="密码">
          <el-input
            v-model="form.password"
            type="password"
            show-password
            placeholder="至少 6 位"
            autocomplete="current-password"
            @keyup.enter="submit"
          />
        </el-form-item>

        <el-form-item v-if="mode === 'register'" label="确认密码">
          <el-input
            v-model="form.confirm"
            type="password"
            show-password
            placeholder="再次输入密码"
            @keyup.enter="submit"
          />
        </el-form-item>

        <el-button type="primary" class="submit-btn" :loading="loading" @click="submit">
          {{ mode === "login" ? "登录" : "注册并进入系统" }}
        </el-button>
      </el-form>

      <p class="auth-hint">注册后可使用智能诊断、模型看板等完整功能</p>
    </div>
  </div>
</template>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background:
    radial-gradient(ellipse at 20% 20%, rgba(34, 197, 94, 0.18), transparent 50%),
    radial-gradient(ellipse at 80% 80%, rgba(22, 101, 52, 0.22), transparent 45%),
    linear-gradient(160deg, #0a3f27 0%, #14532d 45%, #052e16 100%);
}

.auth-panel {
  width: min(420px, 100%);
  background: rgba(255, 255, 255, 0.96);
  border-radius: 16px;
  padding: 32px 28px 28px;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.25);
}

.auth-brand h1 {
  margin: 0;
  font-size: 28px;
  color: #14532d;
  letter-spacing: 0.5px;
}

.auth-brand p {
  margin: 8px 0 20px;
  font-size: 13px;
  color: #6b7280;
  line-height: 1.5;
}

.auth-tabs {
  margin-bottom: 8px;
}

.submit-btn {
  width: 100%;
  margin-top: 8px;
  height: 42px;
  font-size: 15px;
}

.auth-hint {
  margin: 16px 0 0;
  text-align: center;
  font-size: 12px;
  color: #9ca3af;
}
</style>
