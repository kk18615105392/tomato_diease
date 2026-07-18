const { API_BASE } = require("./config");

function getToken() {
  return wx.getStorageSync("tomato_ai_token") || "";
}

function request({ url, method = "GET", data, header = {}, auth = true }) {
  return new Promise((resolve, reject) => {
    const headers = {
      "Content-Type": "application/json",
      ...header,
    };
    if (auth) {
      const token = getToken();
      if (token) headers.Authorization = `Bearer ${token}`;
    }
    wx.request({
      url: `${API_BASE}${url}`,
      method,
      data,
      header: headers,
      success(res) {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data);
        } else {
          const msg = (res.data && res.data.error) || `请求失败(${res.statusCode})`;
          reject(new Error(msg));
        }
      },
      fail(err) {
        reject(new Error(err.errMsg || "网络错误，请检查后端是否启动"));
      },
    });
  });
}

function login(username, password) {
  return request({
    url: "/api/auth/login",
    method: "POST",
    data: { username, password },
    auth: false,
  });
}

function register(username, password, display_name) {
  return request({
    url: "/api/auth/register",
    method: "POST",
    data: { username, password, display_name },
    auth: false,
  });
}

function fetchMe() {
  return request({ url: "/api/auth/me" });
}

function fetchWiki() {
  return request({ url: "/api/wiki/diseases", auth: false });
}

function fetchWikiDetail(id) {
  return request({ url: `/api/wiki/diseases/${id}`, auth: false });
}

function fetchReports() {
  return request({ url: "/api/reports" });
}

function fetchReport(id) {
  return request({ url: `/api/reports/${id}`, auth: false });
}

function saveReport(payload) {
  return request({
    url: "/api/reports",
    method: "POST",
    data: payload,
  });
}

/** 上传图片并做目标检测诊断 */
function diagnoseImage(filePath) {
  return new Promise((resolve, reject) => {
    const token = getToken();
    wx.uploadFile({
      url: `${API_BASE}/api/upload`,
      filePath,
      name: "image",
      header: token ? { Authorization: `Bearer ${token}` } : {},
      success(uploadRes) {
        let body;
        try {
          body = JSON.parse(uploadRes.data);
        } catch (e) {
          reject(new Error("上传响应解析失败"));
          return;
        }
        if (uploadRes.statusCode >= 400) {
          reject(new Error(body.error || "上传失败"));
          return;
        }
        const imageId = body.image_id;
        request({
          url: "/api/diagnose",
          method: "POST",
          data: { image_id: imageId, mode: "detection" },
        })
          .then((diag) => resolve({ imageId, result: diag }))
          .catch(reject);
      },
      fail(err) {
        reject(new Error(err.errMsg || "上传失败"));
      },
    });
  });
}

function buildSummary(result) {
  if (!result) return "诊断完成";
  if (result.mode === "classification") {
    return `${result.disease_name} · 置信度 ${Math.round((result.confidence || 0) * 100)}%`;
  }
  if (result.mode === "detection") {
    const n = (result.detections || []).length;
    if (!n) return "未检测到目标";
    const top = result.detections[0];
    return `检测到 ${n} 个目标 · ${top.label}`;
  }
  return result.disease_name || "诊断完成";
}

module.exports = {
  request,
  login,
  register,
  fetchMe,
  fetchWiki,
  fetchWikiDetail,
  fetchReports,
  fetchReport,
  saveReport,
  diagnoseImage,
  buildSummary,
  getToken,
};
