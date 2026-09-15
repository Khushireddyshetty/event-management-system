import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  MdPeople, MdPersonAdd, MdFactCheck, MdPendingActions,
  MdSchool, MdWork, MdRefresh,
} from "react-icons/md";
import {
  Chart as ChartJS, CategoryScale, LinearScale, BarElement, PointElement,
  LineElement, ArcElement, Title, Tooltip, Legend,
} from "chart.js";
import { Bar, Doughnut, Line } from "react-chartjs-2";
import StatCard from "../components/StatCard.jsx";
import Spinner from "../components/Spinner.jsx";
import API from "../api/axios.js";

ChartJS.register(CategoryScale, LinearScale, BarElement, PointElement, LineElement, ArcElement, Title, Tooltip, Legend);

const CHART_COLORS = ["#8b5cf6","#a78bfa","#c4b5fd","#ddd6fe","#7c3aed","#6d28d9","#4c1d95","#ede9fe"];

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    setLoading(true);
    try {
      const res = await API.get("/analytics");
      setData(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  if (loading) return <div className="flex items-center justify-center h-64"><Spinner size="lg" /></div>;
  if (!data) return <div className="text-center text-gray-500 mt-10">Failed to load dashboard data.</div>;

  const trendChart = {
    labels: data.trend.map((t) => t.date),
    datasets: [{
      label: "Registrations",
      data: data.trend.map((t) => t.count),
      borderColor: "#7c3aed",
      backgroundColor: "rgba(139,92,246,0.15)",
      fill: true,
      tension: 0.4,
      pointRadius: 4,
    }],
  };

  const genderChart = {
    labels: Object.keys(data.gender_dist),
    datasets: [{
      data: Object.values(data.gender_dist),
      backgroundColor: CHART_COLORS,
      borderWidth: 0,
    }],
  };

  const ageChart = {
    labels: Object.keys(data.age_dist),
    datasets: [{
      label: "Attendees",
      data: Object.values(data.age_dist),
      backgroundColor: CHART_COLORS,
      borderRadius: 8,
    }],
  };

  const deptChart = {
    labels: Object.keys(data.dept_dist),
    datasets: [{
      label: "Registrations",
      data: Object.values(data.dept_dist),
      backgroundColor: CHART_COLORS,
      borderRadius: 8,
    }],
  };

  const chartOpts = (title) => ({
    responsive: true,
    plugins: { legend: { display: false }, title: { display: false } },
    scales: { x: { grid: { display: false } }, y: { grid: { color: "#f1f5f9" } } },
  });

  const donutOpts = {
    responsive: true,
    plugins: { legend: { position: "bottom", labels: { usePointStyle: true, padding: 16, font: { size: 12 } } } },
  };

  return (
    <div className="space-y-6">
      {/* Stat Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        <StatCard title="Total Registrations" value={data.total}           icon={MdPeople}         color="violet"  />
        <StatCard title="Today's"              value={data.today_registrations} icon={MdPersonAdd}  color="blue"    />
        <StatCard title="Checked In"           value={data.checked_in}     icon={MdFactCheck}      color="emerald" />
        <StatCard title="Pending"              value={data.pending}        icon={MdPendingActions} color="amber"   />
        <StatCard title="Students"             value={data.total_students} icon={MdSchool}         color="purple"  />
        <StatCard title="Professionals"        value={data.total_professionals} icon={MdWork}      color="rose"    />
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="card lg:col-span-2">
          <h3 className="font-semibold text-gray-700 mb-3">Registration Trend (Last 7 Days)</h3>
          {data.trend.length ? <Line data={trendChart} options={{ ...chartOpts(), plugins: { legend: { display: false } } }} /> : <p className="text-gray-400 text-sm">No trend data yet.</p>}
        </div>
        <div className="card">
          <h3 className="font-semibold text-gray-700 mb-3">Gender Distribution</h3>
          {Object.keys(data.gender_dist).length ? <Doughnut data={genderChart} options={donutOpts} /> : <p className="text-gray-400 text-sm">No data yet.</p>}
        </div>
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="card">
          <h3 className="font-semibold text-gray-700 mb-3">Age Distribution</h3>
          {Object.keys(data.age_dist).length ? <Bar data={ageChart} options={chartOpts()} /> : <p className="text-gray-400 text-sm">No data yet.</p>}
        </div>
        <div className="card">
          <h3 className="font-semibold text-gray-700 mb-3">Department Distribution</h3>
          {Object.keys(data.dept_dist).length ? <Bar data={deptChart} options={chartOpts()} /> : <p className="text-gray-400 text-sm">No data yet.</p>}
        </div>
      </div>

      {/* Recent Registrations */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-gray-700">Recent Registrations</h3>
          <div className="flex gap-2">
            <button onClick={fetchData} className="btn-secondary text-xs py-1.5 px-3 flex items-center gap-1">
              <MdRefresh className="text-base" /> Refresh
            </button>
            <Link to="/register" className="btn-primary text-xs py-1.5 px-3">+ Register</Link>
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-100">
                {["#","Name","Email","Department","Date","Status"].map((h) => (
                  <th key={h} className="pb-2 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide pr-4">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.recent.length === 0 && (
                <tr><td colSpan={6} className="py-6 text-center text-gray-400">No registrations yet.</td></tr>
              )}
              {data.recent.map((a) => (
                <tr key={a.id} className="border-b border-gray-50 hover:bg-gray-50/60 transition">
                  <td className="py-2 pr-4 text-gray-400 font-mono text-xs">#{a.id}</td>
                  <td className="py-2 pr-4 font-medium text-gray-800">{a.full_name}</td>
                  <td className="py-2 pr-4 text-gray-500">{a.email}</td>
                  <td className="py-2 pr-4 text-gray-600">{a.department || "—"}</td>
                  <td className="py-2 pr-4 text-gray-400 text-xs">{a.registration_date?.split(" ")[0]}</td>
                  <td className="py-2">
                    <span className={`badge ${a.status === "checked_in" ? "bg-emerald-100 text-emerald-700" : "bg-violet-100 text-violet-700"}`}>
                      {a.status === "checked_in" ? "Checked In" : "Registered"}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="card">
        <h3 className="font-semibold text-gray-700 mb-4">Quick Actions</h3>
        <div className="flex flex-wrap gap-3">
          {[
            { to: "/register",    label: "New Registration", className: "btn-primary" },
            { to: "/checkin",     label: "Check-In Attendees", className: "btn-secondary" },
            { to: "/analytics",  label: "View Analytics",    className: "btn-secondary" },
            { to: "/ai-insights",label: "AI Insights",       className: "btn-secondary" },
            { to: "/export",     label: "Export Data",       className: "btn-secondary" },
            { to: "/import",     label: "Import Data",       className: "btn-secondary" },
          ].map(({ to, label, className }) => (
            <Link key={to} to={to} className={className}>{label}</Link>
          ))}
        </div>
      </div>
    </div>
  );
}
