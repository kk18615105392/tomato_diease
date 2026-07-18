const api = require("../../utils/api");

Page({
  data: {
    mode: "login",
    username: "",
    password: "",
    displayName: "",
    loading: false,
  },
  switchMode(e) {
    this.setData({ mode: e.currentTarget.dataset.mode });
  },
  onUser(e) {
    this.setData({ username: e.detail.value });
  },
  onPass(e) {
    this.setData({ password: e.detail.value });
  },
  onDisplay(e) {
    this.setData({ displayName: e.detail.value });
  },
  submit() {
    const { mode, username, password, displayName } = this.data;
    if (!username.trim() || !password) {
      wx.showToast({ title: "请输入用户名和密码", icon: "none" });
      return;
    }
    this.setData({ loading: true });
    const task =
      mode === "login"
        ? api.login(username.trim(), password)
        : api.register(username.trim(), password, displayName.trim() || undefined);
    task
      .then((res) => {
        wx.setStorageSync("tomato_ai_token", res.token);
        wx.setStorageSync("tomato_ai_user", res.user);
        const app = getApp();
        app.globalData.token = res.token;
        app.globalData.user = res.user;
        wx.showToast({ title: "成功", icon: "success" });
        setTimeout(() => wx.navigateBack({ fail: () => wx.switchTab({ url: "/pages/index/index" }) }), 500);
      })
      .catch((err) => wx.showToast({ title: err.message || "失败", icon: "none" }))
      .finally(() => this.setData({ loading: false }));
  },
});
