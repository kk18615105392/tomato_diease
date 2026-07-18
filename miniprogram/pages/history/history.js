const api = require("../../utils/api");

Page({
  data: {
    token: "",
    reports: [],
  },
  onShow() {
    this.setData({ token: api.getToken() });
    if (api.getToken()) this.load();
  },
  onPullDownRefresh() {
    this.load().finally(() => wx.stopPullDownRefresh());
  },
  load() {
    return api
      .fetchReports()
      .then((res) => this.setData({ reports: res.reports || [] }))
      .catch((err) => wx.showToast({ title: err.message || "加载失败", icon: "none" }));
  },
  goLogin() {
    wx.navigateTo({ url: "/pages/login/login" });
  },
  openReport(e) {
    const id = e.currentTarget.dataset.id;
    wx.navigateTo({ url: `/pages/report/report?id=${id}` });
  },
});
