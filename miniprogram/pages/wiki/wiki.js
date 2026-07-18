const api = require("../../utils/api");

function sevClass(severity) {
  if (severity === "高") return "high";
  if (severity === "中") return "mid";
  return "low";
}

Page({
  data: { diseases: [] },
  onShow() {
    api
      .fetchWiki()
      .then((res) => {
        const diseases = (res.diseases || []).map((d) => ({
          ...d,
          sevClass: sevClass(d.severity),
        }));
        this.setData({ diseases });
      })
      .catch((err) => wx.showToast({ title: err.message || "加载失败", icon: "none" }));
  },
  openDetail(e) {
    wx.navigateTo({ url: `/pages/wiki-detail/wiki-detail?id=${e.currentTarget.dataset.id}` });
  },
});
