import { createFileRoute } from "@tanstack/react-router";
import { useMemo, useState, useEffect } from "react";
import {
  Home, Building2, Hammer, Wallet, BarChart3, TrendingUp, Clock, BadgeCheck,
  Lightbulb, Calculator, Layers, ArrowRight, ArrowLeft, Check, Sparkles,
  Fence, DoorOpen, Car, Droplet, Waves, Sun, Sofa, Trees, Cpu, Cctv,
  Zap, Grid3x3, Paintbrush, MapPin, Ruler, Bed, Bath, Building,
  IndianRupee, Gauge, ChartPie, Download, Printer, Share2,
} from "lucide-react";
import {
  PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend,
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
} from "recharts";
import {
  DISTRICTS, ADDONS, computeEstimate, stageBreakdown, budgetAnalysis,
  healthScore, houseCategory, recommendations, inr, type Inputs,
} from "@/lib/estimator";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Kerala Home Cost Estimator — Smart Construction Planner" },
      { name: "description", content: "Predict Kerala house construction cost with ML-powered planning, budgeting, stage estimates and smart recommendations." },
      { property: "og:title", content: "Kerala Home Cost Estimator" },
      { property: "og:description", content: "ML-powered construction cost planning for Kerala homes." },
      { property: "og:type", content: "website" },
    ],
  }),
  component: App,
});

type View = "landing" | "wizard" | "loading" | "dashboard";

const initialInputs: Inputs = {
  district: "Ernakulam", builtUpArea: 1800, plotSize: 8, bedrooms: 3,
  bathrooms: 3, floors: 2, parking: 1, balconies: 2,
  kitchen: "Modular", quality: "Standard", roof: "RCC", flooring: "Vitrified Tile",
  budget: 5500000, addons: [],
};

const ADDON_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  Fence, DoorOpen, Car, Droplet, Waves, Sun, Layers, Sofa, Trees, Cpu, Cctv,
};

function App() {
  const [view, setView] = useState<View>("landing");
  const [inputs, setInputs] = useState<Inputs>(initialInputs);

  return (
    <div className="min-h-screen bg-background text-foreground font-sans">
      <link rel="preconnect" href="https://fonts.googleapis.com" />
      <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
      <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@600;700;800&display=swap" rel="stylesheet" />
      <Navbar onHome={() => setView("landing")} onStart={() => setView("wizard")} />
      {view === "landing" && <Landing onStart={() => setView("wizard")} />}
      {view === "wizard" && (
        <Wizard
          inputs={inputs}
          setInputs={setInputs}
          onSubmit={() => {
            setView("loading");
            setTimeout(() => setView("dashboard"), 2400);
          }}
        />
      )}
      {view === "loading" && <LoadingScreen />}
      {view === "dashboard" && (
        <Dashboard inputs={inputs} setInputs={setInputs} onEdit={() => setView("wizard")} />
      )}
      <Footer />
    </div>
  );
}

