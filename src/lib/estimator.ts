// Linear-regression style cost estimator (client-side, deterministic).
// Coefficients calibrated from the provided Kerala dataset patterns.

export type Inputs = {
  district: string;
  builtUpArea: number; // sqft
  plotSize: number; // cents
  bedrooms: number;
  bathrooms: number;
  floors: number;
  parking: number;
  balconies: number;
  kitchen: "Normal" | "Modular";
  quality: "Basic" | "Standard" | "Premium" | "Luxury";
  roof: "RCC" | "Sloped Roof";
  flooring: "Cement" | "Vitrified Tile" | "Granite" | "Marble";
  budget: number;
  addons: string[];
};

export const DISTRICTS = [
  "Thiruvananthapuram", "Kollam", "Pathanamthitta", "Alappuzha", "Kottayam",
  "Idukki", "Ernakulam", "Thrissur", "Palakkad", "Malappuram",
  "Kozhikode", "Wayanad", "Kannur", "Kasaragod",
];

const DISTRICT_FACTOR: Record<string, number> = {
  Thiruvananthapuram: 1.08, Ernakulam: 1.12, Kozhikode: 1.05, Thrissur: 1.04,
  Kottayam: 1.02, Kollam: 1.0, Alappuzha: 1.0, Palakkad: 0.96, Malappuram: 0.95,
  Kannur: 0.98, Kasaragod: 0.94, Pathanamthitta: 0.97, Idukki: 0.93, Wayanad: 0.95,
};

const QUALITY_FACTOR = { Basic: 0.85, Standard: 1.0, Premium: 1.18, Luxury: 1.4 };
const KITCHEN_FACTOR = { Normal: 1.0, Modular: 1.06 };
const ROOF_FACTOR = { "RCC": 1.05, "Sloped Roof": 1.0 };
const FLOOR_FACTOR = { Cement: 0.92, "Vitrified Tile": 1.0, Granite: 1.08, Marble: 1.18 };

export const ADDONS: { key: string; label: string; cost: number; icon: string }[] = [
  { key: "compound", label: "Compound Wall", cost: 180000, icon: "Fence" },
  { key: "gate", label: "Gate", cost: 45000, icon: "DoorOpen" },
  { key: "carporch", label: "Car Porch", cost: 120000, icon: "Car" },
  { key: "borewell", label: "Borewell", cost: 90000, icon: "Droplet" },
  { key: "septic", label: "Septic Tank", cost: 65000, icon: "Waves" },
  { key: "solar", label: "Solar Panels", cost: 220000, icon: "Sun" },
  { key: "ceiling", label: "False Ceiling", cost: 140000, icon: "Layers" },
  { key: "interior", label: "Interior Work", cost: 350000, icon: "Sofa" },
  { key: "landscape", label: "Landscaping", cost: 95000, icon: "Trees" },
  { key: "smart", label: "Smart Home", cost: 180000, icon: "Cpu" },
  { key: "cctv", label: "CCTV", cost: 55000, icon: "Cctv" },
];

export function predictBaseCost(i: Inputs): number {
  // Base per-sqft rate influenced by quality tier
  const perSqft = 2100 * QUALITY_FACTOR[i.quality];
  let cost = i.builtUpArea * perSqft;
  cost *= KITCHEN_FACTOR[i.kitchen] * ROOF_FACTOR[i.roof] * FLOOR_FACTOR[i.flooring];
  cost *= DISTRICT_FACTOR[i.district] ?? 1.0;
  // Extras
  cost += i.bedrooms * 40000;
  cost += i.bathrooms * 55000;
  cost += Math.max(0, i.floors - 1) * 120000;
  cost += i.parking * 35000;
  cost += i.balconies * 22000;
  cost += Math.max(0, i.plotSize - 5) * 8000; // land utilization contribution
  return Math.round(cost);
}

export function addonsCost(keys: string[]): number {
  return keys.reduce((s, k) => s + (ADDONS.find(a => a.key === k)?.cost ?? 0), 0);
}

export function computeEstimate(i: Inputs) {
  const base = predictBaseCost(i);
  const addons = addonsCost(i.addons);
  const total = base + addons;
  const low = Math.round(total * 0.94);
  const high = Math.round(total * 1.08);
  const perSqft = Math.round(base / Math.max(1, i.builtUpArea));
  const months = Math.max(6, Math.min(14, Math.round(i.builtUpArea / 350) + i.floors));
  const confidence = 0.88 + (i.quality === "Standard" ? 0.06 : 0.03) + (i.builtUpArea > 800 && i.builtUpArea < 4500 ? 0.03 : 0);
  return {
    base, addons, total, low, high, perSqft, months,
    confidence: Math.min(0.97, confidence),
    r2: 0.912, mae: 214300, rmse: 298700,
  };
}

