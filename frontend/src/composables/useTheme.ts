import { ref, watch } from "vue";

const STORAGE_KEY = "tomato_ai_dark_mode";

const isDark = ref(localStorage.getItem(STORAGE_KEY) === "true");

function applyTheme(dark: boolean) {
  document.documentElement.classList.toggle("dark-screen", dark);
  localStorage.setItem(STORAGE_KEY, String(dark));
}

watch(isDark, (v) => applyTheme(v), { immediate: true });

export function useTheme() {
  function toggleDark() {
    isDark.value = !isDark.value;
  }
  return { isDark, toggleDark };
}
