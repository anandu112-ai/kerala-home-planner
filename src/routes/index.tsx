import { createFileRoute } from "@tanstack/react-router";
import { useMemo, useState, useEffect, useRef } from "react";
import {
  Home, Building2, Hammer, Wallet, BarChart3, TrendingUp, Clock, BadgeCheck,
  Lightbulb, Calculator, Layers, ArrowRight, ArrowLeft, Check, Sparkles,
  Fence, DoorOpen, Car, Droplet, Waves, Sun, Sofa, Trees, Cpu, Cctv,
  Zap, Grid3x3, Paintbrush, MapPin, Ruler, Bed, Bath, Building,
  IndianRupee, Gauge, ChartPie, Download,
  AlertTriangle, PartyPopper, CheckCircle2, ChefHat, Award, Users, ChevronDown,
  Moon, SunMedium,
} from "lucide-react";
import {
  PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend,
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
} from "recharts";
import {
  DISTRICTS, ADDONS, STAGES, computeEstimate, stageBreakdown, budgetAnalysis,
  healthScore, houseCategory, smartRecommendations, houseSizeInsight, planningScore,
  inr, type Inputs, type SmartRec,
} from "@/lib/estimator";
import jsPDF from "jspdf";
import { type PredictionResponse } from "@/services/predictionApi";
import { serverPredict } from "@/services/serverPredict";
import { toast, Toaster } from "sonner";

async function getPrediction(inputs: Inputs): Promise<PredictionResponse> {
  const result = await serverPredict({
    data: {
      district: inputs.district,
      built_up_area_sqft: inputs.builtUpArea,
      plot_size_cents: inputs.plotSize,
      bedrooms: inputs.bedrooms,
      bathrooms: inputs.bathrooms,
      floors: inputs.floors,
      parking_spaces: inputs.parking,
      balconies: inputs.balconies,
      kitchen_type: inputs.kitchen,
      quality: inputs.quality,
      roof_type: inputs.roof,
      flooring: inputs.flooring,
      budget: inputs.budget,
      addons: inputs.addons,
      site_description: inputs.siteDescription?.trim() || undefined,
    },
  });
  if (!result.ok) {
    throw new Error(result.error);
  }
  return result.data;
}

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Kerala Home Cost Estimator — Smart Construction Planner" },
      { name: "description", content: "Predict Kerala house construction cost with ML-powered planning, budgeting, stage estimates and smart recommendations." },
      { property: "og:title", content: "Kerala Home Cost Estimator — Smart Construction Planner" },
      { property: "og:description", content: "Predict Kerala house construction cost with ML-powered planning, budgeting, stage estimates and smart recommendations." },
      { property: "og:type", content: "website" },
    ],
  }),
  component: App,
});

type View = "landing" | "wizard" | "loading" | "dashboard";

/* ---- Dark mode hook ---- */
function useDarkMode() {
  const [dark, setDark] = useState<boolean>(() => {
    if (typeof window === "undefined") return false;
    const saved = localStorage.getItem("theme");
    if (saved) return saved === "dark";
    return window.matchMedia("(prefers-color-scheme: dark)").matches;
  });

  useEffect(() => {
    const root = document.documentElement;
    if (dark) {
      root.classList.add("dark");
      localStorage.setItem("theme", "dark");
    } else {
      root.classList.remove("dark");
      localStorage.setItem("theme", "light");
    }
  }, [dark]);

  return [dark, setDark] as const;
}

/* ---- Scroll reveal hook ---- */
function useScrollReveal() {
  useEffect(() => {
    const els = document.querySelectorAll(".reveal");
    const observer = new IntersectionObserver(
      (entries) => entries.forEach((e) => {
        if (e.isIntersecting) {
          e.target.classList.add("revealed");
          observer.unobserve(e.target);
        }
      }),
      { threshold: 0.12 }
    );
    els.forEach((el) => observer.observe(el));
    return () => observer.disconnect();
  });
}

/* ---- Animated counter ---- */
function AnimatedNumber({ to, prefix = "", suffix = "" }: { to: number; prefix?: string; suffix?: string }) {
  const [val, setVal] = useState(0);
  const ref = useRef<HTMLSpanElement>(null);
  useEffect(() => {
    const obs = new IntersectionObserver(([e]) => {
      if (!e.isIntersecting) return;
      obs.disconnect();
      const dur = 1400;
      const start = performance.now();
      const tick = (t: number) => {
        const p = Math.min(1, (t - start) / dur);
        const eased = 1 - Math.pow(1 - p, 3);
        setVal(Math.round(eased * to));
        if (p < 1) requestAnimationFrame(tick);
      };
      requestAnimationFrame(tick);
    }, { threshold: 0.5 });
    if (ref.current) obs.observe(ref.current);
    return () => obs.disconnect();
  }, [to]);
  return <span ref={ref}>{prefix}{val.toLocaleString("en-IN")}{suffix}</span>;
}

const initialInputs: Inputs = {
  district: "Ernakulam", builtUpArea: 1800, plotSize: 8, bedrooms: 3,
  bathrooms: 3, floors: 2, parking: 1, balconies: 2,
  kitchen: "Modular", quality: "Standard", roof: "RCC", flooring: "Vitrified Tile",
  budget: 5500000, addons: [], siteDescription: "",
};

const ADDON_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  Fence, DoorOpen, Car, Droplet, Waves, Sun, Layers, Sofa, Trees, Cpu, Cctv,
};

// Shape of the JSON response from the FastAPI /predict endpoint
type ApiResult = PredictionResponse | null;