function Navbar({ onHome, onStart }: { onHome: () => void; onStart: () => void }) {
  return (
    <header className="sticky top-0 z-40 backdrop-blur-md bg-background/75 border-b border-border">
      <div className="max-w-7xl mx-auto flex items-center justify-between px-6 py-4">
        <button onClick={onHome} className="flex items-center gap-2.5 group">
          <span className="grid place-items-center w-9 h-9 rounded-xl bg-gradient-to-br from-primary to-accent-blue text-primary-foreground shadow-sm">
            <Home className="w-5 h-5" />
          </span>
          <span className="font-display font-bold text-lg tracking-tight">Kerala <span className="text-primary">Home</span></span>
        </button>
        <nav className="hidden md:flex items-center gap-8 text-sm text-muted-foreground">
          <a href="#features" className="hover:text-foreground transition">Features</a>
          <a href="#how" className="hover:text-foreground transition">How it works</a>
          <a href="#about" className="hover:text-foreground transition">About</a>
        </nav>
        <button onClick={onStart} className="inline-flex items-center gap-1.5 rounded-full bg-primary text-primary-foreground px-4 py-2 text-sm font-medium hover:opacity-90 transition shadow-sm">
          Estimate <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
}

function Landing({ onStart }: { onStart: () => void }) {
  return (
    <>
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 -z-10 bg-[radial-gradient(ellipse_at_top,oklch(0.94_0.05_245)_0%,transparent_60%)]" />
        <div className="max-w-7xl mx-auto px-6 pt-16 pb-24 md:pt-24 md:pb-32 text-center">
          <div className="inline-flex items-center gap-2 rounded-full bg-accent/70 border border-border px-3 py-1 text-xs text-accent-foreground mb-6">
            <Sparkles className="w-3.5 h-3.5" /> ML-powered · Linear Regression · Kerala dataset
          </div>
          <h1 className="font-display text-4xl md:text-6xl font-extrabold tracking-tight leading-[1.05] mb-5">
            Smart House Construction<br />
            <span className="bg-gradient-to-r from-primary via-accent-blue to-primary bg-clip-text text-transparent">Planning Assistant</span>
          </h1>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto mb-9">
            Predict construction costs using Machine Learning and plan your entire building journey with intelligent budgeting, recommendations and stage-wise estimates.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-3">
            <button onClick={onStart} className="inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-primary to-accent-blue text-primary-foreground px-6 py-3.5 font-semibold shadow-lg shadow-primary/20 hover:shadow-xl hover:-translate-y-0.5 transition">
              Estimate My House <ArrowRight className="w-4 h-4" />
            </button>
            <a href="#features" className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-6 py-3.5 font-medium hover:bg-accent transition">
              See features
            </a>
          </div>
          <div className="mt-14 grid grid-cols-2 md:grid-cols-4 gap-6 max-w-3xl mx-auto text-left">
            {[
              { k: "R²", v: "0.91" },
              { k: "Districts", v: "14" },
              { k: "Data points", v: "1,500" },
              { k: "Cost range", v: "₹25L–1.5Cr" },
            ].map(s => (
              <div key={s.k} className="rounded-2xl bg-card border border-border p-4">
                <div className="text-xs uppercase tracking-wider text-muted-foreground">{s.k}</div>
                <div className="font-display text-2xl font-bold mt-1">{s.v}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section id="features" className="max-w-7xl mx-auto px-6 py-20">
        <div className="text-center mb-14">
          <div className="text-sm font-medium text-primary">Everything you need</div>
          <h2 className="font-display text-3xl md:text-4xl font-bold mt-2">Plan smarter, build with confidence</h2>
        </div>
        <div className="grid md:grid-cols-3 gap-5">
          {[
            { icon: Calculator, t: "Accurate Cost Prediction", d: "Linear regression trained on Kerala construction data." },
            { icon: Wallet, t: "Budget Planning", d: "Track surplus, tight, or shortfall against your budget." },
            { icon: Layers, t: "Stage Breakdown", d: "Foundation → finishing costs mapped to your project." },
            { icon: TrendingUp, t: "Scenario Comparison", d: "Compare quality tiers, roof types, and areas side by side." },
            { icon: Lightbulb, t: "Smart Recommendations", d: "Materials, savings and design tips tailored to you." },
            { icon: BadgeCheck, t: "Optional Add-ons", d: "Solar, borewell, interiors — priced instantly." },
          ].map((f) => (
            <div key={f.t} className="group rounded-2xl bg-card border border-border p-6 hover:shadow-lg hover:-translate-y-0.5 transition">
              <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-primary/10 to-accent-blue/10 grid place-items-center text-primary mb-4">
                <f.icon className="w-5 h-5" />
              </div>
              <div className="font-display font-semibold text-lg">{f.t}</div>
              <div className="text-sm text-muted-foreground mt-1">{f.d}</div>
            </div>
          ))}
        </div>
      </section>

      <section id="how" className="max-w-7xl mx-auto px-6 pb-24">
        <div className="rounded-3xl bg-gradient-to-br from-primary to-accent-blue text-primary-foreground p-10 md:p-14 shadow-xl">
          <h3 className="font-display text-2xl md:text-3xl font-bold">Ready in three steps</h3>
          <div className="grid md:grid-cols-3 gap-6 mt-8">
            {[
              ["01", "Tell us about your plot & home"],
              ["02", "Set quality, roof, flooring & budget"],
              ["03", "Get a full dashboard & report"],
            ].map(([n, t]) => (
              <div key={n} className="rounded-2xl bg-white/10 backdrop-blur p-5">
                <div className="font-display text-3xl font-bold opacity-80">{n}</div>
                <div className="mt-2 font-medium">{t}</div>
              </div>
            ))}
          </div>
          <button onClick={onStart} className="mt-8 inline-flex items-center gap-2 rounded-full bg-white text-primary px-6 py-3 font-semibold hover:bg-white/90 transition">
            Start estimate <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </section>
    </>
  );
}

function Wizard({ inputs, setInputs, onSubmit }: { inputs: Inputs; setInputs: (i: Inputs) => void; onSubmit: () => void }) {
  const [step, setStep] = useState(0);
  const steps = ["Location", "Specifications", "Details", "Budget"];
  const next = () => setStep(s => Math.min(steps.length - 1, s + 1));
  const prev = () => setStep(s => Math.max(0, s - 1));
  const upd = <K extends keyof Inputs,>(k: K, v: Inputs[K]) => setInputs({ ...inputs, [k]: v });

  return (
    <section className="max-w-4xl mx-auto px-6 py-12">
      <div className="mb-8">
        <div className="flex items-center justify-between mb-3">
          {steps.map((s, i) => (
            <div key={s} className="flex-1 flex items-center">
              <div className={`w-9 h-9 rounded-full grid place-items-center text-sm font-semibold border-2 transition ${i <= step ? "bg-primary text-primary-foreground border-primary" : "bg-card text-muted-foreground border-border"}`}>
                {i < step ? <Check className="w-4 h-4" /> : i + 1}
              </div>
              {i < steps.length - 1 && <div className={`flex-1 h-0.5 mx-2 ${i < step ? "bg-primary" : "bg-border"}`} />}
            </div>
          ))}
        </div>
        <div className="flex justify-between text-xs text-muted-foreground">
          {steps.map(s => <div key={s} className="flex-1 text-center">{s}</div>)}
        </div>
      </div>

      <div className="rounded-3xl bg-card border border-border p-8 shadow-sm">
        {step === 0 && (
          <>
            <StepHeader icon={MapPin} title="Where are you building?" sub="District affects material rates and labour costs." />
            <div>
              <label className="text-sm font-medium">District</label>
              <select value={inputs.district} onChange={(e) => upd("district", e.target.value)} className="mt-2 w-full rounded-xl border border-input bg-background px-4 py-3 text-base focus:outline-none focus:ring-2 focus:ring-ring">
                {DISTRICTS.map(d => <option key={d}>{d}</option>)}
              </select>
            </div>
          </>
        )}

        {step === 1 && (
          <>
            <StepHeader icon={Building2} title="House specifications" sub="Size and layout drive the biggest cost differences." />
            <div className="grid md:grid-cols-2 gap-5">
              <Num label="Built-up Area (sqft)" icon={Ruler} value={inputs.builtUpArea} min={500} max={6000} step={50} onChange={v => upd("builtUpArea", v)} />
              <Num label="Plot Size (cents)" icon={Layers} value={inputs.plotSize} min={3} max={50} step={1} onChange={v => upd("plotSize", v)} />
              <Num label="Bedrooms" icon={Bed} value={inputs.bedrooms} min={1} max={8} step={1} onChange={v => upd("bedrooms", v)} />
              <Num label="Bathrooms" icon={Bath} value={inputs.bathrooms} min={1} max={8} step={1} onChange={v => upd("bathrooms", v)} />
              <Num label="Floors" icon={Building} value={inputs.floors} min={1} max={4} step={1} onChange={v => upd("floors", v)} />
            </div>
          </>
        )}

        {step === 2 && (
          <>
            <StepHeader icon={Hammer} title="Construction details" sub="Quality tier and finishes shape the total significantly." />
            <div className="grid md:grid-cols-2 gap-5">
              <Num label="Parking Spaces" icon={Car} value={inputs.parking} min={0} max={4} step={1} onChange={v => upd("parking", v)} />
              <Num label="Balconies" icon={Sun} value={inputs.balconies} min={0} max={5} step={1} onChange={v => upd("balconies", v)} />
              <Pick label="Kitchen" value={inputs.kitchen} options={["Normal", "Modular"]} onChange={v => upd("kitchen", v as Inputs["kitchen"])} />
              <Pick label="Quality" value={inputs.quality} options={["Basic", "Standard", "Premium", "Luxury"]} onChange={v => upd("quality", v as Inputs["quality"])} />
              <Pick label="Roof Type" value={inputs.roof} options={["RCC", "Sloped Roof"]} onChange={v => upd("roof", v as Inputs["roof"])} />
              <Pick label="Flooring" value={inputs.flooring} options={["Cement", "Vitrified Tile", "Granite", "Marble"]} onChange={v => upd("flooring", v as Inputs["flooring"])} />
            </div>
          </>
        )}

        {step === 3 && (
          <>
            <StepHeader icon={Wallet} title="Budget & add-ons" sub="Set your available budget and pick optional features." />
            <div>
              <label className="text-sm font-medium">Available Budget (₹)</label>
              <div className="mt-2 relative">
                <IndianRupee className="w-4 h-4 absolute left-4 top-1/2 -translate-y-1/2 text-muted-foreground" />
                <input type="number" value={inputs.budget} onChange={(e) => upd("budget", Number(e.target.value))}
                  className="w-full rounded-xl border border-input bg-background pl-10 pr-4 py-3 text-base focus:outline-none focus:ring-2 focus:ring-ring" />
              </div>
              <div className="text-xs text-muted-foreground mt-1.5">{inr(inputs.budget)}</div>
            </div>
            <div className="mt-6">
              <div className="text-sm font-medium mb-3">Optional Add-ons</div>
              <div className="grid sm:grid-cols-2 md:grid-cols-3 gap-3">
                {ADDONS.map(a => {
                  const Icon = ADDON_ICONS[a.icon] ?? Layers;
                  const on = inputs.addons.includes(a.key);
                  return (
                    <button key={a.key} onClick={() => upd("addons", on ? inputs.addons.filter(k => k !== a.key) : [...inputs.addons, a.key])}
                      className={`text-left rounded-2xl p-4 border-2 transition ${on ? "border-primary bg-primary/5" : "border-border bg-card hover:border-primary/40"}`}>
                      <div className="flex items-start justify-between">
                        <Icon className={`w-5 h-5 ${on ? "text-primary" : "text-muted-foreground"}`} />
                        {on && <Check className="w-4 h-4 text-primary" />}
                      </div>
                      <div className="mt-2 font-medium text-sm">{a.label}</div>
                      <div className="text-xs text-muted-foreground">{inr(a.cost)}</div>
                    </button>
                  );
                })}
              </div>
            </div>
          </>
        )}

        <div className="mt-8 flex items-center justify-between">
          <button onClick={prev} disabled={step === 0} className="inline-flex items-center gap-1 rounded-full border border-border px-4 py-2 text-sm font-medium disabled:opacity-40 hover:bg-accent transition">
            <ArrowLeft className="w-4 h-4" /> Back
          </button>
          {step < steps.length - 1 ? (
            <button onClick={next} className="inline-flex items-center gap-1 rounded-full bg-primary text-primary-foreground px-5 py-2.5 text-sm font-semibold hover:opacity-90 transition">
              Next <ArrowRight className="w-4 h-4" />
            </button>
          ) : (
            <button onClick={onSubmit} className="inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-primary to-accent-blue text-primary-foreground px-6 py-3 text-sm font-semibold shadow-lg shadow-primary/20 hover:-translate-y-0.5 transition">
              <Calculator className="w-4 h-4" /> Predict Cost
            </button>
          )}
        </div>
      </div>
    </section>
  );
}

function StepHeader({ icon: Icon, title, sub }: { icon: React.ComponentType<{ className?: string }>; title: string; sub: string }) {
  return (
    <div className="flex items-start gap-3 mb-6">
      <div className="w-10 h-10 rounded-xl bg-primary/10 text-primary grid place-items-center"><Icon className="w-5 h-5" /></div>
      <div>
        <div className="font-display text-xl font-bold">{title}</div>
        <div className="text-sm text-muted-foreground">{sub}</div>
      </div>
    </div>
  );
}

function Num({ label, icon: Icon, value, min, max, step, onChange }:
  { label: string; icon: React.ComponentType<{ className?: string }>; value: number; min: number; max: number; step: number; onChange: (v: number) => void }) {
  return (
    <div>
      <label className="text-sm font-medium flex items-center gap-1.5"><Icon className="w-4 h-4 text-muted-foreground" />{label}</label>
      <input type="number" value={value} min={min} max={max} step={step} onChange={(e) => onChange(Number(e.target.value))}
        className="mt-2 w-full rounded-xl border border-input bg-background px-4 py-3 focus:outline-none focus:ring-2 focus:ring-ring" />
      <input type="range" value={value} min={min} max={max} step={step} onChange={(e) => onChange(Number(e.target.value))}
        className="mt-2 w-full accent-primary" />
    </div>
  );
}

function Pick({ label, value, options, onChange }: { label: string; value: string; options: string[]; onChange: (v: string) => void }) {
  return (
    <div>
      <label className="text-sm font-medium">{label}</label>
      <div className="mt-2 grid grid-cols-2 gap-2">
        {options.map(o => (
          <button key={o} onClick={() => onChange(o)}
            className={`rounded-xl px-3 py-2.5 text-sm font-medium border transition ${value === o ? "bg-primary text-primary-foreground border-primary" : "bg-card text-foreground border-border hover:bg-accent"}`}>
            {o}
          </button>
        ))}
      </div>
    </div>
  );
}

function LoadingScreen() {
  const messages = [
    "Analyzing House Specifications...",
    "Predicting Construction Cost...",
    "Calculating Budget Analysis...",
    "Preparing Recommendations...",
    "Generating Dashboard...",
  ];
  const [i, setI] = useState(0);
  useEffect(() => {
    const t = setInterval(() => setI(x => (x + 1) % messages.length), 480);
    return () => clearInterval(t);
  }, []);
  return (
    <section className="max-w-3xl mx-auto px-6 py-24 text-center">
      <div className="mx-auto w-20 h-20 rounded-3xl bg-gradient-to-br from-primary to-accent-blue grid place-items-center text-primary-foreground shadow-xl shadow-primary/30 animate-pulse">
        <Calculator className="w-10 h-10" />
      </div>
      <div className="mt-8 font-display text-2xl font-bold">{messages[i]}</div>
      <div className="mt-6 max-w-md mx-auto h-2 rounded-full bg-muted overflow-hidden">
        <div className="h-full bg-gradient-to-r from-primary to-accent-blue animate-[loading_2.4s_ease-in-out]" style={{ width: `${(i + 1) * 20}%`, transition: "width 400ms" }} />
      </div>
    </section>
  );
}

/* ---------------- DASHBOARD ---------------- */

function Dashboard({ inputs, setInputs, onEdit }: { inputs: Inputs; setInputs: (i: Inputs) => void; onEdit: () => void }) {
  const est = useMemo(() => computeEstimate(inputs), [inputs]);
  const stages = useMemo(() => stageBreakdown(est.base), [est.base]);
  const budget = useMemo(() => budgetAnalysis(inputs.budget, est.total), [inputs.budget, est.total]);
  const hs = useMemo(() => healthScore(inputs, est.total, inputs.budget), [inputs, est.total]);
  const category = houseCategory(est.total);
  const recs = useMemo(() => recommendations(inputs, est.total, inputs.budget), [inputs, est.total]);

  const scenarios = useMemo(() => ([
    { name: "Basic", cost: computeEstimate({ ...inputs, quality: "Basic" }).total },
    { name: "Standard", cost: computeEstimate({ ...inputs, quality: "Standard" }).total },
    { name: "Premium", cost: computeEstimate({ ...inputs, quality: "Premium" }).total },
    { name: "Luxury", cost: computeEstimate({ ...inputs, quality: "Luxury" }).total },
  ]), [inputs]);

  const toggleAddon = (k: string) => setInputs({ ...inputs, addons: inputs.addons.includes(k) ? inputs.addons.filter(x => x !== k) : [...inputs.addons, k] });

  return (
    <section className="max-w-7xl mx-auto px-6 py-10">
      <div className="flex flex-wrap items-center justify-between gap-3 mb-8">
        <div>
          <div className="text-sm text-muted-foreground">Estimate for {inputs.district} · {inputs.builtUpArea} sqft</div>
          <h1 className="font-display text-3xl md:text-4xl font-extrabold tracking-tight">Your Construction Dashboard</h1>
        </div>
        <button onClick={onEdit} className="inline-flex items-center gap-1.5 rounded-full border border-border bg-card px-4 py-2 text-sm font-medium hover:bg-accent transition">
          Edit inputs
        </button>
      </div>

      {/* KPIs */}
      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard gradient icon={IndianRupee} label="Estimated Cost" value={inr(est.total)} sub="Linear regression prediction" />
        <KpiCard icon={BarChart3} label="Expected Range" value={`${inr(est.low)} – ${inr(est.high)}`} sub="90% confidence band" />
        <KpiCard icon={Wallet} label="Budget Status" value={budget.status === "within" ? "Within Budget" : budget.status === "tight" ? "Budget Tight" : "Budget Short"}
          sub={`Utilization ${budget.utilization}%`} tone={budget.status === "within" ? "good" : budget.status === "tight" ? "warn" : "bad"} />
        <KpiCard icon={BadgeCheck} label="Model Confidence" value={`${Math.round(est.confidence * 100)}%`} sub={`R² ${est.r2} · MAE ${inr(est.mae)}`} />
      </div>

      {/* Second row */}
      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4 mt-4">
        <StatCard icon={Ruler} label="Cost per sqft" value={inr(est.perSqft)} />
        <StatCard icon={Clock} label="Construction Duration" value={`${est.months - 1}–${est.months + 1} months`} />
        <StatCard icon={Home} label="House Category" value={category} />
        <HealthCard score={hs} />
      </div>

      {/* Budget analysis */}
      <div className="mt-8 rounded-3xl bg-card border border-border p-6 md:p-8">
        <div className="flex items-center gap-2 mb-5">
          <Wallet className="w-5 h-5 text-primary" />
          <h2 className="font-display text-xl font-bold">Budget Analysis</h2>
        </div>
        <div className="grid md:grid-cols-4 gap-4">
          <BudgetTile label="Your Budget" value={inr(inputs.budget)} />
          <BudgetTile label="Predicted Cost" value={inr(est.total)} />
          <BudgetTile label={budget.diff >= 0 ? "Surplus" : "Deficit"} value={inr(Math.abs(budget.diff))} tone={budget.diff >= 0 ? "good" : "bad"} />
          <BudgetTile label="Utilization" value={`${budget.utilization}%`} tone={budget.status === "within" ? "good" : budget.status === "tight" ? "warn" : "bad"} />
        </div>
        <div className="mt-6">
          <div className="h-3 w-full rounded-full bg-muted overflow-hidden">
            <div className={`h-full transition-all duration-700 ${budget.status === "within" ? "bg-emerald-500" : budget.status === "tight" ? "bg-amber-500" : "bg-red-500"}`}
              style={{ width: `${Math.min(120, budget.utilization)}%` }} />
          </div>
          <div className="mt-2 text-xs text-muted-foreground flex justify-between">
            <span>0%</span><span>50%</span><span>100%</span><span>120%</span>
          </div>
        </div>
      </div>

      {/* Stage distribution — DETAILED BLUE PIE */}
      <div className="mt-8 grid lg:grid-cols-5 gap-6">
        <div className="lg:col-span-3 rounded-3xl bg-card border border-border p-6 md:p-8">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <ChartPie className="w-5 h-5 text-primary" />
              <h2 className="font-display text-xl font-bold">Construction Stage Distribution</h2>
            </div>
            <div className="text-xs text-muted-foreground">Base of {inr(est.base)}</div>
          </div>
          <p className="text-sm text-muted-foreground mb-4">How your base construction cost is split across stages of the build.</p>
          <StageDistributionPie stages={stages} total={est.base} />
        </div>
        <div className="lg:col-span-2 rounded-3xl bg-card border border-border p-6 md:p-8">
          <div className="flex items-center gap-2 mb-4">
            <Layers className="w-5 h-5 text-primary" />
            <h2 className="font-display text-xl font-bold">Stage-wise Cost</h2>
          </div>
          <div className="space-y-4">
            {stages.map((s, i) => (
              <div key={s.key}>
                <div className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2 font-medium">
                    <span className="w-2.5 h-2.5 rounded-full" style={{ background: BLUE_SHADES[i] }} />
                    {s.label}
                  </div>
                  <div className="tabular-nums">{inr(s.cost)}</div>
                </div>
                <div className="mt-1.5 h-2 bg-muted rounded-full overflow-hidden">
                  <div className="h-full rounded-full transition-all duration-700" style={{ width: `${s.pct * 100}%`, background: BLUE_SHADES[i] }} />
                </div>
                <div className="text-xs text-muted-foreground mt-1">{Math.round(s.pct * 100)}% · {s.desc}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recommendations */}
      <div className="mt-8">
        <div className="flex items-center gap-2 mb-4">
          <Lightbulb className="w-5 h-5 text-primary" />
          <h2 className="font-display text-xl font-bold">Smart Recommendations</h2>
        </div>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          <RecCard title="Budget Advice" tone="blue" items={recs.budgetAdvice} />
          <RecCard title="Design Advice" tone="indigo" items={recs.design} />
          <RecCard title="Material Suggestions" tone="cyan" items={recs.materials} />
          <RecCard title="Cost Saving Tips" tone="sky" items={recs.savings} />
          <RecCard title="Positive Highlights" tone="emerald" items={recs.positive} />
        </div>
      </div>

      {/* Add-ons */}
      <div className="mt-8 rounded-3xl bg-card border border-border p-6 md:p-8">
        <div className="flex items-center justify-between flex-wrap gap-3 mb-4">
          <div className="flex items-center gap-2">
            <BadgeCheck className="w-5 h-5 text-primary" />
            <h2 className="font-display text-xl font-bold">Optional Add-ons</h2>
          </div>
          <div className="text-sm text-muted-foreground">Add-on total: <b className="text-foreground">{inr(est.addons)}</b> · Grand total: <b className="text-foreground">{inr(est.total)}</b></div>
        </div>
        <div className="grid sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
          {ADDONS.map(a => {
            const Icon = ADDON_ICONS[a.icon] ?? Layers;
            const on = inputs.addons.includes(a.key);
            return (
              <button key={a.key} onClick={() => toggleAddon(a.key)}
                className={`text-left rounded-2xl p-4 border-2 transition ${on ? "border-primary bg-primary/5" : "border-border bg-card hover:border-primary/40"}`}>
                <div className="flex items-start justify-between">
                  <Icon className={`w-5 h-5 ${on ? "text-primary" : "text-muted-foreground"}`} />
                  {on && <Check className="w-4 h-4 text-primary" />}
                </div>
                <div className="mt-2 font-medium text-sm">{a.label}</div>
                <div className="text-xs text-muted-foreground">{inr(a.cost)}</div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Scenario comparison */}
      <div className="mt-8 rounded-3xl bg-card border border-border p-6 md:p-8">
        <div className="flex items-center gap-2 mb-4">
          <TrendingUp className="w-5 h-5 text-primary" />
          <h2 className="font-display text-xl font-bold">Scenario Comparison</h2>
        </div>
        <p className="text-sm text-muted-foreground mb-4">How total cost shifts across quality tiers, keeping everything else equal.</p>
        <div className="h-72">
          <ResponsiveContainer>
            <BarChart data={scenarios} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="name" tick={{ fill: "var(--muted-foreground)", fontSize: 12 }} />
              <YAxis tickFormatter={(v: number) => `${(v / 1e5).toFixed(0)}L`} tick={{ fill: "var(--muted-foreground)", fontSize: 12 }} />
              <Tooltip formatter={(v: number) => inr(v)} contentStyle={{ borderRadius: 12, border: "1px solid var(--border)", background: "var(--card)" }} />
              <Bar dataKey="cost" radius={[10, 10, 0, 0]}>
                {scenarios.map((s, i) => (
                  <Cell key={s.name} fill={BLUE_SHADES[(i * 2) % BLUE_SHADES.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Summary + Report */}
      <div className="mt-8 grid lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 rounded-3xl bg-gradient-to-br from-primary to-accent-blue text-primary-foreground p-8">
          <div className="text-sm opacity-80">Result Summary</div>
          <div className="font-display text-3xl md:text-4xl font-extrabold mt-1">{category} · {inr(est.total)}</div>
          <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              ["Estimated Cost", inr(est.total)],
              ["Completion", `${est.months - 1}–${est.months + 1} mo`],
              ["Budget", budget.status === "within" ? "Within Budget" : budget.status === "tight" ? "Tight" : "Short"],
              ["Confidence", `${Math.round(est.confidence * 100)}%`],
            ].map(([k, v]) => (
              <div key={k} className="rounded-2xl bg-white/10 backdrop-blur p-4">
                <div className="text-xs opacity-80">{k}</div>
                <div className="font-display text-lg font-bold mt-0.5">{v}</div>
              </div>
            ))}
          </div>
        </div>
        <div className="rounded-3xl bg-card border border-border p-6">
          <div className="flex items-center gap-2 mb-3">
            <Gauge className="w-5 h-5 text-primary" />
            <h3 className="font-display font-bold">Report</h3>
          </div>
          <div className="space-y-2">
            {[
              { icon: Download, label: "Download PDF" },
              { icon: Printer, label: "Print Report" },
              { icon: Share2, label: "Share Report" },
            ].map((r) => (
              <button key={r.label} disabled className="w-full flex items-center justify-between rounded-xl border border-border px-4 py-3 text-sm opacity-60 cursor-not-allowed">
                <span className="flex items-center gap-2"><r.icon className="w-4 h-4" />{r.label}</span>
                <span className="text-xs px-2 py-0.5 rounded-full bg-muted text-muted-foreground">Coming soon</span>
              </button>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

/* ---------- Blue palette for pie/bars ---------- */
const BLUE_SHADES = [
  "#1e3a8a", "#1d4ed8", "#2563eb", "#3b82f6",
  "#60a5fa", "#38bdf8", "#0ea5e9", "#0284c7",
];

function StageDistributionPie({ stages, total }: { stages: ReturnType<typeof stageBreakdown>; total: number }) {
  const data = stages.map((s, i) => ({ name: s.label, value: s.cost, pct: s.pct, desc: s.desc, fill: BLUE_SHADES[i] }));
  return (
    <div className="grid md:grid-cols-5 gap-4 items-center">
      <div className="md:col-span-3 h-80 relative">
        <ResponsiveContainer>
          <PieChart>
            <Pie data={data} dataKey="value" nameKey="name" innerRadius={70} outerRadius={120} paddingAngle={2} stroke="var(--card)" strokeWidth={3}>
              {data.map((d, i) => <Cell key={i} fill={d.fill} />)}
            </Pie>
            <Tooltip
              formatter={(v: number, _n, p) => [`${inr(v)} · ${Math.round((p.payload.pct as number) * 100)}%`, p.payload.name]}
              contentStyle={{ borderRadius: 12, border: "1px solid var(--border)", background: "var(--card)" }}
            />
          </PieChart>
        </ResponsiveContainer>
        <div className="absolute inset-0 pointer-events-none grid place-items-center">
          <div className="text-center">
            <div className="text-xs uppercase tracking-wider text-muted-foreground">Base cost</div>
            <div className="font-display text-2xl font-extrabold">{inr(total)}</div>
            <div className="text-xs text-muted-foreground mt-0.5">8 stages</div>
          </div>
        </div>
      </div>
      <div className="md:col-span-2 space-y-2">
        {data.map(d => (
          <div key={d.name} className="flex items-start gap-2.5 rounded-xl border border-border p-2.5 bg-background/60">
            <span className="mt-1 w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ background: d.fill }} />
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between gap-2 text-sm">
                <span className="font-medium truncate">{d.name}</span>
                <span className="tabular-nums text-muted-foreground">{Math.round(d.pct * 100)}%</span>
              </div>
              <div className="text-xs text-muted-foreground truncate">{d.desc}</div>
              <div className="text-xs font-semibold tabular-nums mt-0.5">{inr(d.value)}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ---------- Small components ---------- */

function KpiCard({ icon: Icon, label, value, sub, gradient, tone }:
  { icon: React.ComponentType<{ className?: string }>; label: string; value: string; sub?: string; gradient?: boolean; tone?: "good" | "warn" | "bad" }) {
  const toneClass = tone === "good" ? "text-emerald-600" : tone === "warn" ? "text-amber-600" : tone === "bad" ? "text-red-600" : "";
  return (
    <div className={`rounded-3xl p-6 border transition hover:-translate-y-0.5 hover:shadow-lg ${gradient ? "bg-gradient-to-br from-primary to-accent-blue text-primary-foreground border-transparent shadow-lg shadow-primary/20" : "bg-card border-border"}`}>
      <div className="flex items-center justify-between">
        <div className={`text-xs uppercase tracking-wider ${gradient ? "opacity-80" : "text-muted-foreground"}`}>{label}</div>
        <Icon className={`w-5 h-5 ${gradient ? "opacity-90" : "text-muted-foreground"}`} />
      </div>
      <div className={`mt-3 font-display text-2xl md:text-3xl font-extrabold ${!gradient ? toneClass : ""}`}>{value}</div>
      {sub && <div className={`text-xs mt-1 ${gradient ? "opacity-80" : "text-muted-foreground"}`}>{sub}</div>}
    </div>
  );
}

function StatCard({ icon: Icon, label, value }: { icon: React.ComponentType<{ className?: string }>; label: string; value: string }) {
  return (
    <div className="rounded-3xl bg-card border border-border p-5 flex items-center gap-4">
      <div className="w-11 h-11 rounded-2xl bg-primary/10 text-primary grid place-items-center"><Icon className="w-5 h-5" /></div>
      <div>
        <div className="text-xs uppercase tracking-wider text-muted-foreground">{label}</div>
        <div className="font-display font-bold text-lg">{value}</div>
      </div>
    </div>
  );
}

function HealthCard({ score }: { score: number }) {
  const tier = score >= 85 ? "Excellent" : score >= 70 ? "Good" : score >= 50 ? "Average" : "Needs Improvement";
  const color = score >= 85 ? "text-emerald-600" : score >= 70 ? "text-sky-600" : score >= 50 ? "text-amber-600" : "text-red-600";
  const bar = score >= 85 ? "bg-emerald-500" : score >= 70 ? "bg-sky-500" : score >= 50 ? "bg-amber-500" : "bg-red-500";
  return (
    <div className="rounded-3xl bg-card border border-border p-5">
      <div className="flex items-center justify-between">
        <div className="text-xs uppercase tracking-wider text-muted-foreground">Health Score</div>
        <Gauge className="w-5 h-5 text-muted-foreground" />
      </div>
      <div className={`font-display text-2xl font-extrabold mt-2 ${color}`}>{score}/100</div>
      <div className="text-xs text-muted-foreground">{tier}</div>
      <div className="mt-3 h-2 bg-muted rounded-full overflow-hidden">
        <div className={`h-full ${bar} transition-all duration-700`} style={{ width: `${score}%` }} />
      </div>
    </div>
  );
}

function BudgetTile({ label, value, tone }: { label: string; value: string; tone?: "good" | "warn" | "bad" }) {
  const color = tone === "good" ? "text-emerald-600" : tone === "warn" ? "text-amber-600" : tone === "bad" ? "text-red-600" : "";
  return (
    <div className="rounded-2xl bg-background border border-border p-4">
      <div className="text-xs uppercase tracking-wider text-muted-foreground">{label}</div>
      <div className={`font-display text-xl font-bold mt-1 ${color}`}>{value}</div>
    </div>
  );
}

function RecCard({ title, items, tone }: { title: string; items: string[]; tone: "blue" | "indigo" | "cyan" | "sky" | "emerald" }) {
  if (!items.length) return null;
  const bg = {
    blue: "from-blue-500/10 to-blue-500/0",
    indigo: "from-indigo-500/10 to-indigo-500/0",
    cyan: "from-cyan-500/10 to-cyan-500/0",
    sky: "from-sky-500/10 to-sky-500/0",
    emerald: "from-emerald-500/10 to-emerald-500/0",
  }[tone];
  return (
    <div className={`rounded-3xl bg-gradient-to-br ${bg} bg-card border border-border p-5`}>
      <div className="font-display font-bold mb-3">{title}</div>
      <ul className="space-y-2 text-sm">
        {items.map((t, i) => (
          <li key={i} className="flex gap-2"><Check className="w-4 h-4 text-primary flex-shrink-0 mt-0.5" /><span className="text-muted-foreground">{t}</span></li>
        ))}
      </ul>
    </div>
  );
}

function Footer() {
  return (
    <footer id="about" className="border-t border-border mt-16">
      <div className="max-w-7xl mx-auto px-6 py-10 grid md:grid-cols-3 gap-6 text-sm">
        <div>
          <div className="flex items-center gap-2 font-display font-bold text-base">
            <span className="grid place-items-center w-8 h-8 rounded-xl bg-gradient-to-br from-primary to-accent-blue text-primary-foreground"><Home className="w-4 h-4" /></span>
            Kerala Home Cost Estimator
          </div>
          <p className="mt-2 text-muted-foreground">Smart house construction planning assistant for Kerala.</p>
        </div>
        <div>
          <div className="font-medium">Model</div>
          <div className="text-muted-foreground">Linear Regression · R² 0.91</div>
          <div className="font-medium mt-3">Dataset</div>
          <div className="text-muted-foreground">Synthetic Kerala Construction Dataset</div>
        </div>
        <div>
          <div className="font-medium">Version</div>
          <div className="text-muted-foreground">1.0</div>
          <div className="font-medium mt-3">Built with</div>
          <div className="text-muted-foreground">React · TanStack Start · Recharts</div>
        </div>
      </div>
    </footer>
  );
}
