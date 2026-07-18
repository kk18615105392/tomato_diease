const api = require("../../utils/api");

Page({
  data: { disease: null },
  onLoad(query) {
    if (!query.id) return;
    api
      .fetchWikiDetail(query.id)
      .then((res) => this.setData({ disease: res.disease }))
      .catch((err) => wx.showToast({ title: err.message || "加载失败", icon: "none" }));
  },
});
