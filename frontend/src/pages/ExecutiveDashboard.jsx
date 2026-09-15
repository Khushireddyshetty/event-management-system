import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  MdAutoAwesome, MdBusiness, MdCheckCircle, MdFactCheck, MdGroups,
  MdInsights, MdPeople, MdPlayArrow, MdRefresh, MdReportProblem,
  MdSchedule, MdSecurity, MdWarning,
} from "react-icons/md";
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend } from "chart.js";
import { Line } from "react-chartjs-2";
import API from "../api/axios.js";
import Spinner from "../components/Spinner.jsx";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend);

const money = (value) => `₹${Number(value || 0).toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;
const riskStyles = {
  Critical: "bg-red-100 text-red-700 border-red-200",
  High: "bg-orange-100 text-orange-700 border-orange-200",
  Medium: "bg-amber-100 text-amber-700 border-amber-200",
  Low: "bg-slate-100 text-slate-600 border-slate-200",
};
const healthStyles = {
  Healthy: "bg-emerald-50 text-emerald-700 border-emerald-200",
  Moderate: "bg-amber-50 text-amber-700 border-amber-200",
  "At Risk": "bg-orange-50 text-orange-700 border-orange-200",
  Critical: "bg-red-50 text-red-700 border-red-200",
};

function Metric({ label, value, detail, icon: Icon, tone = "violet" }) {
  const tones = {
    violet: "bg-violet-50 text-violet-600", blue: "bg-blue-50 text-blue-600",
    emerald: "bg-emerald-50 text-emerald-600", amber: "bg-amber-50 text-amber-600",
    rose: "bg-rose-50 text-rose-600", indigo: "bg-indigo-50 text-indigo-600",
  };
  return (
    <div className="card flex items-start gap-3">
      <div className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 ${tones[tone]}`}>
        <Icon className="text-xl" />
      </div>
      <div className="min-w-0">
        <p className="text-[11px] font-semibold tracking-wide uppercase text-gray-400 truncate">{label}</p>
        <p className="text-xl font-bold text-gray-800 mt-0.5">{value}</p>
        {detail && <p className="text-xs text-gray-400 mt-0.5">{detail}</p>}
      </div>
    </div>
  );
}

function SectionTitle({ eyebrow, title, action }) {
  return (
    <div className="flex items-end justify-between gap-3 mb-4">
      <div>
        {eyebrow && <p className="text-[11px] uppercase tracking-[0.16em] font-bold text-violet-500">{eyebrow}</p>}
        <h2 className="text-base font-bold text-gray-800 mt-1">{title}</h2>
      </div>
      {action}
    </div>
  );
}

