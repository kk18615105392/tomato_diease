/** 番茄典型叶片病害 — 各省集中分布 Mock 数据（后续对接 /api/map_stats） */

export type ProvinceStat = { name: string; value: number };

export type HotSpot = { name: string; value: [number, number, number] };

export type DiseaseMapProfile = {
  id: string;
  name: string;
  alias: string;
  /** 地理集中特征描述 */
  clusterDesc: string;
  /** 视觉映射色阶（低→高） */
  colorScale: string[];
  emphasisColor: string;
  scatterColor: string;
  provinces: ProvinceStat[];
  hotSpots: HotSpot[];
};

const ALL_PROVINCES = [
  "北京市", "天津市", "河北省", "山西省", "内蒙古自治区",
  "辽宁省", "吉林省", "黑龙江省", "上海市", "江苏省",
  "浙江省", "安徽省", "福建省", "江西省", "山东省",
  "河南省", "湖北省", "湖南省", "广东省", "广西壮族自治区",
  "海南省", "重庆市", "四川省", "贵州省", "云南省",
  "西藏自治区", "陕西省", "甘肃省", "青海省", "宁夏回族自治区",
  "新疆维吾尔自治区", "台湾省", "香港特别行政区", "澳门特别行政区",
];

/** 构建稀疏分布：仅指定省份有较高值，其余接近 0，体现「集中暴发」 */
function buildClustered(
  hotspots: Record<string, number>,
  base = 0,
): ProvinceStat[] {
  return ALL_PROVINCES.map((name) => ({
    name,
    value: hotspots[name] ?? base,
  }));
}

