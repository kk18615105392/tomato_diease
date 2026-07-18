import { computed, ref } from "vue";
import { loginApi, registerApi, fetchMe, type AuthUser } from "../services/api";
import {
  clearAuthSession,
  getAuthToken,
  getStoredUserJson,
  setAuthSession,
} from "./authStorage";

function loadStoredUser(): AuthUser | null {
  try {
    const raw = getStoredUserJson();
    return raw ? (JSON.parse(raw) as AuthUser) : null;
  } catch {
    return null;
  }
}

const token = ref<string | null>(getAuthToken());
const user = ref<AuthUser | null>(loadStoredUser());
const bootstrapped = ref(false);

function persist(nextToken: string, nextUser: AuthUser) {
  token.value = nextToken;
  user.value = nextUser;
  setAuthSession(nextToken, JSON.stringify(nextUser));
}

function clearAuth() {
  token.value = null;
  user.value = null;
  clearAuthSession();
}

export { getAuthToken };

export function useAuth() {
  const isLoggedIn = computed(() => Boolean(token.value && user.value));

  async function login(username: string, password: string) {
    const res = await loginApi(username, password);
    persist(res.token, res.user);
    return res.user;
  }

  async function register(username: string, password: string, displayName?: string) {
    const res = await registerApi(username, password, displayName);
    persist(res.token, res.user);
    return res.user;
  }

  /** 无后端时的访客预览（GitHub Pages 静态站可用） */
  function enterGuest() {
    const guest: AuthUser = {
      id: 0,
      username: "guest",
      display_name: "访客预览",
      created_at: new Date().toISOString(),
    };
    persist("guest:local-preview", guest);
    return guest;
  }

  function isGuest() {
    return Boolean(token.value?.startsWith("guest:"));
  }

  function logout() {
    clearAuth();
  }

  async function bootstrap() {
    if (bootstrapped.value) return;
    bootstrapped.value = true;
    if (!token.value) return;
    if (token.value.startsWith("guest:")) return;
    try {
      const me = await fetchMe();
      user.value = me.user;
      setAuthSession(token.value, JSON.stringify(me.user));
    } catch {
      clearAuth();
    }
  }

  return {
    token,
    user,
    isLoggedIn,
    login,
    register,
    enterGuest,
    isGuest,
    logout,
    bootstrap,
  };
}