function App() {
  const [view, setView] = useState<View>("landing");
  const [inputs, setInputs] = useState<Inputs>(initialInputs);
  const [apiResult, setApiResult] = useState<ApiResult>(null);
  const [dark, setDark] = useDarkMode();
  useScrollReveal();

  useEffect(() => {
    const t = setTimeout(() => {
      window.scrollTo(0, 0);
      if (typeof document !== "undefined") {
        document.documentElement.scrollTop = 0;
        document.body.scrollTop = 0;
      }
    }, 50);
    return () => clearTimeout(t);
  }, [view]);

  const handleSubmit = async () => {
    if (!inputs.district || !inputs.builtUpArea || !inputs.budget) {
      toast.error("Please fill in all required fields.");
      return;
    }
    setView("loading");
    try {
      const result = await getPrediction(inputs);
      setApiResult(result);
    } catch (err) {
      console.warn("ML backend unreachable, using built-in estimate engine:", err);
      toast.error("Backend unavailable — showing local estimate.");
      setApiResult(null);
    }
    setTimeout(() => setView("dashboard"), 2400);
  };

  return (
    <div className="min-h-screen bg-background text-foreground font-sans transition-colors duration-300">
      <link rel="preconnect" href="https://fonts.googleapis.com" />
      <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
      <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@600;700;800&display=swap" rel="stylesheet" />
      <Toaster richColors position="top-right" />
      <Navbar onHome={() => setView("landing")} onStart={() => setView("wizard")} dark={dark} onToggleDark={() => setDark(d => !d)} />
      {view === "landing" && <Landing onStart={() => setView("wizard")} />}
      {view === "wizard" && (
        <Wizard
          inputs={inputs}
          setInputs={setInputs}
          onSubmit={handleSubmit}
        />
      )}
      {view === "loading" && <LoadingScreen />}
      {view === "dashboard" && (
        <Dashboard inputs={inputs} setInputs={setInputs} apiResult={apiResult} onEdit={() => setView("wizard")} />
      )}
      <Footer />
    </div>
  );
}

function Navbar({ onHome, onStart, dark, onToggleDark }: { onHome: () => void; onStart: () => void; dark: boolean; onToggleDark: () => void }) {
  const [scrolled, setScrolled] = useState(false);
  useEffect(() => {
    const fn = () => setScrolled(window.scrollY > 10);
    window.addEventListener("scroll", fn, { passive: true });
    return () => window.removeEventListener("scroll", fn);
  }, []);

  return (
    <header className={`sticky top-0 z-40 transition-all duration-300 ${
      scrolled
        ? "backdrop-blur-xl bg-background/80 border-b border-border shadow-sm"
        : "backdrop-blur-md bg-background/60 border-b border-transparent"
    }`}>
      <div className="max-w-7xl mx-auto flex items-center justify-between px-6 py-4">
        <button onClick={onHome} className="flex items-center gap-2.5 group">
          <span className="grid place-items-center w-9 h-9 rounded-xl bg-gradient-to-br from-primary to-accent-blue text-primary-foreground shadow-sm group-hover:shadow-lg group-hover:scale-105 transition-all duration-200">
            <Home className="w-5 h-5" />
          </span>
          <span className="font-display font-bold text-lg tracking-tight">Kerala <span className="text-primary">Home</span></span>
        </button>
        <nav className="hidden md:flex items-center gap-8 text-sm text-muted-foreground">
          <a href="#features" className="hover:text-foreground transition-colors relative after:absolute after:bottom-0 after:left-0 after:h-px after:w-0 after:bg-primary after:transition-all hover:after:w-full">Features</a>
          <a href="#how" className="hover:text-foreground transition-colors relative after:absolute after:bottom-0 after:left-0 after:h-px after:w-0 after:bg-primary after:transition-all hover:after:w-full">How it works</a>
          <a href="#about" className="hover:text-foreground transition-colors relative after:absolute after:bottom-0 after:left-0 after:h-px after:w-0 after:bg-primary after:transition-all hover:after:w-full">About</a>
        </nav>
        <div className="flex items-center gap-2">
          <button
            id="theme-toggle"
            aria-label={dark ? "Switch to light mode" : "Switch to dark mode"}
            onClick={onToggleDark}
            className="w-9 h-9 rounded-full border border-border bg-card flex items-center justify-center hover:bg-accent transition-colors shadow-sm"
          >
            {dark
              ? <SunMedium className="w-4 h-4 text-amber-400" />
              : <Moon className="w-4 h-4 text-muted-foreground" />}
          </button>
          <button onClick={onStart} className="inline-flex items-center gap-1.5 rounded-full bg-primary text-primary-foreground px-4 py-2 text-sm font-medium hover:opacity-90 hover:scale-105 transition-all shadow-sm">
            Estimate <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </header>
  );
}

