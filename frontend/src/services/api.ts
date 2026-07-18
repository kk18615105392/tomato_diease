import axios from "axios";
import { getAuthToken } from "../composables/authStorage";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "",
  timeout: 30000,
});

api.interceptors.request.use((config) => {
  const token = getAuthToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export type AuthUser = {
  id: number;
  username: string;
  display_name: string;
  created_at: string;
};

export type AuthResponse = {
  token: string;
  user: AuthUser;
};

export async function loginApi(username: string, password: string): Promise<AuthResponse> {
  const { data } = await api.post<AuthResponse>("/api/auth/login", { username, password });
  return data;
}

export async function registerApi(
  username: string,
  password: string,
  displayName?: string,
): Promise<AuthResponse> {
  const { data } = await api.post<AuthResponse>("/api/auth/register", {
    username,
    password,
    display_name: displayName || undefined,
  });
  return data;
}

export async function fetchMe(): Promise<{ user: AuthUser }> {
  const { data } = await api.get<{ user: AuthUser }>("/api/auth/me");
  return data;
}

export type UploadResponse = {
  image_id: string;
  image_path: string;
};

export type DiagnoseMode = "classification" | "detection" | "segmentation";

export type BBox = {
  x: number;
  y: number;
  width: number;
  height: number;
};

export type DetectionItem = {
  label: string;
  confidence: number;
  bbox: BBox;
};

export type ClassificationResult = {
  mode: "classification";
  image_id: string;
  disease_name: string;
  confidence: number;
  note: string;
  top_classes?: { label: string; count: number; confidence: number }[];
  model_label?: string;
  infer_ms?: number;
};

export type DetectionResult = {
  mode: "detection";
  image_id: string;
  detections: DetectionItem[];
  model_key?: string;
  model_label?: string;
  dataset?: string;
  task_type?: string;
  task_label?: string;
  task_hint?: string;
  infer_ms?: number;
  note: string;
  error?: string;
};

/** @deprecated 论文已取消分割章节；保留类型仅兼容历史记录 */
export type SegmentationResult = {
  mode: "segmentation";
  image_id: string;
  disease_name: string;
  dsi: number;
  severity_level: string;
  mask_base64: string;
  note: string;
};

export type DiagnoseResponse = ClassificationResult | DetectionResult | SegmentationResult;

export const MODE_OPTIONS: { value: DiagnoseMode; label: string; desc: string }[] = [
  { value: "classification", label: "快速定性筛查", desc: "YOLO 类别聚合" },
  { value: "detection", label: "精准目标定位", desc: "YOLO 目标检测" },
];

export async function uploadImage(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("image", file);
  const { data } = await api.post<UploadResponse>("/api/upload", formData);
  return data;
}

export async function diagnoseImage(
  imageId: string,
  mode: DiagnoseMode,
  detectionModel?: string,
): Promise<DiagnoseResponse> {
  const body: Record<string, string> = { image_id: imageId, mode };
  if (detectionModel) {
    body.detection_model = detectionModel;
  }
  const { data } = await api.post<DiagnoseResponse>("/api/diagnose", body);
  return data;
}

export type DetectionModelInfo = {
  key: string;
  label: string;
  improvement?: string;
  recommend?: string;
  group?: "ablation" | "legacy";
  exp_id?: string;
  dataset?: string;
  task_type?: string;
  task_label?: string;
  task_hint?: string;
  upload_tip?: string;
  weights: string;
  cfg: string;
  engine?: string;
  imgsz: number;
  epochs: number;
  precision: number;
  recall: number;
  f1: number;
  map50: number;
  map50_95: number;
  test_map50?: number | null;
  is_default: boolean;
};

export type DetectionModelsResponse = {
  models: DetectionModelInfo[];
  default: string | null;
};

export async function fetchDetectionModels(): Promise<DetectionModelsResponse> {
  const { data } = await api.get<DetectionModelsResponse>("/api/detection_models");
  return data;
}

export type CompareItem = {
  label: string;
  image_id: string;
  result: DiagnoseResponse;
};

export type CompareResponse = {
  mode: DiagnoseMode;
  items: CompareItem[];
  trend_summary: string;
};

export async function compareImages(
  imageIds: string[],
  mode: DiagnoseMode = "detection",
  labels?: string[],
): Promise<CompareResponse> {
  const { data } = await api.post<CompareResponse>("/api/compare", {
    image_ids: imageIds,
    mode,
    labels,
  });
  return data;
}

export function modeLabel(mode: DiagnoseMode): string {
  return MODE_OPTIONS.find((o) => o.value === mode)?.label ?? mode;
}

export type DsiHistoryPoint = { label: string; dsi: number };

export type DsiForecastResponse = {
  model: string;
  history: { label: string; day: number; dsi: number }[];
  forecast: { label: string; day: number; dsi: number; severity_level: string }[];
  slope_per_day: number;
  trend: string;
  risk_level: string;
  summary: string;
};

export async function predictDsi(history: DsiHistoryPoint[]): Promise<DsiForecastResponse> {
  const { data } = await api.post<DsiForecastResponse>("/api/predict_dsi", { history });
  return data;
}

export type GradCamResponse = {
  heatmap_base64: string;
  method: string;
  note: string;
};

export async function fetchGradCam(imageId: string): Promise<GradCamResponse> {
  const { data } = await api.post<GradCamResponse>("/api/gradcam", { image_id: imageId });
  return data;
}

export type DetectionVariantMetrics = {
  rank: number;
  key: string;
  label: string;
  exp_id: string;
  dataset: string;
  group: string;
  engine: string;
  recommend: string;
  improvement: string;
  epochs: number;
  map50: number;
  map50_95: number;
  test_map50?: number | null;
  test_score: number;
  precision: number;
  recall: number;
  f1: number;
  is_default?: boolean;
};

export type DetectionMetrics = {
  model_name: string;
  weights: string;
  dataset: string;
  engine: string;
  epochs: number;
  precision: number;
  recall: number;
  f1: number;
  map50: number;
  map50_95: number;
  test_map50?: number | null;
  params_m: number;
  inference_ms: number;
  variants: DetectionVariantMetrics[];
  ablation_chart: {
    experiments: string[];
    v2: (number | null)[];
    merged9: (number | null)[];
    test_v2: (number | null)[];
    test_merged9: (number | null)[];
  };
  test_ranking: {
    labels: string[];
    test_map50: number[];
    datasets: string[];
  };
  summary: {
    total: number;
    ablation: number;
    legacy: number;
    best_v2?: string | null;
    best_merged9?: string | null;
    best_v2_test?: number | null;
    best_merged9_test?: number | null;
    default_key?: string;
  };
};

export type ClassificationMetrics = {
  model_name: string;
  weights: string;
  dataset: string;
  epochs: number;
  precision: number;
  recall: number;
  f1: number;
  accuracy: number;
  params_m: number;
  inference_ms: number;
  per_class: { name: string; precision: number; recall: number; f1: number }[];
};

export type ModelMetricsBundle = {
  classification: ClassificationMetrics;
  detection: DetectionMetrics;
  segmentation: Record<string, unknown> & { precision: number; recall: number; f1: number };
};

export async function fetchModelMetrics(): Promise<ModelMetricsBundle> {
  const { data } = await api.get<ModelMetricsBundle>("/api/model_metrics");
  return data;
}

export type CloudReport = {
  id: string;
  mode: DiagnoseMode;
  image_id?: string;
  zone_id?: string;
  summary: string;
  result: DiagnoseResponse;
  source: string;
  created_at: string;
  share_path?: string;
};

export async function saveCloudReport(payload: {
  mode: DiagnoseMode;
  summary: string;
  result: DiagnoseResponse;
  image_id?: string;
  zone_id?: string;
  source?: string;
}): Promise<CloudReport> {
  const { data } = await api.post<{ report: CloudReport }>("/api/reports", payload);
  return data.report;
}

export async function fetchCloudReports(): Promise<CloudReport[]> {
  const { data } = await api.get<{ reports: CloudReport[] }>("/api/reports");
  return data.reports;
}

export async function fetchCloudReport(id: string): Promise<CloudReport> {
  const { data } = await api.get<{ report: CloudReport }>(`/api/reports/${id}`);
  return data.report;
}
