export type GreenhouseZone = {
  id: string;
  code: string;
  name: string;
  area: string;
  crop: string;
  createdAt: string;
};

const ZONES_KEY = "tomato_ai_zones";
const SELECTED_ZONE_KEY = "tomato_ai_selected_zone";

const DEFAULT_ZONES: GreenhouseZone[] = [
  { id: "z1", code: "A-01", name: "1号日光温室", area: "北区", crop: "樱桃番茄", createdAt: new Date().toISOString() },
  { id: "z2", code: "A-02", name: "2号日光温室", area: "北区", crop: "粉果番茄", createdAt: new Date().toISOString() },
  { id: "z3", code: "B-01", name: "3号连栋大棚", area: "南区", crop: "硬果番茄", createdAt: new Date().toISOString() },
];

export function getZones(): GreenhouseZone[] {
  try {
    const raw = localStorage.getItem(ZONES_KEY);
    if (raw) return JSON.parse(raw) as GreenhouseZone[];
    localStorage.setItem(ZONES_KEY, JSON.stringify(DEFAULT_ZONES));
    return DEFAULT_ZONES;
  } catch {
    return DEFAULT_ZONES;
  }
}

export function saveZones(zones: GreenhouseZone[]) {
  localStorage.setItem(ZONES_KEY, JSON.stringify(zones));
}

export function addZone(zone: Omit<GreenhouseZone, "id" | "createdAt">): GreenhouseZone {
  const newZone: GreenhouseZone = {
    ...zone,
    id: crypto.randomUUID(),
    createdAt: new Date().toISOString(),
  };
  const zones = [...getZones(), newZone];
  saveZones(zones);
  return newZone;
}

export function deleteZone(id: string) {
  saveZones(getZones().filter((z) => z.id !== id));
}

export function getSelectedZoneId(): string {
  return localStorage.getItem(SELECTED_ZONE_KEY) ?? getZones()[0]?.id ?? "";
}

export function setSelectedZoneId(id: string) {
  localStorage.setItem(SELECTED_ZONE_KEY, id);
}

export function getZoneById(id: string): GreenhouseZone | undefined {
  return getZones().find((z) => z.id === id);
}

export function getZoneLabel(id?: string): string {
  if (!id) return "未分区";
  const z = getZoneById(id);
  return z ? `${z.code} · ${z.name}` : "未知分区";
}