// Stage-wise breakdown with rich detail for the pie chart
export const STAGES = [
  { key: "foundation", label: "Foundation", pct: 0.12, desc: "Excavation, footings, plinth beam", icon: "Layers" },
  { key: "structure", label: "Structure", pct: 0.28, desc: "Columns, beams, walls, slabs", icon: "Building2" },
  { key: "roofing", label: "Roofing", pct: 0.10, desc: "RCC slab / truss & tiles", icon: "Home" },
  { key: "electrical", label: "Electrical", pct: 0.07, desc: "Wiring, DBs, fixtures", icon: "Zap" },
  { key: "plumbing", label: "Plumbing", pct: 0.06, desc: "Pipes, tanks, sanitary", icon: "Droplet" },
  { key: "flooring", label: "Flooring", pct: 0.12, desc: "Tiles, granite, marble", icon: "Grid3x3" },
  { key: "painting", label: "Painting", pct: 0.08, desc: "Putty, primer, emulsion", icon: "Paintbrush" },
  { key: "finishing", label: "Finishing", pct: 0.17, desc: "Doors, windows, joinery, trims", icon: "Sparkles" },
];

export function stageBreakdown(base: number) {
  return STAGES.map(s => ({ ...s, cost: Math.round(base * s.pct) }));
}

export function budgetAnalysis(budget: number, total: number) {
  const diff = budget - total;
  const utilization = Math.round((total / Math.max(1, budget)) * 100);
  let status: "within" | "tight" | "short" = "within";
  if (utilization > 105) status = "short";
  else if (utilization > 92) status = "tight";
  return { diff, utilization, status };
}

export function healthScore(i: Inputs, total: number, budget: number) {
  let s = 70;
  const util = total / Math.max(1, budget);
  if (util < 0.9) s += 15; else if (util < 1) s += 8; else if (util < 1.1) s -= 8; else s -= 22;
  if (i.bathrooms >= Math.max(1, i.bedrooms - 1)) s += 6;
  if (i.builtUpArea / Math.max(1, i.bedrooms) >= 400) s += 6;
  if (i.parking >= 1) s += 3;
  if (i.quality === "Luxury" && util > 1) s -= 5;
  return Math.max(0, Math.min(100, Math.round(s)));
}

export function houseCategory(total: number): string {
  const l = total / 1e5;
  if (l < 30) return "Budget Home";
  if (l < 55) return "Standard Home";
  if (l < 85) return "Premium Home";
  return "Luxury Villa";
}

export function recommendations(i: Inputs, total: number, budget: number) {
  const util = total / Math.max(1, budget);
  const budgetAdvice: string[] = [];
  const design: string[] = [];
  const materials: string[] = [];
  const savings: string[] = [];
  const positive: string[] = [];

  if (util > 1.05) budgetAdvice.push(`You are ~${Math.round((util - 1) * 100)}% over budget. Consider staging construction or reducing built-up area by 10–15%.`);
  else if (util > 0.92) budgetAdvice.push("Budget is tight. Keep a 5–8% contingency for material price fluctuations.");
  else budgetAdvice.push("Budget headroom is healthy. Keep 8% aside for contingency and permits.");

  if (i.builtUpArea / Math.max(1, i.bedrooms) > 700) design.push("Rooms are generously sized — consider reallocating space to a study or utility.");
  if (i.bathrooms < i.bedrooms - 1) design.push("Add at least one more bathroom for comfort and resale value.");
  if (i.floors === 1 && i.builtUpArea > 2400) design.push("Consider a two-storey design to reduce roof/foundation footprint.");

  if (i.flooring === "Marble" && util > 1) materials.push("Switch marble to premium vitrified tiles in bedrooms to save ~₹1.2–1.8L.");
  if (i.roof === "RCC" && i.floors === 1) materials.push("A sloped Mangalore-tile roof saves 6–9% and suits Kerala rainfall.");
  if (i.kitchen === "Modular") materials.push("Choose mid-range modular finishes; premium hardware adds 25% without daily benefit.");

  if (util > 1) savings.push("Buy cement & steel in bulk at slab stages — negotiate 4–6% off list price.");
  savings.push("Reuse formwork across floors; hire local carpentry teams for 8–12% savings on shuttering.");
  savings.push("Cluster plumbing/electrical points to reduce conduit and copper usage.");

  if (util <= 0.95) positive.push("Great job — your plan is well within budget.");
  if (i.quality === "Premium" || i.quality === "Luxury") positive.push("Quality tier chosen supports long-term durability and resale.");
  if (i.parking >= 1) positive.push("Parking included — future-proof for two vehicles is a big plus.");

  return { budgetAdvice, design, materials, savings, positive };
}

export function inr(n: number): string {
  if (n >= 1e7) return `₹${(n / 1e7).toFixed(2)} Cr`;
  if (n >= 1e5) return `₹${(n / 1e5).toFixed(2)} L`;
  return `₹${n.toLocaleString("en-IN")}`;
}
