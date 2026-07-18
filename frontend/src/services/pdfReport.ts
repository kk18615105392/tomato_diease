import html2pdf from "html2pdf.js";
import type { HistoryRecord } from "./history";
import { modeLabel } from "./api";

function buildReportHtml(record: HistoryRecord): string {
  const time = new Date(record.timestamp).toLocaleString("zh-CN");
  const serial = record.id.slice(0, 8).toUpperCase();
  let detailRows = "";

  const r = record.result;
  if (r.mode === "classification") {
    detailRows = `
      <tr><td>病害类别</td><td>${r.disease_name}</td></tr>
      <tr><td>置信度</td><td>${(r.confidence * 100).toFixed(1)}%</td></tr>`;
  } else if (r.mode === "detection") {
    detailRows = `<tr><td>检测目标数</td><td>${r.detections.length} 个</td></tr>`;
    r.detections.forEach((d, i) => {
      detailRows += `<tr><td>目标 ${i + 1}</td><td>${d.label} (${(d.confidence * 100).toFixed(0)}%)</td></tr>`;
    });
  } else {
    detailRows = `
      <tr><td>病害类别</td><td>${r.disease_name}</td></tr>
      <tr><td>病情指数 DSI</td><td>${r.dsi}%</td></tr>
      <tr><td>发病等级</td><td>${r.severity_level}</td></tr>`;
  }

  const imgHtml = record.thumbnail
    ? `<img src="${record.thumbnail}" style="max-width:100%;max-height:200px;border-radius:8px;margin:12px 0;" />`
    : "";

  return `
    <div style="font-family:'Microsoft YaHei',sans-serif;padding:24px;color:#1f2937;">
      <div style="text-align:center;border-bottom:3px solid #166534;padding-bottom:16px;margin-bottom:20px;">
        <h1 style="margin:0;color:#14532d;font-size:22px;">番茄病害智能检测与防治报告</h1>
        <p style="margin:8px 0 0;color:#6b7280;font-size:13px;">Tomato Disease Intelligent Detection Report</p>
      </div>
      <table style="width:100%;font-size:13px;margin-bottom:16px;">
        <tr><td style="color:#6b7280;width:100px;">报告编号</td><td><b>${serial}</b></td></tr>
        <tr><td style="color:#6b7280;">检测时间</td><td>${time}</td></tr>
        <tr><td style="color:#6b7280;">诊断模式</td><td>${modeLabel(record.mode)}</td></tr>
        <tr><td style="color:#6b7280;">图片 ID</td><td>${record.imageId}</td></tr>
      </table>
      ${imgHtml}
      <h3 style="color:#166534;font-size:15px;border-left:4px solid #16a34a;padding-left:8px;">检测指标</h3>
      <table style="width:100%;border-collapse:collapse;font-size:13px;margin:12px 0;">
        ${detailRows}
      </table>
      <h3 style="color:#166534;font-size:15px;border-left:4px solid #16a34a;padding-left:8px;">备注</h3>
      <p style="font-size:13px;color:#4b5563;">${r.note}</p>
      <div style="margin-top:24px;padding-top:12px;border-top:1px solid #e5e7eb;font-size:11px;color:#9ca3af;text-align:center;">
        本报告由番茄病虫害智能诊断系统自动生成 · 仅供参考
      </div>
    </div>`;
}

export async function exportReportPdf(record: HistoryRecord): Promise<void> {
  const container = document.createElement("div");
  container.innerHTML = buildReportHtml(record);
  container.style.width = "210mm";
  document.body.appendChild(container);

  const serial = record.id.slice(0, 8).toUpperCase();
  await html2pdf()
    .set({
      margin: 10,
      filename: `番茄病害检测报告_${serial}.pdf`,
      image: { type: "jpeg", quality: 0.95 },
      html2canvas: { scale: 2, useCORS: true },
      jsPDF: { unit: "mm", format: "a4", orientation: "portrait" },
    })
    .from(container)
    .save();

  document.body.removeChild(container);
}
