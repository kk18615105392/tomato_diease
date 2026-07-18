/** 认证 token 本地存储（避免 api ↔ useAuth 循环依赖） */

const TOKEN_KEY = "tomato_ai_token";
const USER_KEY = "tomato_ai_user";

export function getAuthToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setAuthSession(token: string, userJson: string) {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, userJson);
}

export function clearAuthSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

export function getStoredUserJson(): string | null {
  return localStorage.getItem(USER_KEY);
}

export { TOKEN_KEY, USER_KEY };
