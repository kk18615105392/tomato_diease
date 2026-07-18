/** 番茄典型叶片病害百科（与地图分图层数据对应） */

export type DiseaseWikiEntry = {
  id: string;
  name: string;
  pathogen: string;
  category: string;
  symptoms: string[];
  conditions: string;
  prevention: string[];
  pesticides: string[];
  severity: "低" | "中" | "高";
};

export const DISEASE_WIKI: DiseaseWikiEntry[] = [
  {
    id: "early_blight",
    name: "早疫病",
    pathogen: "Alternaria solani",
    category: "真菌性病害",
    symptoms: [
      "叶片出现同心轮纹状褐色病斑，似靶心状",
      "病斑周围常有黄色晕圈",
      "茎部出现黑褐色椭圆形条斑，易折断",
      "果实脐部或肩部出现黑腐",
    ],
    conditions: "温度 25～30℃、相对湿度 80% 以上，密植通风不良时暴发",
    prevention: [
      "选用抗病品种，避免连作",
      "及时摘除下部老叶、病叶",
      "控制氮肥，增施磷钾肥",
      "设施栽培加强通风降湿",
    ],
    pesticides: ["百菌清 600～800 倍液", "代森锰锌 500 倍液", "嘧菌酯 1500 倍液"],
    severity: "高",
  },
  {
    id: "late_blight",
    name: "晚疫病",
    pathogen: "Phytophthora infestans",
    category: "卵菌性病害",
    symptoms: [
      "叶片边缘或叶尖出现水渍状暗绿色大斑",
      "湿度大时病斑背面有白色霉层",
      "茎部呈黑褐色缢缩，植株迅速萎蔫",
      "果实出现褐色硬斑",
    ],
    conditions: "低温高湿（18～22℃），连续阴雨或露水重时流行",
    prevention: [
      "避免低温高湿环境",
      "雨前雨后预防性喷药",
      "发现中心病株立即拔除",
      "合理密植，改善田间通风",
    ],
    pesticides: ["烯酰吗啉 1000 倍液", "霜脲氰 600 倍液", "氟吡菌胺 1500 倍液"],
    severity: "高",
  },
  {
    id: "leaf_mold",
    name: "叶霉病",
    pathogen: "Fulvia fulva",
    category: "真菌性病害",
    symptoms: [
      "叶片正面出现淡黄色褪绿斑",
      "叶背产生灰紫色至黑色霉层",
      "严重时叶片卷曲、干枯",
      "主要危害中上部叶片",
    ],
    conditions: "温室大棚高温高湿（23～27℃、RH>85%），通风不良",
    prevention: [
      "加大通风量，降低棚内湿度",
      "避免叶面结露时间过长",
      "及时整枝打杈",
      "轮换使用不同作用机理药剂",
    ],
    pesticides: ["多抗霉素 300 倍液", "嘧菌酯 1500 倍液", "苯醚甲环唑 2000 倍液"],
    severity: "中",
  },
  {
    id: "gray_mold",
    name: "灰霉病",
    pathogen: "Botrytis cinerea",
    category: "真菌性病害",
    symptoms: [
      "花、果、叶均可受害，出现水渍状软腐",
      "病部产生灰褐色绒毛状霉层",
      "果实从蒂部或伤口侵入，呈灰白色软腐",
      "低温高湿下扩展极快",
    ],
    conditions: "温度 20～23℃、高湿、伤口多、通风差",
    prevention: [
      "减少机械损伤，及时摘除病残体",
      "控制浇水量，避免结露",
      "加强温湿度管理",
      "花期和幼果期重点防护",
    ],
    pesticides: ["腐霉利 800 倍液", "异菌脲 1000 倍液", "咯菌腈 1500 倍液"],
    severity: "高",
  },
  {
    id: "powdery_mildew",
    name: "白粉病",
    pathogen: "Leveillula taurica",
    category: "真菌性病害",
    symptoms: [
      "叶片表面出现白色粉状霉层",
      "严重时叶片变黄、卷曲、早枯",
      "多从下部叶片向上扩展",
      "干燥条件下仍可发生",
    ],
    conditions: "温度 22～30℃，干湿交替，氮肥过多时加重",
    prevention: [
      "合理施肥，避免徒长",
      "及时清除病叶",
      "注意通风透光",
      "避免偏施氮肥",
    ],
    pesticides: ["三唑酮 1000 倍液", "乙嘧酚 800 倍液", "氟硅唑 2000 倍液"],
    severity: "中",
  },
  {
    id: "tylcv",
    name: "黄化曲叶病毒病",
    pathogen: "Tomato yellow leaf curl virus (TYLCV)",
    category: "病毒性病害",
    symptoms: [
      "新叶黄化、皱缩、卷曲、变小",
      "植株矮化，节间缩短",
      "花器发育不良，座果率极低",
      "由烟粉虱持久传播",
    ],
    conditions: "高温干旱、烟粉虱种群数量大时暴发",
    prevention: [
      "悬挂黄板监测和诱杀烟粉虱",
      "选用抗病毒品种",
      "防虫网阻隔传毒媒介",
      "发现病株立即拔除销毁",
    ],
    pesticides: ["噻虫嗪 3000 倍液（治虫）", "吡虫啉 2000 倍液", "啶虫脒 1500 倍液"],
    severity: "高",
  },
  {
    id: "bacterial_spot",
    name: "细菌性斑点病",
    pathogen: "Xanthomonas spp.",
    category: "细菌性病害",
    symptoms: [
      "叶片出现褐色至黑色角斑，周围有黄色晕",
      "病斑可穿孔、破裂",
      "果实出现圆形隆起斑，中心木栓化",
      "暴雨后快速扩展",
    ],
    conditions: "高温高湿（25～30℃），风雨传播",
    prevention: [
      "种子消毒，使用无病苗",
      "避免大水漫灌",
      "台风暴雨后及时喷药保护",
      "田间操作避免造成伤口",
    ],
    pesticides: ["春雷霉素 600 倍液", "氢氧化铜 800 倍液", "噻菌铜 500 倍液"],
    severity: "中",
  },
  {
    id: "septoria",
    name: "斑枯病",
    pathogen: "Septoria lycopersici",
    category: "真菌性病害",
    symptoms: [
      "叶片出现圆形小斑点，中央灰白色",
      "斑点边缘深褐色，具黑色小点（分生孢子器）",
      "从下部叶片向上发展",
      "连作地块发病重",
    ],
    conditions: "温度 22～26℃，高湿，连作 3 年以上加重",
    prevention: [
      "实行轮作，避免连作",
      "清除田间病残体",
      "加强通风，降低湿度",
      "增施有机肥提高抗病性",
    ],
    pesticides: ["苯醚甲环唑 2000 倍液", "代森锰锌 500 倍液", "百菌清 600 倍液"],
    severity: "中",
  },
];