export const DISEASE_MAP_PROFILES: DiseaseMapProfile[] = [
  {
    id: "early_blight",
    name: "早疫病",
    alias: "Alternaria solani",
    clusterDesc: "集中分布于华北、华东设施番茄主产区，高湿密植田块易发",
    colorScale: ["#fef2f2", "#fecaca", "#f87171", "#dc2626", "#991b1b"],
    emphasisColor: "#dc2626",
    scatterColor: "#ef4444",
    provinces: buildClustered({
      山东省: 920,
      河北省: 780,
      辽宁省: 620,
      江苏省: 540,
      河南省: 480,
      安徽省: 320,
      北京市: 180,
      天津市: 160,
      山西省: 120,
    }),
    hotSpots: [
      { name: "寿光", value: [118.74, 36.86, 920] },
      { name: "邯郸", value: [114.54, 36.63, 780] },
      { name: "沈阳", value: [123.43, 41.80, 620] },
      { name: "徐州", value: [117.28, 34.20, 540] },
    ],
  },
  {
    id: "late_blight",
    name: "晚疫病",
    alias: "Phytophthora infestans",
    clusterDesc: "西南、华南高湿冷凉区域集中，雨季露地栽培风险高",
    colorScale: ["#fff7ed", "#fed7aa", "#fb923c", "#ea580c", "#9a3412"],
    emphasisColor: "#ea580c",
    scatterColor: "#f97316",
    provinces: buildClustered({
      云南省: 860,
      四川省: 740,
      贵州省: 580,
      重庆市: 520,
      广东省: 460,
      广西壮族自治区: 420,
      湖南省: 380,
      湖北省: 280,
      福建省: 240,
    }),
    hotSpots: [
      { name: "昆明", value: [102.71, 25.04, 860] },
      { name: "成都", value: [104.07, 30.67, 740] },
      { name: "贵阳", value: [106.63, 26.65, 580] },
      { name: "广州", value: [113.26, 23.13, 460] },
    ],
  },
  {
    id: "leaf_mold",
    name: "叶霉病",
    alias: "Fulvia fulva",
    clusterDesc: "北方日光温室集中区高发，通风不良时快速蔓延",
    colorScale: ["#faf5ff", "#e9d5ff", "#c084fc", "#9333ea", "#581c87"],
    emphasisColor: "#9333ea",
    scatterColor: "#a855f7",
    provinces: buildClustered({
      山东省: 880,
      河北省: 720,
      辽宁省: 650,
      江苏省: 490,
      北京市: 380,
      天津市: 340,
      河南省: 290,
      安徽省: 220,
    }),
    hotSpots: [
      { name: "寿光", value: [118.74, 36.86, 880] },
      { name: "唐山", value: [118.18, 39.63, 720] },
      { name: "大连", value: [121.61, 38.91, 650] },
      { name: "连云港", value: [119.22, 34.60, 490] },
    ],
  },
  {
    id: "gray_mold",
    name: "灰霉病",
    alias: "Botrytis cinerea",
    clusterDesc: "长三角、环渤海设施农业区集中，低温高湿期易流行",
    colorScale: ["#f8fafc", "#cbd5e1", "#94a3b8", "#64748b", "#334155"],
    emphasisColor: "#64748b",
    scatterColor: "#475569",
    provinces: buildClustered({
      江苏省: 760,
      浙江省: 680,
      山东省: 620,
      上海市: 540,
      安徽省: 420,
      河北省: 360,
      辽宁省: 280,
      湖北省: 200,
    }),
    hotSpots: [
      { name: "南京", value: [118.80, 32.06, 760] },
      { name: "杭州", value: [120.15, 30.28, 680] },
      { name: "潍坊", value: [119.16, 36.71, 620] },
      { name: "上海", value: [121.47, 31.23, 540] },
    ],
  },
  {
    id: "powdery_mildew",
    name: "白粉病",
    alias: "Leveillula taurica",
    clusterDesc: "西北干燥区及华北露地番茄田块集中发生，昼夜温差大时加重",
    colorScale: ["#fefce8", "#fef08a", "#facc15", "#ca8a04", "#854d0e"],
    emphasisColor: "#ca8a04",
    scatterColor: "#eab308",
    provinces: buildClustered({
      新疆维吾尔自治区: 820,
      甘肃省: 680,
      宁夏回族自治区: 560,
      内蒙古自治区: 480,
      河北省: 420,
      山西省: 360,
      陕西省: 300,
      山东省: 240,
    }),
    hotSpots: [
      { name: "乌鲁木齐", value: [87.62, 43.82, 820] },
      { name: "兰州", value: [103.83, 36.06, 680] },
      { name: "银川", value: [106.23, 38.49, 560] },
      { name: "呼和浩特", value: [111.75, 40.84, 480] },
    ],
  },
  {
    id: "tylcv",
    name: "黄化曲叶病毒病",
    alias: "TYLCV",
    clusterDesc: "华南、华东迁飞带区集中，烟粉虱传播导致区域性暴发",
    colorScale: ["#fffbeb", "#fde68a", "#fbbf24", "#d97706", "#92400e"],
    emphasisColor: "#d97706",
    scatterColor: "#f59e0b",
    provinces: buildClustered({
      广东省: 900,
      福建省: 720,
      广西壮族自治区: 640,
      海南省: 580,
      浙江省: 520,
      江苏省: 460,
      山东省: 380,
      云南省: 320,
      江西省: 260,
    }),
    hotSpots: [
      { name: "广州", value: [113.26, 23.13, 900] },
      { name: "漳州", value: [117.65, 24.51, 720] },
      { name: "南宁", value: [108.37, 22.82, 640] },
      { name: "海口", value: [110.35, 20.02, 580] },
    ],
  },
  {
    id: "bacterial_spot",
    name: "细菌性斑点病",
    alias: "Xanthomonas spp.",
    clusterDesc: "长江流域及华南多雨区集中，台风暴雨后田间扩散明显",
    colorScale: ["#ecfeff", "#a5f3fc", "#22d3ee", "#0891b2", "#164e63"],
    emphasisColor: "#0891b2",
    scatterColor: "#06b6d4",
    provinces: buildClustered({
      湖北省: 780,
      湖南省: 700,
      江西省: 620,
      安徽省: 540,
      江苏省: 480,
      浙江省: 420,
      广东省: 380,
      四川省: 300,
      重庆市: 260,
    }),
    hotSpots: [
      { name: "武汉", value: [114.31, 30.52, 780] },
      { name: "长沙", value: [112.94, 28.23, 700] },
      { name: "南昌", value: [115.89, 28.68, 620] },
      { name: "合肥", value: [117.28, 31.86, 540] },
    ],
  },
  {
    id: "septoria",
    name: "斑枯病",
    alias: "Septoria lycopersici",
    clusterDesc: "东北、华北春播番茄区集中，连作地块发病指数偏高",
    colorScale: ["#f0fdf4", "#bbf7d0", "#4ade80", "#16a34a", "#14532d"],
    emphasisColor: "#16a34a",
    scatterColor: "#22c55e",
    provinces: buildClustered({
      黑龙江省: 840,
      吉林省: 760,
      辽宁省: 680,
      河北省: 520,
      山东省: 460,
      内蒙古自治区: 380,
      山西省: 300,
      北京市: 220,
    }),
    hotSpots: [
      { name: "哈尔滨", value: [126.53, 45.80, 840] },
      { name: "长春", value: [125.32, 43.82, 760] },
      { name: "沈阳", value: [123.43, 41.80, 680] },
      { name: "张家口", value: [114.88, 40.82, 520] },
    ],
  },
];

export function getDiseaseProfile(id: string): DiseaseMapProfile {
  return DISEASE_MAP_PROFILES.find((d) => d.id === id) ?? DISEASE_MAP_PROFILES[0];
}

export function getTopProvinces(profile: DiseaseMapProfile, limit = 8): ProvinceStat[] {
  return [...profile.provinces]
    .filter((p) => p.value > 0)
    .sort((a, b) => b.value - a.value)
    .slice(0, limit);
}

export function getMaxValue(profile: DiseaseMapProfile): number {
  return Math.max(...profile.provinces.map((p) => p.value), 1);
}

export function getTotalCases(profile: DiseaseMapProfile): number {
  return profile.provinces.reduce((sum, p) => sum + p.value, 0);
}

export function getAffectedProvinceCount(profile: DiseaseMapProfile): number {
  return profile.provinces.filter((p) => p.value > 0).length;
}