export default function ExecutiveDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [working, setWorking] = useState(false);
  const [error, setError] = useState("");
  const [updated, setUpdated] = useState(null);

  const load = useCallback(async (showSpinner = true) => {
    if (showSpinner) setLoading(true);
    setError("");
    try {
      const response = await API.get("/intelligence/overview");
      setData(response.data);
      setUpdated(new Date());
    } catch (err) {
      setError(err.message || "Unable to load intelligence data.");
    } finally {
      if (showSpinner) setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    const timer = window.setInterval(() => load(false), 30000);
    return () => window.clearInterval(timer);
  }, [load]);

  const runAnalysis = async () => {
    setWorking(true);
    setError("");
    try {
      const response = await API.post("/orchestrator/analyze");
      setData(response.data);
      setUpdated(new Date());
    } catch (err) {
      setError(err.message || "Analysis could not be completed.");
    } finally {
      setWorking(false);
    }
  };

  const chart = useMemo(() => ({
    labels: (data?.trends || []).map((item) => item.date),
    datasets: [
      { label: "Registrations", data: (data?.trends || []).map((item) => item.registrations), borderColor: "#7c3aed", backgroundColor: "rgba(124,58,237,.08)", fill: true, tension: .4 },
      { label: "Check-ins", data: (data?.trends || []).map((item) => item.checkins), borderColor: "#10b981", backgroundColor: "transparent", tension: .4 },
    ],
  }), [data]);

  if (loading) return <div className="h-64 flex items-center justify-center"><Spinner size="lg" /></div>;
  if (error && !data) return <div className="card max-w-xl mx-auto mt-10 text-center"><MdWarning className="mx-auto text-4xl text-amber-500 mb-2" /><p className="font-semibold text-gray-700">Intelligence data is unavailable</p><p className="text-sm text-gray-500 mt-1">{error}</p><button onClick={() => load()} className="btn-primary mt-4">Try again</button></div>;
  if (!data) return null;

  const o = data.kpis?.overview || {};
  const v = data.kpis?.venue || {};
  const s = data.kpis?.speaker || {};
  const i = data.kpis?.incidents || {};
  const sp = data.kpis?.sponsors || {};
  const health = Math.max(0, Math.min(100, Number(data.event_health || 0)));

  return (
    <div className="space-y-6 max-w-[1500px] mx-auto">
      <div className="rounded-3xl bg-gradient-to-br from-violet-700 via-purple-700 to-indigo-800 text-white p-6 md:p-8 shadow-xl overflow-hidden relative">
        <div className="absolute -right-16 -top-20 w-64 h-64 rounded-full bg-white/10" />
        <div className="relative flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div>
            <div className="flex items-center gap-2 text-violet-200 text-xs font-bold uppercase tracking-[.18em]"><MdBusiness /> Leadership view</div>
            <h1 className="text-2xl md:text-3xl font-bold mt-3">Executive Dashboard</h1>
            <p className="text-violet-100/80 text-sm mt-2 max-w-2xl">A live decision-support view built from registrations, operations, sponsorships, incidents, and schedule data.</p>
            <div className="flex flex-wrap items-center gap-3 mt-5">
              <button onClick={runAnalysis} disabled={working} className="bg-white text-violet-700 hover:bg-violet-50 font-semibold px-4 py-2.5 rounded-xl text-sm flex items-center gap-2 disabled:opacity-70">
                <MdPlayArrow className="text-lg" /> {working ? "Analyzing…" : "Run analysis"}
              </button>
              <Link to="/intelligence" className="text-white/90 hover:text-white border border-white/25 hover:bg-white/10 px-4 py-2.5 rounded-xl text-sm font-medium">Open Intelligence Center</Link>
            </div>
          </div>
          <div className="flex items-center gap-5 bg-black/10 rounded-2xl p-4 min-w-[245px]">
            <div className="relative w-28 h-28 rounded-full flex items-center justify-center" style={{ background: `conic-gradient(#a7f3d0 ${health * 3.6}deg, rgba(255,255,255,.16) 0deg)` }}>
              <div className="w-20 h-20 rounded-full bg-indigo-800 flex flex-col items-center justify-center"><span className="text-2xl font-bold">{health}</span><span className="text-[10px] text-violet-200">/ 100</span></div>
            </div>
            <div><p className="text-xs text-violet-200 uppercase tracking-wide font-semibold">Event health</p><p className="text-xl font-bold mt-1">{data.health_status}</p><p className="text-xs text-violet-200/80 mt-2 leading-relaxed">Updated {updated ? updated.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : "now"} · auto-refresh 30s</p></div>
          </div>
        </div>
      </div>

      {error && <div className="rounded-xl bg-amber-50 border border-amber-200 text-amber-800 px-4 py-3 text-sm flex items-center gap-2"><MdWarning /> {error}</div>}

      <section>
        <SectionTitle eyebrow="At a glance" title="Event overview" action={<button onClick={() => load()} className="btn-secondary text-xs py-2 px-3 flex items-center gap-1"><MdRefresh /> Refresh</button>} />
        <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-3">
          <Metric label="Registrations" value={o.total_registrations} detail={`${o.pending_registrations || 0} awaiting check-in`} icon={MdPeople} />
          <Metric label="Confirmed attendees" value={o.confirmed_attendees} detail={`${o.attendance_rate || 0}% attendance`} icon={MdGroups} tone="blue" />
          <Metric label="Check-ins" value={o.checked_in} detail="live count" icon={MdFactCheck} tone="emerald" />
          <Metric label="Event completion" value={`${o.event_completion || 0}%`} detail={`${o.sessions_remaining || 0} sessions remaining`} icon={MdSchedule} tone="indigo" />
          <Metric label="Active sponsors" value={sp.active || 0} detail={money(sp.revenue)} icon={MdBusiness} tone="amber" />
          <Metric label="Open incidents" value={i.open || 0} detail={`${i.critical || 0} critical`} icon={MdReportProblem} tone="rose" />
        </div>
      </section>

      <div className="grid grid-cols-1 xl:grid-cols-5 gap-4">
        <div className="card xl:col-span-3">
          <SectionTitle eyebrow="Momentum" title="Registration and check-in trend" />
          {chart.labels.length ? <Line data={chart} options={{ responsive: true, plugins: { legend: { position: "bottom", labels: { usePointStyle: true, padding: 18 } } }, scales: { x: { grid: { display: false } }, y: { beginAtZero: true, grid: { color: "#f1f5f9" } } } }} /> : <div className="h-48 flex items-center justify-center text-sm text-gray-400">No trend data available</div>}
        </div>
        <div className="card xl:col-span-2">
          <SectionTitle eyebrow="Decision support" title="Current event readout" />
          <p className="text-sm text-gray-600 leading-6">{data.summary}</p>
          <div className={`mt-4 rounded-xl border px-4 py-3 text-sm font-medium ${healthStyles[data.health_status] || healthStyles.Critical}`}>{data.health_status === "Healthy" ? "The operating picture is stable." : "Review the priority items below before the next checkpoint."}</div>
          <div className="grid grid-cols-2 gap-3 mt-5">
            <div className="rounded-xl bg-gray-50 p-3"><p className="text-xs text-gray-400">Capacity utilization</p><p className="text-lg font-bold text-gray-800 mt-1">{v.capacity_utilization || 0}%</p></div>
            <div className="rounded-xl bg-gray-50 p-3"><p className="text-xs text-gray-400">Active alerts</p><p className="text-lg font-bold text-gray-800 mt-1">{data.kpis?.operations?.active_alerts || 0}</p></div>
            <div className="rounded-xl bg-gray-50 p-3"><p className="text-xs text-gray-400">Sessions conducted</p><p className="text-lg font-bold text-gray-800 mt-1">{o.sessions_conducted || 0}</p></div>
            <div className="rounded-xl bg-gray-50 p-3"><p className="text-xs text-gray-400">Speaker participation</p><p className="text-lg font-bold text-gray-800 mt-1">{s.participation || 0}%</p></div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="card"><SectionTitle eyebrow="Operations" title="Venue status" /><div className="space-y-3"><div className="flex justify-between text-sm"><span className="text-gray-500">Occupied</span><b>{v.occupied || 0} / {v.total || 0}</b></div><div className="h-2 bg-gray-100 rounded-full overflow-hidden"><div className="h-full bg-violet-500 rounded-full" style={{ width: `${Math.min(100, v.utilization || 0)}%` }} /></div><div className="flex justify-between text-xs text-gray-400"><span>{v.available || 0} available</span><span>{v.capacity_utilization || 0}% capacity used</span></div><div className="pt-3 border-t border-gray-100 flex justify-between text-sm"><span className="text-gray-500">Potential overcrowding</span><span className={`font-semibold ${v.overcrowding_risk ? "text-orange-600" : "text-emerald-600"}`}>{v.overcrowding_risk || 0} venue(s)</span></div></div></div>
        <div className="card"><SectionTitle eyebrow="Partnerships" title="Sponsor performance" /><div className="space-y-4"><div className="flex items-end justify-between"><div><p className="text-3xl font-bold text-gray-800">{money(sp.revenue)}</p><p className="text-xs text-gray-400 mt-1">tracked sponsorship value</p></div><span className="text-emerald-600 bg-emerald-50 px-2 py-1 rounded-lg text-xs font-bold">{sp.average_roi || 0}x avg ROI</span></div><div className="grid grid-cols-2 gap-3 text-sm"><div className="bg-gray-50 rounded-xl p-3"><p className="text-gray-400 text-xs">Performance</p><b className="text-gray-800">{sp.average_performance || 0}/100</b></div><div className="bg-gray-50 rounded-xl p-3"><p className="text-gray-400 text-xs">Pending payments</p><b className="text-gray-800">{sp.pending_payments || 0}</b></div></div></div></div>
        <div className="card"><SectionTitle eyebrow="Reliability" title="Incident posture" /><div className="space-y-3">{[["Open incidents", i.open, "text-gray-800"], ["Critical", i.critical, "text-red-600"], ["Escalated", i.escalated, "text-orange-600"], ["Resolved", i.resolved, "text-emerald-600"]].map(([label, value, color]) => <div key={label} className="flex justify-between items-center text-sm"><span className="text-gray-500">{label}</span><span className={`font-bold ${color}`}>{value || 0}</span></div>)}<div className="pt-3 mt-1 border-t border-gray-100 text-xs text-gray-400 flex items-center gap-1"><MdSecurity /> Priority incidents are included in health score</div></div></div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="card"><SectionTitle eyebrow="Predicted risks" title="What needs attention" action={<Link to="/intelligence" className="text-xs text-violet-600 font-semibold hover:text-violet-800">View all →</Link>} />{data.risks?.length ? <div className="space-y-3">{data.risks.slice(0, 4).map((risk) => <div key={`${risk.title}-${risk.source}`} className="border border-gray-100 rounded-xl p-3.5"><div className="flex items-start gap-3"><span className={`badge border ${riskStyles[risk.severity] || riskStyles.Medium}`}>{risk.severity}</span><div className="min-w-0"><p className="text-sm font-semibold text-gray-800">{risk.title}</p><p className="text-xs text-gray-500 mt-1 leading-5">{risk.description}</p><p className="text-xs text-violet-600 mt-2 font-medium">{risk.recommended_action}</p></div></div></div>)}</div> : <div className="rounded-xl bg-emerald-50 text-emerald-700 p-4 text-sm flex items-center gap-2"><MdCheckCircle /> No material risks detected in this snapshot.</div>}</div>
        <div className="card"><SectionTitle eyebrow="Recommended actions" title="Next best actions" />{data.recommendations?.length ? <div className="space-y-2.5">{data.recommendations.slice(0, 5).map((item, index) => <div key={`${item.recommendation}-${index}`} className="flex gap-3 p-3 rounded-xl hover:bg-gray-50 transition"><div className="w-6 h-6 rounded-lg bg-violet-100 text-violet-700 text-xs font-bold flex items-center justify-center flex-shrink-0">{index + 1}</div><div><p className="text-sm font-semibold text-gray-800">{item.recommendation}</p><p className="text-xs text-gray-500 mt-1">{item.reason}</p><span className="text-[11px] text-gray-400 mt-1 inline-block">{item.related_module} · {item.priority} priority</span></div></div>)}</div> : <p className="text-sm text-gray-400">No recommendations available.</p>}</div>
      </div>
      <p className="text-center text-xs text-gray-400 flex items-center justify-center gap-1"><MdAutoAwesome className="text-violet-400" /> Rule-based intelligence is active; all values are calculated from the current SQLite data.</p>
    </div>
  );
}
