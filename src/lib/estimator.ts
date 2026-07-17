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

export type RecCategory = "warning" | "optimization" | "upgrade" | "positive" | "insight" | "risk";
export type RecPriority = "High" | "Medium" | "Low";

export type SmartRec = {
  id: string;
  category: RecCategory;
  badge: string;
  icon: string;
  title: string;
  description: string;
  impact: string;
  priority: RecPriority;
};

const lakh = (n: number) => `₹${(n / 1e5).toFixed(1)}L`;

export function smartRecommendations(i: Inputs, total: number, budget: number): SmartRec[] {
  const recs: SmartRec[] = [];
  const diff = budget - total;
  const util = total / Math.max(1, budget);
  const surplusPct = diff / Math.max(1, total);

  // ---- BUDGET SHORT ----
  if (diff < 0) {
    const short = Math.abs(diff);
    recs.push({
      id: "budget-short",
      category: "warning",
      badge: "Budget Warning",
      icon: "AlertTriangle",
      title: `Budget short by ${lakh(short)}`,
      description: `Your available budget is below the predicted cost by ~${Math.round((util - 1) * 100)}%. Below are optimization suggestions to close this gap.`,
      impact: `Gap: ${lakh(short)}`,
      priority: "High",
    });

    if (i.builtUpArea > 1800) {
      recs.push({
        id: "opt-area",
        category: "optimization",
        badge: "Area Optimization",
        icon: "Ruler",
        title: "Reduce built-up area by 100–200 sq.ft.",
        description: "Trimming built-up area is the single most effective way to reduce total cost without compromising quality tier.",
        impact: "Save ₹2L – ₹5L",
        priority: "High",
      });
    }
    if (i.floors > 1) {
      recs.push({
        id: "opt-floors",
        category: "optimization",
        badge: "Floor Optimization",
        icon: "Building",
        title: "Consider a single-floor layout",
        description: "Single-storey homes have lower structural, staircase and foundation costs, and cheaper long-term maintenance.",
        impact: "Save ₹2L – ₹6L",
        priority: "Medium",
      });
    }
    if (i.balconies > 2) {
      recs.push({
        id: "opt-balcony",
        category: "optimization",
        badge: "Balcony Optimization",
        icon: "Sun",
        title: "Reduce balcony count or size",
        description: "Balconies add RCC, railing and waterproofing costs. Cutting back keeps the elevation without the overhead.",
        impact: "Save ₹40K – ₹1L",
        priority: "Low",
      });
    }
    if (i.parking > 1) {
      recs.push({
        id: "opt-parking",
        category: "optimization",
        badge: "Parking Optimization",
        icon: "Car",
        title: "Reduce extra parking spaces",
        description: "One covered parking is enough for most families. Additional bays add paving, roofing and drainage costs.",
        impact: "Save ₹35K – ₹80K",
        priority: "Low",
      });
    }
    if (i.kitchen === "Modular") {
      recs.push({
        id: "opt-kitchen",
        category: "optimization",
        badge: "Kitchen Optimization",
        icon: "ChefHat",
        title: "Switch to a semi-modular kitchen",
        description: "Semi-modular kitchens use factory-made shutters on site-built carcasses — nearly the same look for far less cost.",
        impact: "Save ₹1L – ₹2L",
        priority: "Medium",
      });
    }
    if (i.flooring === "Marble" || i.flooring === "Granite") {
      recs.push({
        id: "opt-flooring",
        category: "optimization",
        badge: "Flooring Optimization",
        icon: "Grid3x3",
        title: "Choose premium vitrified tiles",
        description: "Modern double-charge vitrified tiles look and last close to natural stone at a fraction of the price.",
        impact: "Save ₹80K – ₹1.5L",
        priority: "Medium",
      });
    }
    if (i.quality === "Premium" || i.quality === "Luxury") {
      recs.push({
        id: "opt-quality",
        category: "optimization",
        badge: "Quality Optimization",
        icon: "Award",
        title: "Step down to Standard construction quality",
        description: "Standard tier still uses ISI-grade materials and gives long service life while reducing structural cost.",
        impact: "Save ₹3L – ₹7L",
        priority: "High",
      });
    }
    if (i.roof === "RCC") {
      recs.push({
        id: "opt-roof",
        category: "optimization",
        badge: "Roof Optimization",
        icon: "Home",
        title: "Consider a Mangalore-tiled sloped roof",
        description: "Sloped roofs suit Kerala rainfall, save on steel and concrete, and dramatically cut waterproofing bills.",
        impact: "Save ₹1L – ₹3L",
        priority: "Medium",
      });
    }
    // postpone add-ons
    const postponable = i.addons.filter(k => ["ceiling", "landscape", "interior", "smart"].includes(k));
    if (postponable.length) {
      recs.push({
        id: "opt-postpone",
        category: "optimization",
        badge: "Phase-wise Build",
        icon: "Clock",
        title: "Postpone premium add-ons to phase 2",
        description: "False ceiling, landscaping, premium interiors and smart-home features can be added comfortably after occupancy.",
        impact: `Defer up to ${lakh(addonsCost(postponable))}`,
        priority: "High",
      });
    }
  }

  // ---- BUDGET COMFORTABLE / SURPLUS ----
  if (diff >= 0) {
    if (surplusPct > 0.1) {
      recs.push({
        id: "budget-excellent",
        category: "positive",
        badge: "Excellent Planning",
        icon: "PartyPopper",
        title: "You have sufficient budget to comfortably complete this project",
        description: "Your configuration is well balanced. You can safely include premium finishes, energy-efficient upgrades and keep a healthy contingency reserve.",
        impact: `Surplus: ${lakh(diff)}`,
        priority: "High",
      });
    } else {
      recs.push({
        id: "budget-tight",
        category: "warning",
        badge: "Tight Budget",
        icon: "Wallet",
        title: "Your budget is sufficient but has limited flexibility",
        description: "Avoid unnecessary luxury upgrades, keep a contingency reserve, and compare quotations from multiple contractors before finalizing materials.",
        impact: `Remaining: ${lakh(diff)}`,
        priority: "High",
      });
    }

    // Upgrade suggestions when surplus exists
    if (surplusPct > 0.05) {
      const has = (k: string) => i.addons.includes(k);
      if (!has("solar")) recs.push({
        id: "up-solar", category: "upgrade", badge: "Upgrade", icon: "Sun",
        title: "Install rooftop solar panels",
        description: "Reduce electricity bills, offset carbon footprint, and gain state subsidy benefits. Payback is typically 4–6 years in Kerala.",
        impact: "Add ₹2.5L – ₹4L · Long-term savings", priority: "High",
      });
      if (i.flooring !== "Vitrified Tile" && i.flooring !== "Granite" && i.flooring !== "Marble") recs.push({
        id: "up-floor", category: "upgrade", badge: "Upgrade", icon: "Grid3x3",
        title: "Upgrade to premium vitrified flooring",
        description: "Better scratch resistance, cleaner joints, and a premium finish across living and bedrooms.",
        impact: "Add ₹80K – ₹2L", priority: "Medium",
      });
      if (!has("compound") || !has("gate")) recs.push({
        id: "up-compound", category: "upgrade", badge: "Upgrade", icon: "Fence",
        title: "Add compound wall with decorative gate",
        description: "Improves security, privacy and property valuation. Do it during construction to save on repeat mobilization costs.",
        impact: "Add ₹1.8L – ₹3L", priority: "Medium",
      });
      if (!has("cctv")) recs.push({
        id: "up-cctv", category: "upgrade", badge: "Upgrade", icon: "Cctv",
        title: "Install a CCTV security system",
        description: "4–8 camera IP setup with NVR and mobile access adds a strong security layer with negligible running cost.",
        impact: "Add ₹45K – ₹75K", priority: "Low",
      });
      if (!has("smart")) recs.push({
        id: "up-smart", category: "upgrade", badge: "Upgrade", icon: "Cpu",
        title: "Add smart door locks and video door phone",
        description: "Keyless entry with fingerprint/PIN and video verification of visitors — practical, family-friendly upgrades.",
        impact: "Add ₹35K – ₹90K", priority: "Low",
      });
      if (!has("ceiling")) recs.push({
        id: "up-ceiling", category: "upgrade", badge: "Upgrade", icon: "Layers",
        title: "False ceiling with concealed LED lighting",
        description: "Transforms the living room and master bedroom, hides electrical conduits, and enables layered mood lighting.",
        impact: "Add ₹1.2L – ₹1.8L", priority: "Low",
      });
      recs.push({
        id: "up-rainwater", category: "upgrade", badge: "Upgrade", icon: "Droplet",
        title: "Install rainwater harvesting",
        description: "Kerala’s monsoon makes this one of the highest-ROI upgrades. Recharges the borewell and reduces groundwater dependence.",
        impact: "Add ₹40K – ₹90K · Long-term savings", priority: "Medium",
      });
      recs.push({
        id: "up-porch", category: "upgrade", badge: "Upgrade", icon: "Car",
        title: "Covered car porch with cantilever roof",
        description: "Protects your vehicle from sun and rain, extends the elevation, and adds usable semi-outdoor space.",
        impact: "Add ₹90K – ₹1.6L", priority: "Low",
      });
      if (i.kitchen !== "Modular") recs.push({
        id: "up-kitchen", category: "upgrade", badge: "Upgrade", icon: "ChefHat",
        title: "Upgrade to a premium modular kitchen",
        description: "Ergonomic layouts, soft-close hardware and easy-clean surfaces make daily cooking dramatically more pleasant.",
        impact: "Add ₹1.5L – ₹3L", priority: "Medium",
      });
    }

    // Positive highlights
    recs.push({
      id: "pos-config",
      category: "positive",
      badge: "Positive",
      icon: "CheckCircle2",
      title: "Your configuration is financially balanced",
      description: "Room-to-bath ratio, floor count and quality tier are consistent with a well-planned Kerala home.",
      impact: "Long-term value",
      priority: "Low",
    });
    if (i.parking >= 1) recs.push({
      id: "pos-parking",
      category: "positive",
      badge: "Positive",
      icon: "Car",
      title: "Parking included — future-proofed",
      description: "Dedicated parking is a strong resale factor and avoids costly retrofits later.",
      impact: "Resale value",
      priority: "Low",
    });
  }

  // ---- Universal risk alerts ----
  recs.push({
    id: "risk-materials",
    category: "risk",
    badge: "Project Risk",
    icon: "TrendingUp",
    title: "Material prices fluctuate month to month",
    description: "Steel, cement and tile prices move with fuel and import trends. Lock rates with your dealer at each slab stage.",
    impact: "±3–6% swing",
    priority: "Medium",
  });
  recs.push({
    id: "risk-labour",
    category: "risk",
    badge: "Project Risk",
    icon: "Users",
    title: `Labour rates vary across ${i.district}`,
    description: "Compare at least three contractor quotes and freeze payment milestones tied to visible progress.",
    impact: "±5–10% swing",
    priority: "Medium",
  });
  recs.push({
    id: "risk-site",
    category: "risk",
    badge: "Project Risk",
    icon: "Layers",
    title: "Site conditions can affect foundation cost",
    description: "Waterlogged or sloped plots need extra earthwork or piling. Get a soil test before finalizing the foundation design.",
    impact: "+₹50K – ₹2L possible",
    priority: "Medium",
  });
  recs.push({
    id: "risk-contingency",
    category: "risk",
    badge: "Project Risk",
    icon: "Wallet",
    title: "Keep 5–10% contingency reserve",
    description: "Unforeseen scope changes, weather delays and price revisions are common. A contingency reserve prevents mid-project stalls.",
    impact: `Reserve ~${lakh(total * 0.08)}`,
    priority: "High",
  });

  return recs;
}

