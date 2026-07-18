const api = require("../../utils/api");

Page({
  data: {
    report: null,
    detections: [],
    confidencePct: 0,
    error: "",
  },
  onLoad(query) {
    const id = query.id;
    if (!id) {
      this.setData({ error: "缺少报告 ID" });
      return;
    }
    api
      .fetchReport(id)
      .then((res) => {
        const report = res.report;
        let detections = [];
        let confidencePct = 0;
        if (report.result && report.result.mode === "detection") {
          detections = (report.result.detections || []).map((d) => ({
            ...d,
            confidencePct: Math.round((d.confidence || 0) * 100),
          }));
        }
        if (report.result && report.result.mode === "classification") {
          confidencePct = Math.round((report.result.confidence || 0) * 100);
        }
        this.setData({ report, detections, confidencePct });
      })
      .catch((err) => this.setData({ error: err.message || "报告不存在" }));
  },
});
