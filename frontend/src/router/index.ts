import { createRouter, createWebHistory } from "vue-router";
import MainLayout from "../layouts/MainLayout.vue";
import HomeView from "../views/HomeView.vue";
import DiagnoseView from "../views/DiagnoseView.vue";
import CompareView from "../views/CompareView.vue";
import HistoryView from "../views/HistoryView.vue";
import ExpertView from "../views/ExpertView.vue";
import WikiView from "../views/WikiView.vue";
import ZoneView from "../views/ZoneView.vue";
import ReferenceView from "../views/ReferenceView.vue";
import MetricsView from "../views/MetricsView.vue";
import EnhancementDashboardView from "../views/EnhancementDashboardView.vue";
import MiniProgramView from "../views/MiniProgramView.vue";
import LoginView from "../views/LoginView.vue";
import { getAuthToken } from "../composables/authStorage";

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: "/login",
      name: "login",
      component: LoginView,
      meta: { public: true },
    },
    {
      path: "/",
      component: MainLayout,
      meta: { requiresAuth: true },
      children: [
        { path: "", redirect: "/home" },
        { path: "home", name: "home", component: HomeView },
        { path: "diagnose", name: "diagnose", component: DiagnoseView },
        { path: "compare", name: "compare", component: CompareView },
        { path: "wiki", name: "wiki", component: WikiView },
        { path: "reference", name: "reference", component: ReferenceView },
        { path: "zones", name: "zones", component: ZoneView },
        { path: "metrics", name: "metrics", component: MetricsView },
        { path: "enhancement-dashboard", name: "enhancement", component: EnhancementDashboardView },
        { path: "history", name: "history", component: HistoryView },
        { path: "expert", name: "expert", component: ExpertView },
        { path: "miniprogram", name: "miniprogram", component: MiniProgramView },
      ],
    },
  ],
});

router.beforeEach((to) => {
  const loggedIn = Boolean(getAuthToken());
  if (to.meta.public) {
    if (loggedIn && to.name === "login") {
      return { path: "/home" };
    }
    return true;
  }
  if (to.matched.some((r) => r.meta.requiresAuth) && !loggedIn) {
    return { path: "/login", query: { redirect: to.fullPath } };
  }
  return true;
});

export default router;
