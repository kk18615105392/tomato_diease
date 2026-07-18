App({
  globalData: {
    user: null,
    token: null,
  },
  onLaunch() {
    const token = wx.getStorageSync("tomato_ai_token");
    const user = wx.getStorageSync("tomato_ai_user");
    if (token) this.globalData.token = token;
    if (user) this.globalData.user = user;
  },
});
