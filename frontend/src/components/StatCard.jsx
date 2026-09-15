import React from "react";

/**
 * Reusable statistic card for the dashboard.
 */
export default function StatCard({ title, value, icon: Icon, color, sub }) {
  const colors = {
    violet:  { bg: "bg-violet-50",   icon: "bg-violet-500",  text: "text-violet-700" },
    purple:  { bg: "bg-purple-50",   icon: "bg-purple-500",  text: "text-purple-700" },
    blue:    { bg: "bg-blue-50",     icon: "bg-blue-500",    text: "text-blue-700"   },
    emerald: { bg: "bg-emerald-50",  icon: "bg-emerald-500", text: "text-emerald-700"},
    amber:   { bg: "bg-amber-50",    icon: "bg-amber-500",   text: "text-amber-700"  },
    rose:    { bg: "bg-rose-50",     icon: "bg-rose-500",    text: "text-rose-700"   },
  };

  const c = colors[color] || colors.violet;

  return (
    <div className={`card flex items-center gap-4 hover:shadow-md transition-shadow`}>
      <div className={`w-12 h-12 rounded-xl ${c.icon} flex items-center justify-center shadow-sm flex-shrink-0`}>
        <Icon className="text-white text-2xl" />
      </div>
      <div className="min-w-0">
        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide truncate">{title}</p>
        <p className={`text-2xl font-bold ${c.text}`}>{value ?? "—"}</p>
        {sub && <p className="text-xs text-gray-400 mt-0.5">{sub}</p>}
      </div>
    </div>
  );
}
