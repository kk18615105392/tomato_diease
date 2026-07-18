Page({
  data: {
    result: null,
    summary: "",
    reportId: "",
  },
  onLoad(query) {
    const cached = wx.getStorageSync("mp_last_result") || {};
    const result = cached.result || null;
    if (result && result.mode === "detection" && result.detections) {
      result.detections = result.detections.map((d) => ({
        ...d,
        confidencePct: Math.round((d.confidence || 0) * 100),
      }));
    }
    if (result && result.mode === "classification") {
      result.confidencePct = Math.round((result.confidence || 0) * 100);
    }
    this.setData({
      result,
      summary: cached.summary || "诊断完成",
      reportId: query.reportId || cached.reportId || "",
    });
  },
  goHistory() {
    wx.switchTab({ url: "/pages/history/history" });
  },
  goWiki() {
    wx.switchTab({ url: "/pages/wiki/wiki" });
  },
});
