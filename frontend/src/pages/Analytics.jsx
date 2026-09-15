import React, { useEffect, useState } from "react";
import {
  Chart as ChartJS, CategoryScale, LinearScale, BarElement, PointElement,
  LineElement, ArcElement, Title, Tooltip, Legend,
} from "chart.js";
import { Bar, Doughnut, Line, Pie } from "react-chartjs-2";
import Spinner from "../components/Spinner.jsx";
import API from "../api/axios.js";

ChartJS.register(CategoryScale, LinearScale, BarElement, PointElement, LineElement, ArcElement, Title, Tooltip, Legend);

const COLORS = ["#8b5cf6","#a78bfa","#c4b5fd","#7c3aed","#6d28d9","#4c1d95","#ddd6fe","#ede9fe"];

const barOpts = {
  responsive: true,
  plugins: { legend: { display: false } },
  scales: { x: { grid: { display: false } }, y: { grid: { color: "#f1f5f9" }, beginAtZero: true } },
};

const donutOpts = {
  responsive: true,
  plugins: { legend: { position: "bottom", labels: { usePointStyle: true, padding: 12, font: { size: 11 } } } },
};

function ChartCard({ title, children }) {
  return (
    <div className="card">
      <h3 className="font-semibold text-gray-700 mb-4">{title}</h3>
      {children}
    </div>
  );
}

