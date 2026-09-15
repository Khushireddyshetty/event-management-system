import React, { useCallback, useEffect, useState } from "react";
import { MdAccessTime, MdAutoAwesome, MdCheckCircle, MdErrorOutline, MdPlayArrow, MdRefresh, MdSmartToy, MdWarning } from "react-icons/md";
import API from "../api/axios.js";
import Spinner from "../components/Spinner.jsx";

const severity = {
  Critical: "bg-red-100 text-red-700 border-red-200",
  High: "bg-orange-100 text-orange-700 border-orange-200",
  Medium: "bg-amber-100 text-amber-700 border-amber-200",
  Low: "bg-slate-100 text-slate-600 border-slate-200",
};

function Empty({ children = "No data available" }) {
  return <div className="rounded-xl border border-dashed border-gray-200 p-6 text-center text-sm text-gray-400">{children}</div>;
}

function Kpi({ label, value, tone = "text-violet-700" }) {
  return <div className="rounded-xl bg-gray-50 p-3"><p className="text-[11px] text-gray-400 uppercase tracking-wide font-semibold">{label}</p><p className={`text-xl font-bold mt-1 ${tone}`}>{value}</p></div>;
}

export default function Intelligence() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [working, setWorking] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const response = await API.get("/intelligence/latest");
      setData(response.data);
    } catch (err) {
      setError(err.message || "Unable to load the intelligence center.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const runAnalysis = async () => {
    setWorking(true);
    setError("");
    try {
      const response = await API.post("/intelligence/analyze");
      setData(response.data);
    } catch (err) {
      setError(err.message || "Analysis could not be completed.");
    } finally {
      setWorking(false);
    }
  };

  if (loading) return <div className="h-64 flex items-center justify-center"><Spinner size="lg" /></div>;
  if (!data) return <div className="card text-center max-w-xl mx-auto mt-10"><MdErrorOutline className="mx-auto text-4xl text-red-400" /><p className="mt-2 text-gray-700 font-semibold">Could not load the intelligence center</p><p className="text-sm text-gray-500 mt-1">{error}</p><button onClick={load} className="btn-primary mt-4">Try again</button></div>;

  const k = data.kpis || {};
  const agents = data.agents || [];
  return (
    <div className="space-y-6 max-w-[1500px] mx-auto">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div><div className="flex items-center gap-2 text-violet-600 text-xs font-bold uppercase tracking-[.16em]"><MdAutoAwesome /> Intelligence layer</div><h1 className="text-2xl font-bold text-gray-800 mt-2">Event Intelligence Center</h1><p className="text-sm text-gray-500 mt-2 max-w-3xl">The Event Intelligence Engine analyzes registrations, venues, speakers, sponsors, incidents, operations, and agent outputs to identify risks and recommend actions.</p></div>
        <div className="flex gap-2 flex-shrink-0"><button onClick={load} className="btn-secondary text-sm flex items-center gap-2"><MdRefresh /> Refresh</button><button onClick={runAnalysis} disabled={working} className="btn-primary text-sm flex items-center gap-2 disabled:opacity-70"><MdPlayArrow /> {working ? "Running…" : "Run analysis"}</button></div>
      </div>
      {error && <div className="rounded-xl bg-amber-50 border border-amber-200 text-amber-800 px-4 py-3 text-sm flex items-center gap-2"><MdWarning /> {error}</div>}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="card lg:col-span-1 bg-gradient-to-br from-violet-700 to-indigo-800 text-white">
          <div className="flex items-center justify-between"><div><p className="text-xs uppercase tracking-[.16em] text-violet-200 font-semibold">Event health</p><p className="text-5xl font-bold mt-4">{data.event_health}<span className="text-xl text-violet-200">/100</span></p><span className={`inline-flex mt-4 badge ${data.health_status === "Healthy" ? "bg-emerald-100 text-emerald-700" : data.health_status === "Critical" ? "bg-red-100 text-red-700" : "bg-amber-100 text-amber-700"}`}>{data.health_status}</span></div><div className="w-24 h-24 rounded-full flex items-center justify-center" style={{ background: `conic-gradient(#c4b5fd ${(data.event_health || 0) * 3.6}deg, rgba(255,255,255,.16) 0deg)` }}><div className="w-16 h-16 bg-indigo-800 rounded-full" /></div></div>
          <p className="text-sm text-violet-100/90 mt-6 leading-6">{data.summary}</p><p className="text-xs text-violet-200 mt-5 flex items-center gap-1"><MdAccessTime /> Last analysis: {data.timestamp || "Not yet run"}</p>
        </div>
        <div className="card lg:col-span-2"><div className="flex items-center justify-between mb-4"><div><p className="text-xs uppercase tracking-[.16em] text-violet-500 font-bold">Signals</p><h2 className="font-bold text-gray-800 mt-1">Live KPI snapshot</h2></div><span className="text-xs text-gray-400">Calculated from SQLite</span></div><div className="grid grid-cols-2 md:grid-cols-4 gap-3"><Kpi label="Registrations" value={k.overview?.total_registrations || 0} /><Kpi label="Attendance rate" value={`${k.overview?.attendance_rate || 0}%`} tone="text-emerald-600" /><Kpi label="Venue utilization" value={`${k.venue?.utilization || 0}%`} tone="text-indigo-600" /><Kpi label="Capacity used" value={`${k.venue?.capacity_utilization || 0}%`} tone="text-blue-600" /><Kpi label="Open incidents" value={k.incidents?.open || 0} tone="text-rose-600" /><Kpi label="Active sponsors" value={k.sponsors?.active || 0} tone="text-amber-600" /><Kpi label="Sponsor revenue" value={`₹${Number(k.sponsors?.revenue || 0).toLocaleString("en-IN")}`} tone="text-emerald-600" /><Kpi label="Active alerts" value={k.operations?.active_alerts || 0} tone="text-orange-600" /></div></div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        <div className="card"><div className="flex items-center justify-between mb-4"><div><p className="text-xs uppercase tracking-[.16em] text-red-500 font-bold">Prioritized signal</p><h2 className="font-bold text-gray-800 mt-1">Detected risks</h2></div><span className="badge bg-gray-100 text-gray-600">{data.risks?.length || 0} found</span></div>{data.risks?.length ? <div className="space-y-3">{data.risks.map((risk, index) => <div key={`${risk.title}-${index}`} className="border border-gray-100 rounded-xl p-4"><div className="flex justify-between items-start gap-3"><div><span className={`badge border ${severity[risk.severity] || severity.Medium}`}>{risk.severity}</span><h3 className="font-semibold text-sm text-gray-800 mt-2">{risk.title}</h3></div><span className="text-[11px] text-gray-400">{risk.source}</span></div><p className="text-sm text-gray-500 mt-2 leading-5">{risk.description}</p><div className="mt-3 bg-violet-50 text-violet-700 rounded-lg px-3 py-2 text-xs font-medium">Action: {risk.recommended_action}</div></div>)}</div> : <Empty><MdCheckCircle className="inline text-emerald-500 mr-1" /> No risks detected</Empty>}</div>
        <div className="card"><div className="flex items-center justify-between mb-4"><div><p className="text-xs uppercase tracking-[.16em] text-emerald-600 font-bold">Action queue</p><h2 className="font-bold text-gray-800 mt-1">Recommendations</h2></div></div>{data.recommendations?.length ? <div className="space-y-3">{data.recommendations.map((item, index) => <div key={`${item.recommendation}-${index}`} className="flex gap-3"><span className={`badge border h-fit ${severity[item.priority] || severity.Medium}`}>{item.priority}</span><div className="pb-3 border-b border-gray-100 flex-1"><p className="text-sm font-semibold text-gray-800">{item.recommendation}</p><p className="text-xs text-gray-500 mt-1 leading-5">{item.reason}</p><p className="text-[11px] text-gray-400 mt-1">{item.related_module}</p></div></div>)}</div> : <Empty />}</div>
      </div>

      <div className="card"><div className="flex items-center gap-2 mb-4"><MdSmartToy className="text-xl text-violet-600" /><div><p className="text-xs uppercase tracking-[.16em] text-violet-500 font-bold">Orchestration</p><h2 className="font-bold text-gray-800 mt-1">Agent activity</h2></div></div><div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-3">{agents.length ? agents.map((agent) => <div key={agent.agent_name} className="rounded-xl border border-gray-100 p-4"><div className="flex items-center justify-between gap-2"><p className="font-semibold text-sm text-gray-800">{agent.agent_name}</p><span className={`w-2.5 h-2.5 rounded-full ${agent.status === "attention_required" ? "bg-amber-400" : "bg-emerald-400"}`} /></div><p className="text-xs text-gray-500 mt-2 leading-5">{agent.findings || "No findings returned."}</p><p className="text-[11px] mt-3 font-medium text-gray-400">{agent.status === "attention_required" ? "Attention required" : "Completed"}</p></div>) : <Empty>No agent run recorded yet</Empty>}</div></div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card"><p className="text-xs uppercase tracking-[.16em] text-gray-400 font-bold">Incident management</p><div className="grid grid-cols-2 gap-3 mt-4"><Kpi label="Total" value={k.incidents?.total || 0} /><Kpi label="Critical" value={k.incidents?.critical || 0} tone="text-red-600" /><Kpi label="Escalated" value={k.incidents?.escalated || 0} tone="text-orange-600" /><Kpi label="Resolved" value={k.incidents?.resolved || 0} tone="text-emerald-600" /></div></div>
        <div className="card"><p className="text-xs uppercase tracking-[.16em] text-gray-400 font-bold">Speaker performance</p><div className="grid grid-cols-2 gap-3 mt-4"><Kpi label="Speakers" value={k.speaker?.total || 0} /><Kpi label="Participation" value={`${k.speaker?.participation || 0}%`} tone="text-emerald-600" /><Kpi label="Avg rating" value={k.speaker?.average_rating || 0} tone="text-amber-600" /><Kpi label="Conflicts" value={k.speaker?.schedule_conflicts || 0} tone="text-red-600" /></div></div>
        <div className="card"><p className="text-xs uppercase tracking-[.16em] text-gray-400 font-bold">Trend window</p>{data.trends?.length ? <div className="mt-4 space-y-2">{data.trends.slice(-5).map((item) => <div key={item.date} className="flex items-center justify-between text-sm"><span className="text-gray-500">{item.date}</span><span className="font-semibold text-gray-700">{item.registrations} registrations <span className="text-emerald-600">· {item.checkins} check-ins</span></span></div>)}</div> : <div className="mt-4"><Empty /></div>}</div>
      </div>
      <p className="text-center text-xs text-gray-400">The fallback intelligence engine is deterministic and works without GEMINI_API_KEY.</p>
    </div>
  );
}
