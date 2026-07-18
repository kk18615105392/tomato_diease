const api = require("../../utils/api");

Page({
  data: {
    user: null,
    alerts: [],
  },
  onShow() {
    const app = getApp();
    this.setData({ user: app.globalData.user || wx.getStorageSync("tomato_ai_user") || null });
    this.loadAlerts();
  },
  loadAlerts() {
    api
      .fetchWiki()
      .then((res) => this.setData({ alerts: res.alerts || [] }))
      .catch(() => {});
  },
  goLogin() {
    wx.navigateTo({ url: "/pages/login/login" });
  },
  goDiagnose() {
    wx.switchTab({ url: "/pages/diagnose/diagnose" });
  },
  goHistory() {
    wx.switchTab({ url: "/pages/history/history" });
  },
  goWiki() {
    wx.switchTab({ url: "/pages/wiki/wiki" });
  },
  scanReport() {
    wx.scanCode({
      onlyFromCamera: false,
      success: (res) => {
        let id = "";
        const raw = res.result || "";
        try {
          const obj = JSON.parse(raw);
          id = obj.report_id || obj.id || "";
        } catch (e) {
          const m = raw.match(/[?&]id=([a-f0-9]+)/i) || raw.match(/([a-f0-9]{16,})/i);
          if (m) id = m[1];
        }
        if (!id) {
          wx.showToast({ title: "无法识别报告码", icon: "none" });
          return;
        }
        wx.navigateTo({ url: `/pages/report/report?id=${id}` });
      },
      fail: () => wx.showToast({ title: "已取消扫码", icon: "none" }),
    });
  },
});