export function getWikiById(id: string) {
  return DISEASE_WIKI.find((d) => d.id === id);
}

export function getWikiByName(name: string) {
  return DISEASE_WIKI.find((d) => d.name === name || name.includes(d.name));
}

/** 按月份返回当前高发病害预警 */
export function getSeasonalRiskAlerts(): { level: "warning" | "danger"; disease: string; message: string }[] {
  const month = new Date().getMonth() + 1;
  const alerts: { level: "warning" | "danger"; disease: string; message: string }[] = [];

  if ([3, 4, 5].includes(month)) {
    alerts.push({ level: "warning", disease: "早疫病", message: "春播期温湿度波动大，华北设施区早疫病进入易发窗口" });
    alerts.push({ level: "warning", disease: "斑枯病", message: "东北春播番茄区斑枯病风险上升，建议预防性用药" });
  }
  if ([6, 7, 8].includes(month)) {
    alerts.push({ level: "danger", disease: "黄化曲叶病毒病", message: "夏季高温期烟粉虱活跃，华南 TYLCV 传播风险极高" });
    alerts.push({ level: "warning", disease: "细菌性斑点病", message: "梅雨/台风季注意长江流域细菌性斑点病暴发" });
  }
  if ([9, 10].includes(month)) {
    alerts.push({ level: "warning", disease: "晚疫病", message: "秋季昼夜温差大，西南露地番茄晚疫病需重点防控" });
    alerts.push({ level: "warning", disease: "叶霉病", message: "北方温室通风减少，叶霉病高发期来临" });
  }
  if ([11, 12, 1, 2].includes(month)) {
    alerts.push({ level: "warning", disease: "灰霉病", message: "冬季设施低温高湿，灰霉病和花腐风险增加" });
    alerts.push({ level: "warning", disease: "白粉病", message: "西北干燥温室注意白粉病监测" });
  }
  return alerts;
}
