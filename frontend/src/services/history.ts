import type { DiagnoseMode, DiagnoseResponse } from "./api";
import { getAuthToken } from "../composables/authStorage";
import { saveCloudReport } from "./api";

export type HistoryRecord = {
  id: string;
  timestamp: string;
  mode: DiagnoseMode;
  imageId: string;
  zoneId?: string;
  thumbnail?: string;
  summary: string;
  result: DiagnoseResponse;
  cloudId?: string;
};

const STORAGE_KEY = "tomato_ai_history";
const LATEST_KEY = "tomato_ai_latest";

function buildSummary(result: DiagnoseResponse): string {
  if (result.mode === "classification") {
    return `${result.disease_name} · 置信度 ${Math.round(result.confidence * 100)}%`;
  }
  if (result.mode === "detection") {
    return `检测到 ${result.detections.length} 个病斑目标`;
  }
  return `${result.disease_name} · DSI ${result.dsi}% · ${result.severity_level}`;
}

export function getHistoryRecords(): HistoryRecord[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as HistoryRecord[]) : [];
  } catch {
    return [];
  }
}

export function saveHistoryRecord(
  mode: DiagnoseMode,
  imageId: string,
  result: DiagnoseResponse,
  thumbnail?: string,
  zoneId?: string,
): HistoryRecord {
  const record: HistoryRecord = {
    id: crypto.randomUUID(),
    timestamp: new Date().toISOString(),
    mode,
    imageId,
    zoneId,
    thumbnail,
    summary: buildSummary(result),
    result,
  };

  const records = [record, ...getHistoryRecords()].slice(0, 50);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(records));
  localStorage.setItem(LATEST_KEY, JSON.stringify(record));

  // 已登录时同步到云端，供小程序扫码 / 同账号查看
  if (getAuthToken()) {
    void saveCloudReport({
      mode,
      summary: record.summary,
      result,
      image_id: imageId,
      zone_id: zoneId,
      source: "web",
    })
      .then((cloud) => {
        record.cloudId = cloud.id;
        const latest = getHistoryRecords().map((r) => (r.id === record.id ? { ...r, cloudId: cloud.id } : r));
        localStorage.setItem(STORAGE_KEY, JSON.stringify(latest));
        localStorage.setItem(LATEST_KEY, JSON.stringify({ ...record, cloudId: cloud.id }));
      })
      .catch(() => {
        /* 本地历史仍保留 */
      });
  }

  return record;
}

export function getLatestRecord(): HistoryRecord | null {
  try {
    const raw = localStorage.getItem(LATEST_KEY);
    return raw ? (JSON.parse(raw) as HistoryRecord) : null;
  } catch {
    return null;
  }
}

export function deleteHistoryRecord(id: string): void {
  const records = getHistoryRecords().filter((r) => r.id !== id);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(records));
}

export function clearHistory(): void {
  localStorage.removeItem(STORAGE_KEY);
  localStorage.removeItem(LATEST_KEY);
}

export function getHistoryStats() {
  const records = getHistoryRecords();
  const today = new Date().toDateString();
  const todayCount = records.filter(
    (r) => new Date(r.timestamp).toDateString() === today,
  ).length;

  const diseaseMap: Record<string, number> = {};
  const zoneMap: Record<string, number> = {};
  for (const r of records) {
    if (r.result.mode === "classification" || r.result.mode === "segmentation") {
      const name = r.result.disease_name;
      diseaseMap[name] = (diseaseMap[name] ?? 0) + 1;
    } else if (r.result.mode === "detection" && r.result.detections?.length) {
      const name = r.result.detections[0].label;
      diseaseMap[name] = (diseaseMap[name] ?? 0) + 1;
    }
    if (r.zoneId) {
      zoneMap[r.zoneId] = (zoneMap[r.zoneId] ?? 0) + 1;
    }
  }

  const topDisease = Object.entries(diseaseMap).sort((a, b) => b[1] - a[1])[0];

  // 近 7 日检测次数（真实历史）
  const dayCounts: { label: string; count: number }[] = [];
  for (let i = 6; i >= 0; i--) {
    const d = new Date();
    d.setDate(d.getDate() - i);
    const key = d.toDateString();
    const label = `${d.getMonth() + 1}/${d.getDate()}`;
    const count = records.filter((r) => new Date(r.timestamp).toDateString() === key).length;
    dayCounts.push({ label, count });
  }

  return {
    total: records.length,
    todayCount,
    topDisease: topDisease ? topDisease[0] : "—",
    topDiseaseCount: topDisease ? topDisease[1] : 0,
    recent: records.slice(0, 5),
    zoneStats: zoneMap,
    dayCounts,
  };
}

export function fileToDataUrl(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result as string);
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}