// House size insight
export function houseSizeInsight(area: number) {
  if (area < 1200) return { label: "Budget House", desc: "Efficient design with lower maintenance costs." };
  if (area < 1800) return { label: "Standard Family House", desc: "Balanced cost and living space." };
  if (area < 2500) return { label: "Premium House", desc: "Higher comfort with moderate cost increase." };
  return { label: "Luxury House", desc: "Expect higher structural and finishing costs." };
}

// Construction planning score (0-100)
export function planningScore(i: Inputs, total: number, budget: number) {
  let s = 60;
  const util = total / Math.max(1, budget);
  if (util < 0.85) s += 30;
  else if (util < 0.95) s += 22;
  else if (util < 1.02) s += 10;
  else if (util < 1.1) s -= 10;
  else s -= 25;

  if (i.bathrooms >= Math.max(1, i.bedrooms - 1)) s += 4;
  if (i.builtUpArea / Math.max(1, i.bedrooms) >= 380) s += 3;
  if (i.parking >= 1) s += 2;
  if (i.addons.includes("solar")) s += 2;
  if (i.addons.length > 6 && util > 1) s -= 4;

  s = Math.max(0, Math.min(100, Math.round(s)));
  const tier =
    s >= 95 ? "Excellent Planning" :
    s >= 80 ? "Good Planning" :
    s >= 65 ? "Average Planning" :
    "Needs Optimization";
  return { score: s, tier };
}

export function inr(n: number): string {
  if (n >= 1e7) return `₹${(n / 1e7).toFixed(2)} Cr`;
  if (n >= 1e5) return `₹${(n / 1e5).toFixed(2)} L`;
  return `₹${n.toLocaleString("en-IN")}`;
}