export default function Analytics() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [ops, setOps] = useState(null);
  const [opsError, setOpsError] = useState(false);

  useEffect(() => {
    Promise.allSettled([API.get("/analytics"), API.get("/analytics/operations"), API.get("/analytics/venue"), API.get("/analytics/speaker"), API.get("/analytics/sessions")])
      .then(([legacy, operations, venue, speaker, sessions]) => {
        if (legacy.status === "fulfilled") setData(legacy.value.data);
        if (operations.status === "fulfilled") setOps({ operations: operations.value.data, venue: venue.status === "fulfilled" ? venue.value.data : null, speaker: speaker.status === "fulfilled" ? speaker.value.data : null, sessions: sessions.status === "fulfilled" ? sessions.value.data : null });
        else setOpsError(true);
      }).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="flex items-center justify-center h-64"><Spinner size="lg" /></div>;
  if (!data && !ops) return <div className="text-center text-gray-400 mt-10">Failed to load analytics.</div>;

  const total = data?.total || 1; // avoid division by zero
  const checkinPct = Math.round(((data?.checked_in || 0) / total) * 100);

  const mkBar = (labelMap) => ({
    labels: Object.keys(labelMap),
    datasets: [{ data: Object.values(labelMap), backgroundColor: COLORS, borderRadius: 8 }],
  });

  const mkPie = (labelMap) => ({
    labels: Object.keys(labelMap),
    datasets: [{ data: Object.values(labelMap), backgroundColor: COLORS, borderWidth: 0 }],
  });

  const trendData = {
    labels: (data?.trend || []).map((t) => t.date),
    datasets: [{
      label: "Registrations",
       data: (data?.trend || []).map((t) => t.count),
      borderColor: "#7c3aed",
      backgroundColor: "rgba(139,92,246,0.12)",
      fill: true, tension: 0.4, pointRadius: 5,
    }],
  };

   const checkinTrendData = (data?.checkin_trend || []).length > 0 ? {
     labels: data.checkin_trend.map((t) => t.date),
    datasets: [{
      label: "Check-Ins",
      data: data.checkin_trend.map((t) => t.count),
      borderColor: "#10b981",
      backgroundColor: "rgba(16,185,129,0.12)",
      fill: true, tension: 0.4, pointRadius: 5,
    }],
  } : null;

  const collegeBars = {
     labels: (data?.top_colleges || []).map((c) => c.college),
     datasets: [{ label: "Attendees", data: (data?.top_colleges || []).map((c) => c.count), backgroundColor: COLORS, borderRadius: 8 }],
  };

  return (
    <div className="space-y-4">
      {ops && <OperationsAnalytics ops={ops} error={opsError} />}
      {!data && ops && <div className="card text-sm text-gray-500">Registration analytics are not available yet. Operations reporting is active.</div>}
      {data && <>
      {/* Summary row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {[
          { label: "Total Registrations", value: data.total, color: "text-violet-700" },
          { label: "Checked In", value: data.checked_in, color: "text-emerald-600" },
          { label: "Pending Check-In", value: data.pending, color: "text-amber-600" },
          { label: "Check-In Rate", value: `${checkinPct}%`, color: "text-blue-600" },
        ].map(({ label, value, color }) => (
          <div key={label} className="card text-center">
            <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">{label}</p>
            <p className={`text-2xl font-bold ${color}`}>{value}</p>
          </div>
        ))}
      </div>

      {/* Check-in Percentage Arc */}
      <div className="card">
        <h3 className="font-semibold text-gray-700 mb-3">Check-In Percentage</h3>
        <div className="flex items-center gap-6">
          <div className="relative w-28 h-28 flex-shrink-0">
            <svg viewBox="0 0 36 36" className="w-28 h-28 -rotate-90">
              <circle cx="18" cy="18" r="15.915" fill="none" stroke="#ede9fe" strokeWidth="3" />
              <circle
                cx="18" cy="18" r="15.915" fill="none"
                stroke="#7c3aed" strokeWidth="3"
                strokeDasharray={`${checkinPct} ${100 - checkinPct}`}
                strokeLinecap="round"
              />
            </svg>
            <span className="absolute inset-0 flex items-center justify-center text-xl font-bold text-violet-700">{checkinPct}%</span>
          </div>
          <div>
            <p className="text-gray-600 text-sm">{data.checked_in} out of {data.total} registered attendees have checked in.</p>
            {data.pending > 0 && <p className="text-amber-600 text-sm mt-1">{data.pending} still pending check-in.</p>}
          </div>
        </div>
      </div>

      {/* Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <ChartCard title="Registration Trend (Last 7 Days)">
          {data.trend.length ? <Line data={trendData} options={{ ...barOpts, plugins: { legend: { display: false } } }} /> : <p className="text-gray-400 text-sm">No trend data.</p>}
        </ChartCard>
        <ChartCard title="Gender Distribution">
          {Object.keys(data.gender_dist).length ? <Doughnut data={mkPie(data.gender_dist)} options={donutOpts} /> : <p className="text-gray-400 text-sm">No data.</p>}
        </ChartCard>
      </div>

      {/* Row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <ChartCard title="Age Distribution">
          {Object.keys(data.age_dist).length ? <Bar data={mkBar(data.age_dist)} options={barOpts} /> : <p className="text-gray-400 text-sm">No data.</p>}
        </ChartCard>
        <ChartCard title="Department Distribution">
          {Object.keys(data.dept_dist).length ? <Pie data={mkPie(data.dept_dist)} options={donutOpts} /> : <p className="text-gray-400 text-sm">No data.</p>}
        </ChartCard>
      </div>

      {/* Row 3 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <ChartCard title="Top Colleges">
          {data.top_colleges.length ? <Bar data={collegeBars} options={{ ...barOpts, indexAxis: "y" }} /> : <p className="text-gray-400 text-sm">No data.</p>}
        </ChartCard>
        <ChartCard title="Check-In Trend">
          {checkinTrendData ? <Line data={checkinTrendData} options={{ ...barOpts, plugins: { legend: { display: false } } }} /> : <p className="text-gray-400 text-sm">No check-ins recorded yet.</p>}
        </ChartCard>
      </div>

      {/* Food Preference */}
      {Object.keys(data.food_dist).length > 0 && (
        <ChartCard title="Food Preference Distribution">
          <div className="max-w-sm mx-auto">
            <Doughnut data={mkPie(data.food_dist)} options={donutOpts} />
          </div>
        </ChartCard>
      )}
      </>}
    </div>
  );
}

function OperationsAnalytics({ ops, error }) {
  const root = ops.operations || {};
  const summary = root.summary || root;
  const list = (obj, keys) => { for (const key of keys) if (Array.isArray(obj?.[key])) return obj[key]; return []; };
  const venues = list(ops.venue, ["venues", "data"]);
  const speakers = list(ops.speaker, ["speakers", "data"]);
  const sessions = list(ops.sessions, ["sessions", "data"]);
  const value = (obj, keys, fallback = "—") => { for (const k of keys) if (obj?.[k] !== undefined && obj?.[k] !== null) return obj[k]; return fallback; };
  return <section className="space-y-4">
    <div className="flex items-end justify-between"><div><p className="text-xs font-bold uppercase tracking-widest text-violet-500">Milestone 2</p><h2 className="text-2xl font-bold text-gray-800 mt-1">Operations pulse</h2><p className="text-sm text-gray-500">Capacity, workload and schedule health at a glance.</p></div>{error && <span className="text-xs text-amber-600">Some operation feeds unavailable</span>}</div>
    <div className="grid grid-cols-2 lg:grid-cols-6 gap-4">{[["Avg. utilization",`${value(summary,["average_venue_utilization"],0)}%`],["Planned attendees",value(summary,["planned_attendees"],0)],["Speakers",value(summary,["total_speakers"],0)],["Confirmed sessions",value(summary,["confirmed_sessions"],0)],["Venues",value(summary,["total_venues"],0)],["Conflicts",value(summary,["scheduling_conflicts"],0)]].map(([l,v])=><div className="card" key={l}><p className="text-xs uppercase tracking-wide text-gray-400">{l}</p><p className="text-2xl font-bold text-violet-700 mt-2">{v}</p></div>)}</div>
    <div className="grid lg:grid-cols-2 gap-4"><ChartCard title="Venue performance">{venues.length?<Bar data={{labels:venues.map(v=>value(v,["name","venue_name"])),datasets:[{label:"Utilization",data:venues.map(v=>Number(value(v,["utilization","utilization_rate"],0))),backgroundColor:"#8b5cf6",borderRadius:8}]}} options={barOpts}/>:<p className="text-sm text-gray-400">No venue performance data.</p>}</ChartCard><ChartCard title="Speaker workload">{speakers.length?<Bar data={{labels:speakers.map(s=>value(s,["name","full_name"])),datasets:[{label:"Scheduled hours",data:speakers.map(s=>Number(value(s,["scheduled_hours"],0))),backgroundColor:"#14b8a6",borderRadius:8}]}} options={barOpts}/>:<p className="text-sm text-gray-400">No speaker workload data.</p>}</ChartCard></div>
    <div className="card overflow-hidden"><h3 className="font-semibold text-gray-700 mb-4">Session operations</h3>{sessions.length?<div className="overflow-x-auto"><table className="w-full text-sm"><thead><tr className="text-left text-xs uppercase tracking-wide text-gray-400 border-b"><th className="pb-3">Session</th><th className="pb-3">Speaker</th><th className="pb-3">Venue</th><th className="pb-3">Attendees</th><th className="pb-3">Duration</th><th className="pb-3">Status</th></tr></thead><tbody>{sessions.map((s,i)=><tr key={s.id||i} className="border-b last:border-0"><td className="py-3 font-medium">{value(s,["title","name"])}</td><td className="py-3">{value(s.speaker,["name"],"Unassigned")}</td><td className="py-3">{value(s.venue,["name"],"Unassigned")}</td><td className="py-3">{value(s,["expected_attendees"],0)}</td><td className="py-3">{value(s,["duration_hours"],0)}h</td><td className="py-3"><span className="badge bg-violet-100 text-violet-700">{value(s,["computed_status","status"],"Scheduled")}</span></td></tr>)}</tbody></table></div>:<p className="text-sm text-gray-400">No session analytics available.</p>}</div>
  </section>;
}
