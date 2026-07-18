/** 标准健康叶 / 典型病斑参考图（SVG 生成） */

function svgDataUrl(svg: string) {
  return `data:image/svg+xml;base64,${btoa(unescape(encodeURIComponent(svg)))}`;
}

function leafSvg(fill: string, spots: string, label: string) {
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 140">
    <rect width="200" height="140" fill="#f0fdf4"/>
    <text x="100" y="16" text-anchor="middle" font-size="11" fill="#166534" font-family="sans-serif">${label}</text>
    <path d="M100 30 C60 35,40 70,45 100 C50 120,75 128,100 125 C125 128,150 120,155 100 C160 70,140 35,100 30Z" fill="${fill}" stroke="#16a34a" stroke-width="2"/>
    ${spots}
  </svg>`;
}

export type ReferenceLeaf = {
  id: string;
  name: string;
  type: "healthy" | "disease";
  description: string;
  imageUrl: string;
};

export const REFERENCE_LEAVES: ReferenceLeaf[] = [
  {
    id: "healthy",
    name: "健康叶片",
    type: "healthy",
    description: "叶色浓绿、无病斑、边缘完整、叶脉清晰",
    imageUrl: svgDataUrl(leafSvg("#22c55e", "", "标准健康叶")),
  },
  {
    id: "early_blight",
    name: "早疫病典型",
    type: "disease",
    description: "同心轮纹褐色病斑，周围黄色晕圈",
    imageUrl: svgDataUrl(
      leafSvg(
        "#86efac",
        `<circle cx="85" cy="75" r="18" fill="none" stroke="#92400e" stroke-width="3"/><circle cx="85" cy="75" r="12" fill="none" stroke="#78350f" stroke-width="2"/><circle cx="85" cy="75" r="6" fill="#451a03"/>`,
        "早疫病典型病斑",
      ),
    ),
  },
  {
    id: "late_blight",
    name: "晚疫病典型",
    type: "disease",
    description: "水渍状暗绿色大斑，边缘不规则",
    imageUrl: svgDataUrl(
      leafSvg(
        "#86efac",
        `<ellipse cx="110" cy="80" rx="30" ry="22" fill="rgba(21,128,61,0.4)" stroke="#14532d" stroke-width="2"/>`,
        "晚疫病典型病斑",
      ),
    ),
  },
  {
    id: "leaf_mold",
    name: "叶霉病典型",
    type: "disease",
    description: "叶背灰紫色霉层，正面黄化斑",
    imageUrl: svgDataUrl(
      leafSvg(
        "#bbf7d0",
        `<ellipse cx="95" cy="70" rx="25" ry="18" fill="rgba(147,51,234,0.35)"/><ellipse cx="105" cy="85" rx="15" ry="10" fill="rgba(126,34,206,0.3)"/>`,
        "叶霉病典型",
      ),
    ),
  },
  {
    id: "powdery",
    name: "白粉病典型",
    type: "disease",
    description: "叶面白色粉状霉层",
    imageUrl: svgDataUrl(
      leafSvg(
        "#86efac",
        `<ellipse cx="100" cy="75" rx="28" ry="20" fill="rgba(255,255,255,0.7)" stroke="#d1d5db" stroke-width="1"/>`,
        "白粉病典型",
      ),
    ),
  },
];