function Landing({ onStart }: { onStart: () => void }) {
  return (
    <>
      {/* Hero */}
      <section className="relative overflow-hidden">
        {/* Animated gradient blobs */}
        <div className="pointer-events-none absolute inset-0 -z-10 overflow-hidden">
          <div className="absolute -top-40 -left-40 w-[600px] h-[600px] rounded-full bg-primary/10 blur-3xl animate-[blob_9s_ease-in-out_infinite]" />
          <div className="absolute -bottom-40 -right-40 w-[500px] h-[500px] rounded-full bg-accent-blue/10 blur-3xl animate-[blob_11s_ease-in-out_infinite_2s]" />
          <div className="absolute top-1/3 left-1/2 -translate-x-1/2 w-[400px] h-[400px] rounded-full bg-primary/5 blur-2xl animate-[blob_13s_ease-in-out_infinite_4s]" />
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,oklch(0.94_0.05_245/0.6)_0%,transparent_65%)] dark:bg-[radial-gradient(ellipse_at_top,oklch(0.3_0.08_250/0.4)_0%,transparent_65%)]" />
        </div>

        <div className="max-w-7xl mx-auto px-6 pt-20 pb-28 md:pt-28 md:pb-36 text-center">
          <div className="reveal inline-flex items-center gap-2 rounded-full bg-accent/70 border border-border px-3 py-1 text-xs text-accent-foreground mb-6 shadow-sm">
            <Sparkles className="w-3.5 h-3.5 text-primary" /> ML-powered · Linear Regression · Kerala dataset
          </div>
          <h1 className="reveal font-display text-4xl md:text-6xl lg:text-7xl font-extrabold tracking-tight leading-[1.05] mb-6">
            Smart House Construction<br />
            <span className="bg-gradient-to-r from-primary via-accent-blue to-primary bg-clip-text text-transparent animate-gradient-x bg-[length:200%_auto]">Planning Assistant</span>
          </h1>
          <p className="reveal text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto mb-10">
            Predict construction costs using Machine Learning and plan your entire building journey with intelligent budgeting, recommendations and stage-wise estimates.
          </p>
          <div className="reveal flex flex-wrap items-center justify-center gap-3">
            <button
              id="hero-estimate-btn"
              onClick={onStart}
              className="group inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-primary to-accent-blue text-primary-foreground px-7 py-4 font-semibold shadow-xl shadow-primary/25 hover:shadow-2xl hover:-translate-y-1 hover:scale-105 transition-all duration-300"
            >
              Estimate My House
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </button>
            <a href="#features" className="inline-flex items-center gap-2 rounded-full border border-border bg-card/80 backdrop-blur px-7 py-4 font-medium hover:bg-accent hover:-translate-y-0.5 transition-all">
              See features
            </a>
          </div>

          {/* Animated stats */}
          <div className="mt-16 grid grid-cols-2 md:grid-cols-4 gap-5 max-w-3xl mx-auto text-left">
            {[
              { k: "R² Score", numTo: 91, suffix: "%" },
              { k: "Districts", numTo: 14, suffix: "" },
              { k: "Data Points", numTo: 1500, suffix: "" },
              { k: "Model Accuracy", numTo: 96, suffix: "%" },
            ].map(s => (
              <div key={s.k} className="reveal rounded-2xl bg-card/80 backdrop-blur border border-border p-5 hover:shadow-lg hover:-translate-y-0.5 transition-all group">
                <div className="text-xs uppercase tracking-wider text-muted-foreground">{s.k}</div>
                <div className="font-display text-2xl font-bold mt-1 group-hover:text-primary transition-colors">
                  <AnimatedNumber to={s.numTo} suffix={s.suffix} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="max-w-7xl mx-auto px-6 py-20">
        <div className="reveal text-center mb-14">
          <div className="text-sm font-medium text-primary uppercase tracking-wider mb-2">Everything you need</div>
          <h2 className="font-display text-3xl md:text-4xl font-bold">Plan smarter, build with confidence</h2>
          <div className="mt-3 mx-auto w-16 h-1 rounded-full bg-gradient-to-r from-primary to-accent-blue" />
        </div>
        <div className="grid md:grid-cols-3 gap-5">
          {[
            { icon: Calculator, t: "Accurate Cost Prediction", d: "Linear regression trained on Kerala construction data." },
            { icon: Wallet, t: "Budget Planning", d: "Track surplus, tight, or shortfall against your budget." },
            { icon: Layers, t: "Stage Breakdown", d: "Foundation → finishing costs mapped to your project." },
            { icon: TrendingUp, t: "Scenario Comparison", d: "Compare quality tiers, roof types, and areas side by side." },
            { icon: Lightbulb, t: "Smart Recommendations", d: "Materials, savings and design tips tailored to you." },
            { icon: BadgeCheck, t: "Optional Add-ons", d: "Solar, borewell, interiors — priced instantly." },
          ].map((f, i) => (
            <div
              key={f.t}
              className="reveal group rounded-2xl bg-card border border-border p-6 hover:shadow-xl hover:-translate-y-1 transition-all duration-300 hover:border-primary/30"
              style={{ transitionDelay: `${i * 60}ms` }}
            >
              <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-primary/10 to-accent-blue/10 grid place-items-center text-primary mb-4 group-hover:scale-110 group-hover:from-primary/20 group-hover:to-accent-blue/20 transition-all">
                <f.icon className="w-5 h-5" />
              </div>
              <div className="font-display font-semibold text-lg">{f.t}</div>
              <div className="text-sm text-muted-foreground mt-1">{f.d}</div>
            </div>
          ))}
        </div>
      </section>

      {/* How it works */}
      <section id="how" className="max-w-7xl mx-auto px-6 pb-24">
        <div className="reveal rounded-3xl bg-gradient-to-br from-primary to-accent-blue text-primary-foreground p-10 md:p-14 shadow-2xl shadow-primary/20 relative overflow-hidden">
          {/* Decorative circles */}
          <div className="pointer-events-none absolute -top-20 -right-20 w-72 h-72 rounded-full bg-white/5" />
          <div className="pointer-events-none absolute -bottom-10 -left-10 w-48 h-48 rounded-full bg-white/5" />
          <h3 className="font-display text-2xl md:text-3xl font-bold relative">Ready in three steps</h3>
          <div className="grid md:grid-cols-3 gap-6 mt-8 relative">
            {[
              ["01", "Tell us about your plot & home"],
              ["02", "Set quality, roof, flooring & budget"],
              ["03", "Get a full dashboard & report"],
            ].map(([n, t]) => (
              <div key={n} className="rounded-2xl bg-white/10 backdrop-blur p-5 hover:bg-white/20 transition-colors">
                <div className="font-display text-3xl font-bold opacity-80">{n}</div>
                <div className="mt-2 font-medium">{t}</div>
              </div>
            ))}
          </div>
          <button onClick={onStart} className="mt-8 inline-flex items-center gap-2 rounded-full bg-white text-primary px-6 py-3 font-semibold hover:bg-white/90 hover:scale-105 transition-all shadow-lg relative">
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

  useEffect(() => {
    const t = setTimeout(() => {
      window.scrollTo(0, 0);
      if (typeof document !== "undefined") {
        document.documentElement.scrollTop = 0;
        document.body.scrollTop = 0;
      }
    }, 50);
    return () => clearTimeout(t);
  }, [step]);

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

            <div className="mt-8">
              <label className="text-sm font-medium flex items-center gap-1.5">
                <Sparkles className="w-4 h-4 text-primary" />
                Additional Site Details
                <span className="text-xs font-normal text-muted-foreground">(optional but recommended)</span>
              </label>
              <p className="text-xs text-muted-foreground mt-1">
                Describe special conditions our AI can factor into the estimate.
              </p>
              <textarea
                value={inputs.siteDescription ?? ""}
                onChange={(e) => upd("siteDescription", e.target.value.slice(0, 800))}
                rows={6}
                maxLength={800}
                placeholder={`Describe special site conditions:\nExample:\n- No vehicle access\n- Hilly area\n- Near highway\n- Flood-prone area\n- Beautiful valley view\n- Far from city\n- Good water availability`}
                className="mt-2 w-full rounded-xl border border-input bg-background px-4 py-3 text-sm leading-relaxed focus:outline-none focus:ring-2 focus:ring-ring resize-y"
              />
              <div className="mt-1.5 flex justify-between text-xs text-muted-foreground">
                <span>Our AI will detect scenic views, accessibility & risk factors.</span>
                <span>{(inputs.siteDescription ?? "").length}/800</span>
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

function Dashboard({ inputs, setInputs, apiResult, onEdit }: { inputs: Inputs; setInputs: (i: Inputs) => void; apiResult: ApiResult; onEdit: () => void }) {
  // Client-side estimate (always available, used as fallback and for scenarios/recs)
  const est = useMemo(() => computeEstimate(inputs), [inputs]);

  // Prefer ML-predicted cost from API when available
  const mlTotal = apiResult?.predicted_cost ?? est.total;
  const mlAddonsCost = apiResult?.addons.total_cost ?? est.addons;
  const mlBase = mlTotal - mlAddonsCost;
  const mlLow = apiResult?.cost_range.min ?? est.low;
  const mlHigh = apiResult?.cost_range.max ?? est.high;
  const mlPerSqft = apiResult?.cost_per_sqft ?? est.perSqft;
  const mlMonths = est.months; // keep client-side months
  const mlAccuracy = apiResult ? (apiResult.model_accuracy / 100) : est.model_accuracy;
  const mlR2 = est.r2;
  const mlMae = est.mae;

  // Stage breakdown — use API stages if available, else client-side
  const stages = useMemo(() => {
    if (apiResult?.stage_breakdown?.length) {
      return apiResult.stage_breakdown.map((s, i) => ({
        key: STAGES[i]?.key ?? s.stage.toLowerCase(),
        label: s.stage,
        pct: s.percentage / 100,
        cost: s.cost,
        desc: STAGES[i]?.desc ?? "",
        icon: STAGES[i]?.icon ?? "Layers",
      }));
    }
    return stageBreakdown(mlBase);
  }, [apiResult, mlBase]);

  // Budget — use API if available
  const budget = useMemo(() => {
    if (apiResult?.budget) {
      const ab = apiResult.budget;
      const status = ab.status === "Within Budget" ? "within" as const : ab.status === "Budget Tight" ? "tight" as const : "short" as const;
      return { diff: ab.surplus - ab.deficit, utilization: ab.utilization, status };
    }
    return budgetAnalysis(inputs.budget, mlTotal);
  }, [apiResult, inputs.budget, mlTotal]);

  // Health score
  const hs = apiResult?.health_score ?? healthScore(inputs, mlTotal, inputs.budget);
  const category = apiResult?.house_category ?? houseCategory(mlTotal);

  // Smart recommendations and planning score always use client-side (richer logic)
  const recs = useMemo(() => smartRecommendations(inputs, mlTotal, inputs.budget), [inputs, mlTotal]);
  const plan = useMemo(() => planningScore(inputs, mlTotal, inputs.budget), [inputs, mlTotal]);
  const insight = useMemo(() => houseSizeInsight(inputs.builtUpArea), [inputs.builtUpArea]);

  // Build a merged est object for PDF generation
  const mergedEst = {
    ...est,
    total: mlTotal,
    base: mlBase,
    addons: mlAddonsCost,
    low: mlLow,
    high: mlHigh,
    perSqft: mlPerSqft,
    months: mlMonths,
    model_accuracy: mlAccuracy,
  };

  const downloadPdf = () => generateReportPdf({ inputs, est: mergedEst, stages, budget, hs, category, plan, insight, recs });

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
          <div className="text-sm text-muted-foreground">
            Estimate for {inputs.district} · {inputs.builtUpArea} sqft · <span className="font-medium text-foreground">{category}</span>
            {apiResult && <span className="ml-2 inline-flex items-center gap-1 text-emerald-600 font-medium"><BadgeCheck className="w-3.5 h-3.5" />ML Prediction</span>}
          </div>
          <h1 className="font-display text-3xl md:text-4xl font-extrabold tracking-tight">Your Construction Dashboard</h1>
        </div>
        <div className="flex items-center gap-3">
          <button onClick={onEdit} className="inline-flex items-center gap-1.5 rounded-full border border-border bg-card px-4 py-2 text-sm font-medium hover:bg-accent transition">
            Edit inputs
          </button>
          <button onClick={downloadPdf} className="inline-flex items-center gap-1.5 rounded-full bg-primary text-primary-foreground px-4 py-2 text-sm font-semibold hover:opacity-90 transition shadow-sm">
            <Download className="w-4 h-4" /> Download PDF
          </button>
        </div>
      </div>

      {/* KPIs */}
      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard gradient icon={IndianRupee} label="Estimated Cost" value={inr(mlTotal)} sub={apiResult ? "ML model prediction" : "Client-side estimate"} />
        <KpiCard icon={Ruler} label="Cost per sqft" value={inr(mlPerSqft)} sub="Based on built-up area" />
        <KpiCard icon={Clock} label="Construction Duration" value={apiResult?.construction_time ?? `${mlMonths - 1}–${mlMonths + 1} months`} sub="Estimated timeframe" />
        <KpiCard icon={Wallet} label="Budget Status" value={budget.status === "within" ? "Within Budget" : budget.status === "tight" ? "Budget Tight" : "Budget Short"}
          sub={`Utilization ${budget.utilization}%`} tone={budget.status === "within" ? "good" : budget.status === "tight" ? "warn" : "bad"} />
      </div>

      {/* AI Site Analysis */}
      {apiResult?.site_analysis && (
        <SiteAnalysisCard analysis={apiResult.site_analysis} />
      )}


      {/* Budget analysis */}
      <div className="mt-8 rounded-3xl bg-card border border-border p-6 md:p-8">
        <div className="flex items-center gap-2 mb-5">
          <Wallet className="w-5 h-5 text-primary" />
          <h2 className="font-display text-xl font-bold">Budget Analysis</h2>
        </div>
        <div className="grid md:grid-cols-4 gap-4">
          <BudgetTile label="Your Budget" value={inr(inputs.budget)} />
          <BudgetTile label="Predicted Cost" value={inr(mlTotal)} />
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
      <div className="mt-8 rounded-3xl bg-card border border-border p-6 md:p-8">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <ChartPie className="w-5 h-5 text-primary" />
            <h2 className="font-display text-xl font-bold">Construction Stage Distribution</h2>
          </div>
          <div className="text-xs text-muted-foreground">Base of {inr(mlBase)}</div>
        </div>
        <p className="text-sm text-muted-foreground mb-4">How your base construction cost is split across stages of the build.</p>
        <StageDistributionPie stages={stages} total={mlBase} />
      </div>

      {/* Planning score + House size insight */}
      <div className="mt-8 grid lg:grid-cols-3 gap-6">
        <PlanningScoreCard score={plan.score} tier={plan.tier} />
        <div className="lg:col-span-2 rounded-3xl bg-card border border-border p-6 md:p-8">
          <div className="flex items-center gap-2 mb-3">
            <Home className="w-5 h-5 text-primary" />
            <h2 className="font-display text-xl font-bold">House Size Insight</h2>
          </div>
          <div className="flex flex-wrap items-baseline gap-x-3">
            <div className="font-display text-2xl font-extrabold">{insight.label}</div>
            <div className="text-sm text-muted-foreground">· {inputs.builtUpArea} sqft</div>
          </div>
          <p className="text-sm text-muted-foreground mt-2">{insight.desc}</p>
          <div className="mt-5 grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
            <MiniStat label="Bedrooms" value={String(inputs.bedrooms)} />
            <MiniStat label="Bathrooms" value={String(inputs.bathrooms)} />
            <MiniStat label="Floors" value={String(inputs.floors)} />
            <MiniStat label="Quality" value={inputs.quality} />
          </div>
        </div>
      </div>

      {/* Smart Recommendations */}
      <div className="mt-10">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-primary to-accent-blue text-primary-foreground grid place-items-center shadow-lg shadow-primary/20">
            <Lightbulb className="w-5 h-5" />
          </div>
          <div>
            <h2 className="font-display text-2xl md:text-3xl font-extrabold tracking-tight">Smart Construction Recommendations</h2>
            <p className="text-sm text-muted-foreground">Personalized suggestions to optimize your construction cost, improve long-term value, and make informed planning decisions.</p>
          </div>
        </div>
        <SmartRecList recs={recs} />
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

function SiteAnalysisCard({ analysis }: { analysis: NonNullable<PredictionResponse["site_analysis"]> }) {
  const adj = analysis.adjustment_percent;
  const adjTone = adj < 0 ? "text-red-600" : adj > 0 ? "text-emerald-600" : "text-muted-foreground";
  const adjBg = adj < 0 ? "bg-red-50 dark:bg-red-950/30" : adj > 0 ? "bg-emerald-50 dark:bg-emerald-950/30" : "bg-muted";
  const sign = adj > 0 ? "+" : "";
  return (
    <div className="mt-8 rounded-3xl bg-card border border-border p-6 md:p-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex items-center gap-2 mb-1">
        <Sparkles className="w-5 h-5 text-primary" />
        <h2 className="font-display text-xl font-bold">AI Site Analysis</h2>
      </div>
      <p className="text-sm text-muted-foreground mb-6">
        Our AI reviewed the additional site details you provided and adjusted the ML prediction accordingly.
      </p>

      <div className="grid md:grid-cols-3 gap-4">
        <div className="rounded-2xl bg-background border border-border p-4">
          <div className="text-xs uppercase tracking-wider text-muted-foreground">Base ML Prediction</div>
          <div className="font-display text-2xl font-bold mt-1">{inr(analysis.base_prediction)}</div>
        </div>
        <div className={`rounded-2xl border border-border p-4 ${adjBg}`}>
          <div className="text-xs uppercase tracking-wider text-muted-foreground">AI Price Adjustment</div>
          <div className={`font-display text-2xl font-bold mt-1 ${adjTone}`}>{sign}{adj}%</div>
          {analysis.adjustment_reason && (
            <div className="text-xs text-muted-foreground mt-1 line-clamp-2">{analysis.adjustment_reason}</div>
          )}
        </div>
        <div className="rounded-2xl bg-primary/5 border border-primary/30 p-4">
          <div className="text-xs uppercase tracking-wider text-primary/80">Final Estimated Price</div>
          <div className="font-display text-2xl font-bold mt-1 text-primary">{inr(analysis.final_price)}</div>
        </div>
      </div>

      {analysis.detected_conditions.length > 0 && (
        <div className="mt-6">
          <div className="text-sm font-semibold mb-3">Detected Conditions</div>
          <div className="grid sm:grid-cols-2 gap-2">
            {analysis.detected_conditions.map((c, i) => (
              <div
                key={i}
                className={`flex items-center gap-2 rounded-xl border px-3 py-2 text-sm ${
                  c.positive
                    ? "border-emerald-200 dark:border-emerald-900 bg-emerald-50/60 dark:bg-emerald-950/20"
                    : "border-red-200 dark:border-red-900 bg-red-50/60 dark:bg-red-950/20"
                }`}
              >
                {c.positive ? (
                  <Check className="w-4 h-4 text-emerald-600 shrink-0" />
                ) : (
                  <AlertTriangle className="w-4 h-4 text-red-600 shrink-0" />
                )}
                <span>{c.label}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {analysis.summary && (
        <div className="mt-5 rounded-2xl bg-muted/50 border border-border p-4 text-sm text-muted-foreground">
          {analysis.summary}
        </div>
      )}
    </div>
  );
}

function MiniStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-border bg-background/60 p-3">
      <div className="text-[10px] uppercase tracking-wider text-muted-foreground">{label}</div>
      <div className="font-display font-bold text-base mt-0.5">{value}</div>
    </div>
  );
}

function PlanningScoreCard({ score, tier }: { score: number; tier: string }) {
  const [display, setDisplay] = useState(0);
  useEffect(() => {
    const start = performance.now();
    const dur = 1200;
    let raf = 0;
    const tick = (t: number) => {
      const p = Math.min(1, (t - start) / dur);
      const eased = 1 - Math.pow(1 - p, 3);
      setDisplay(Math.round(eased * score));
      if (p < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [score]);

  const R = 54;
  const C = 2 * Math.PI * R;
  const offset = C - (display / 100) * C;
  const color =
    score >= 95 ? "#059669" :
    score >= 80 ? "#2563eb" :
    score >= 65 ? "#d97706" : "#dc2626";

  return (
    <div className="rounded-3xl bg-card border border-border p-6 md:p-8 flex flex-col items-center text-center">
      <div className="text-xs uppercase tracking-wider text-muted-foreground">Construction Planning Score</div>
      <div className="relative mt-4 w-40 h-40">
        <svg viewBox="0 0 128 128" className="w-full h-full -rotate-90">
          <circle cx="64" cy="64" r={R} fill="none" stroke="var(--muted)" strokeWidth="12" />
          <circle
            cx="64" cy="64" r={R} fill="none" stroke={color} strokeWidth="12"
            strokeLinecap="round" strokeDasharray={C} strokeDashoffset={offset}
            style={{ transition: "stroke-dashoffset 60ms linear" }}
          />
        </svg>
        <div className="absolute inset-0 grid place-items-center">
          <div>
            <div className="font-display text-4xl font-extrabold" style={{ color }}>{display}</div>
            <div className="text-xs text-muted-foreground">out of 100</div>
          </div>
        </div>
      </div>
      <div className="mt-3 font-display font-bold text-lg" style={{ color }}>{tier}</div>
      <div className="mt-1 text-xs text-muted-foreground max-w-xs">Composite of budget sufficiency, area efficiency, floor count, quality and add-on balance.</div>
    </div>
  );
}

const REC_ICON_MAP: Record<string, React.ComponentType<{ className?: string }>> = {
  AlertTriangle, Ruler, Building, Sun, Car, ChefHat, Grid3x3, Award, Home, Clock,
  PartyPopper, Wallet, Fence, Cctv, Cpu, Layers, Droplet, CheckCircle2,
  TrendingUp, Users,
};

function SmartRecList({ recs }: { recs: SmartRec[] }) {
  const [filter, setFilter] = useState<"all" | "warning" | "optimization" | "upgrade" | "positive" | "risk">("all");
  const filtered = filter === "all" ? recs : recs.filter(r => r.category === filter);
  const counts = {
    all: recs.length,
    warning: recs.filter(r => r.category === "warning").length,
    optimization: recs.filter(r => r.category === "optimization").length,
    upgrade: recs.filter(r => r.category === "upgrade").length,
    positive: recs.filter(r => r.category === "positive").length,
    risk: recs.filter(r => r.category === "risk").length,
  };
  const tabs: { key: typeof filter; label: string }[] = [
    { key: "all", label: "All" },
    { key: "warning", label: "Warnings" },
    { key: "optimization", label: "Optimizations" },
    { key: "upgrade", label: "Upgrades" },
    { key: "positive", label: "Positive" },
    { key: "risk", label: "Risks" },
  ];
  return (
    <>
      <div className="flex flex-wrap gap-2 mt-5 mb-5">
        {tabs.map(t => (
          <button
            key={t.key}
            onClick={() => setFilter(t.key)}
            className={`inline-flex items-center gap-1.5 rounded-full px-3.5 py-1.5 text-xs font-semibold border transition ${filter === t.key ? "bg-primary text-primary-foreground border-primary shadow-sm" : "bg-card text-muted-foreground border-border hover:text-foreground hover:border-primary/40"}`}
          >
            {t.label}
            <span className={`rounded-full px-1.5 py-0.5 text-[10px] ${filter === t.key ? "bg-white/20" : "bg-muted"}`}>{counts[t.key]}</span>
          </button>
        ))}
      </div>
      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filtered.map((r, idx) => (
          <SmartRecCard key={r.id} rec={r} delay={idx * 60} />
        ))}
      </div>
    </>
  );
}

const CATEGORY_STYLES: Record<RecCategory, { border: string; iconBg: string; iconFg: string; badge: string; ring: string }> = {
  warning:      { border: "border-red-500/30 hover:border-red-500/60",     iconBg: "bg-red-500/10",     iconFg: "text-red-600",     badge: "bg-red-500/10 text-red-700 border-red-500/20",         ring: "ring-red-500/10" },
  optimization: { border: "border-amber-500/30 hover:border-amber-500/60", iconBg: "bg-amber-500/10",   iconFg: "text-amber-600",   badge: "bg-amber-500/10 text-amber-700 border-amber-500/20",   ring: "ring-amber-500/10" },
  upgrade:      { border: "border-blue-500/30 hover:border-blue-500/60",   iconBg: "bg-blue-500/10",    iconFg: "text-blue-600",    badge: "bg-blue-500/10 text-blue-700 border-blue-500/20",       ring: "ring-blue-500/10" },
  positive:     { border: "border-emerald-500/30 hover:border-emerald-500/60", iconBg: "bg-emerald-500/10", iconFg: "text-emerald-600", badge: "bg-emerald-500/10 text-emerald-700 border-emerald-500/20", ring: "ring-emerald-500/10" },
  insight:      { border: "border-sky-500/30 hover:border-sky-500/60",     iconBg: "bg-sky-500/10",     iconFg: "text-sky-600",     badge: "bg-sky-500/10 text-sky-700 border-sky-500/20",         ring: "ring-sky-500/10" },
  risk:         { border: "border-slate-400/40 hover:border-slate-500/60", iconBg: "bg-slate-500/10",   iconFg: "text-slate-700",   badge: "bg-slate-500/10 text-slate-700 border-slate-500/20",   ring: "ring-slate-500/10" },
};

type RecCategory = SmartRec["category"];

function SmartRecCard({ rec, delay }: { rec: SmartRec; delay: number }) {
  const Icon = REC_ICON_MAP[rec.icon] ?? Lightbulb;
  const s = CATEGORY_STYLES[rec.category];
  const [open, setOpen] = useState(false);
  const [visible, setVisible] = useState(false);
  useEffect(() => {
    const t = setTimeout(() => setVisible(true), delay);
    return () => clearTimeout(t);
  }, [delay]);

  const priorityStyle =
    rec.priority === "High"   ? "bg-red-500/10 text-red-700 border-red-500/20" :
    rec.priority === "Medium" ? "bg-amber-500/10 text-amber-700 border-amber-500/20" :
                                "bg-slate-500/10 text-slate-700 border-slate-500/20";

  return (
    <div
      className={`group rounded-3xl bg-card border ${s.border} p-5 transition-all duration-500 hover:-translate-y-1 hover:shadow-xl ${visible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-3"}`}
    >
      <div className="flex items-start gap-3">
        <div className={`shrink-0 w-11 h-11 rounded-2xl ${s.iconBg} ${s.iconFg} grid place-items-center ring-8 ${s.ring}`}>
          <Icon className="w-5 h-5" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-1.5 mb-1.5">
            <span className={`text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full border ${s.badge}`}>{rec.badge}</span>
            <span className={`text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full border ${priorityStyle}`}>{rec.priority}</span>
          </div>
          <div className="font-display font-bold text-[15px] leading-snug">{rec.title}</div>
        </div>
      </div>
      <p className={`text-sm text-muted-foreground mt-3 ${open ? "" : "line-clamp-2"}`}>{rec.description}</p>
      <div className="mt-4 flex items-center justify-between">
        <div className={`inline-flex items-center gap-1.5 text-xs font-semibold ${s.iconFg}`}>
          <IndianRupee className="w-3.5 h-3.5" /> {rec.impact}
        </div>
        <button onClick={() => setOpen(o => !o)} className="text-xs text-muted-foreground hover:text-foreground inline-flex items-center gap-1">
          {open ? "Less" : "More"} <ChevronDown className={`w-3.5 h-3.5 transition ${open ? "rotate-180" : ""}`} />
        </button>
      </div>
    </div>
  );
}

/* ---------------- PDF report ---------------- */
type ReportData = {
  inputs: Inputs;
  est: ReturnType<typeof computeEstimate>;
  stages: ReturnType<typeof stageBreakdown>;
  budget: ReturnType<typeof budgetAnalysis>;
  hs: number;
  category: string;
  plan: { score: number; tier: string };
  insight: { label: string; desc: string };
  recs: SmartRec[];
};

function generateReportPdf(d: ReportData) {
  const doc = new jsPDF({ unit: "pt", format: "a4" });
  const W = doc.internal.pageSize.getWidth();
  const H = doc.internal.pageSize.getHeight();
  const M = 40;
  let y = M;

  const line = (h = 14) => { y += h; if (y > H - M) { doc.addPage(); y = M; } };
  const text = (s: string, size = 11, bold = false, color: [number, number, number] = [30, 41, 59]) => {
    doc.setFont("helvetica", bold ? "bold" : "normal");
    doc.setFontSize(size);
    doc.setTextColor(...color);
    const lines = doc.splitTextToSize(s, W - M * 2);
    for (const ln of lines) {
      if (y > H - M) { doc.addPage(); y = M; }
      doc.text(ln, M, y);
      y += size * 1.25;
    }
  };
  const kv = (k: string, v: string) => {
    if (y > H - M) { doc.addPage(); y = M; }
    doc.setFont("helvetica", "normal"); doc.setFontSize(11); doc.setTextColor(100, 116, 139);
    doc.text(k, M, y);
    doc.setFont("helvetica", "bold"); doc.setTextColor(15, 23, 42);
    doc.text(v, W - M, y, { align: "right" });
    y += 16;
  };
  const rule = () => {
    if (y > H - M) { doc.addPage(); y = M; }
    doc.setDrawColor(226, 232, 240); doc.line(M, y, W - M, y); y += 12;
  };
  const heading = (s: string) => { line(6); text(s, 14, true, [37, 99, 235]); rule(); };

  // Header band
  doc.setFillColor(37, 99, 235);
  doc.rect(0, 0, W, 80, "F");
  doc.setTextColor(255, 255, 255);
  doc.setFont("helvetica", "bold"); doc.setFontSize(20);
  doc.text("Kerala Home Cost Estimator", M, 40);
  doc.setFont("helvetica", "normal"); doc.setFontSize(11);
  doc.text("Smart House Construction Planning Report", M, 60);
  doc.setFontSize(9);
  doc.text(new Date().toLocaleString("en-IN"), W - M, 40, { align: "right" });
  y = 110;

  // Summary
  text(`${d.category} · ${inr(d.est.total)}`, 18, true, [15, 23, 42]);
  text(`${d.inputs.district} · ${d.inputs.builtUpArea} sqft · ${d.inputs.bedrooms} BHK · ${d.inputs.floors} floor(s)`, 11, false, [100, 116, 139]);

  heading("Cost Summary");
  kv("Estimated Total Cost", inr(d.est.total));
  kv("Expected Range", `${inr(d.est.low)} – ${inr(d.est.high)}`);
  kv("Cost per sqft", inr(d.est.perSqft));
  kv("Base Construction", inr(d.est.base));
  kv("Add-ons Total", inr(d.est.addons));
  kv("Construction Duration", `${d.est.months - 1}–${d.est.months + 1} months`);
  kv("Model Accuracy", `${Math.round(d.est.model_accuracy * 100)}%  (R² ${d.est.r2})`);

  heading("Budget Analysis");
  kv("Available Budget", inr(d.inputs.budget));
  kv("Predicted Cost", inr(d.est.total));
  kv(d.budget.diff >= 0 ? "Surplus" : "Deficit", inr(Math.abs(d.budget.diff)));
  kv("Utilization", `${d.budget.utilization}%`);
  kv("Status", d.budget.status === "within" ? "Within Budget" : d.budget.status === "tight" ? "Tight" : "Short");

  heading("Planning Score");
  kv("Construction Planning Score", `${d.plan.score} / 100`);
  kv("Planning Tier", d.plan.tier);
  kv("Health Score", `${d.hs} / 100`);
  kv("House Category", d.insight.label);
  text(d.insight.desc, 10, false, [100, 116, 139]);

  heading("Stage-wise Cost Breakdown");
  d.stages.forEach(s => {
    kv(`${s.label} (${Math.round(s.pct * 100)}%)`, inr(s.cost));
  });

  heading("Configuration");
  kv("District", d.inputs.district);
  kv("Built-up Area", `${d.inputs.builtUpArea} sqft`);
  kv("Plot Size", `${d.inputs.plotSize} cents`);
  kv("Bedrooms / Bathrooms", `${d.inputs.bedrooms} / ${d.inputs.bathrooms}`);
  kv("Floors", String(d.inputs.floors));
  kv("Parking / Balconies", `${d.inputs.parking} / ${d.inputs.balconies}`);
  kv("Kitchen", d.inputs.kitchen);
  kv("Quality", d.inputs.quality);
  kv("Roof", d.inputs.roof);
  kv("Flooring", d.inputs.flooring);
  if (d.inputs.addons.length) {
    kv("Add-ons", d.inputs.addons.map(k => ADDONS.find(a => a.key === k)?.label).filter(Boolean).join(", "));
  }

  heading("Smart Recommendations");
  d.recs.forEach(r => {
    if (y > H - M - 40) { doc.addPage(); y = M; }
    text(`[${r.priority}] ${r.badge} — ${r.title}`, 11, true, [15, 23, 42]);
    text(r.description, 10, false, [71, 85, 105]);
    text(`Impact: ${r.impact}`, 10, true, [37, 99, 235]);
    line(4);
  });

  // Footer on last page
  doc.setFontSize(9);
  doc.setTextColor(148, 163, 184);
  doc.text("Generated by Kerala Home Cost Estimator · For planning reference only.", M, H - 20);

  doc.save(`construction-estimate-${d.inputs.district}-${Date.now()}.pdf`);
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
