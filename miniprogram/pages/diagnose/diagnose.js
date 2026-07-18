const api = require("../../utils/api");

Page({
  data: {
    preview: "",
    filePath: "",
    loading: false,
  },
  ensureLogin() {
    if (!api.getToken()) {
      wx.showModal({
        title: "需要登录",
        content: "登录后诊断报告可与 Web 系统同步",
        confirmText: "去登录",
        success: (res) => {
          if (res.confirm) wx.navigateTo({ url: "/pages/login/login" });
        },
      });
      return false;
    }
    return true;
  },
  takePhoto() {
    wx.chooseMedia({
      count: 1,
      mediaType: ["image"],
      sourceType: ["camera"],
      success: (res) => {
        const path = res.tempFiles[0].tempFilePath;
        this.setData({ preview: path, filePath: path });
      },
    });
  },
  chooseAlbum() {
    wx.chooseMedia({
      count: 1,
      mediaType: ["image"],
      sourceType: ["album"],
      success: (res) => {
        const path = res.tempFiles[0].tempFilePath;
        this.setData({ preview: path, filePath: path });
      },
    });
  },
  runDiagnose() {
    if (!this.ensureLogin()) return;
    if (!this.data.filePath) return;
    this.setData({ loading: true });
    api
      .diagnoseImage(this.data.filePath)
      .then(async ({ imageId, result }) => {
        const summary = api.buildSummary(result);
        let reportId = "";
        try {
          const saved = await api.saveReport({
            mode: result.mode || "detection",
            image_id: imageId,
            summary,
            result,
            source: "miniprogram",
          });
          reportId = saved.report && saved.report.id;
        } catch (e) {
          // 仍可本地查看结果
        }
        wx.setStorageSync("mp_last_result", { imageId, result, summary, reportId });
        wx.navigateTo({
          url: `/pages/result/result?reportId=${reportId || ""}`,
        });
      })
      .catch((err) => wx.showToast({ title: err.message || "诊断失败", icon: "none" }))
      .finally(() => this.setData({ loading: false }));
  },
});
