import React from "react";
import { NavLink, useLocation } from "react-router-dom";
import {
  MdDashboard,
  MdPersonAdd,
  MdPeople,
  MdFactCheck,
  MdBarChart,
  MdAutoAwesome,
  MdUpload,
  MdDownload,
  MdPlace,
  MdRecordVoiceOver,
  MdSchedule,
  MdHandshake, MdReportProblem, MdMonitorHeart,
  MdInsights, MdBusinessCenter,
} from "react-icons/md";

const navItems = [
  { to: "/dashboard",   label: "Dashboard",        icon: MdDashboard },
  { to: "/register",    label: "Registration",      icon: MdPersonAdd },
  { to: "/attendees",   label: "Attendees",         icon: MdPeople },
  { to: "/checkin",     label: "Check-In",          icon: MdFactCheck },
  { to: "/analytics",  label: "Analytics",         icon: MdBarChart },
  { to: "/ai-insights",label: "AI Insights",       icon: MdAutoAwesome },
  { to: "/import",      label: "Import Data",       icon: MdUpload },
  { to: "/export",      label: "Export Data",       icon: MdDownload },
  { to: "/venues",      label: "Venues",            icon: MdPlace },
  { to: "/speakers",    label: "Speakers",          icon: MdRecordVoiceOver },
  { to: "/scheduling",  label: "Scheduling",        icon: MdSchedule },
  { to: "/sponsors", label: "Sponsorships", icon: MdHandshake },
  { to: "/sponsor-agent", label: "Sponsorship Agent", icon: MdAutoAwesome },
  { to: "/incidents", label: "Incidents", icon: MdReportProblem },
  { to: "/incident-agent", label: "Incident Agent", icon: MdAutoAwesome },
  { to: "/monitoring", label: "Real-Time Monitoring", icon: MdMonitorHeart },
  { to: "/executive-dashboard", label: "Executive Dashboard", icon: MdBusinessCenter },
  { to: "/intelligence", label: "Event Intelligence", icon: MdInsights },
];

export default function Sidebar({ open, onClose }) {
  return (
    <aside
      className={`
        fixed inset-y-0 left-0 z-30 w-64 flex flex-col
        bg-gradient-to-b from-violet-700 via-purple-700 to-indigo-800
        shadow-2xl transform transition-transform duration-300 ease-in-out
        md:static md:translate-x-0
        ${open ? "translate-x-0" : "-translate-x-full"}
      `}
    >
      {/* Logo */}
      <div className="flex items-center gap-3 px-6 py-5 border-b border-white/10">
        <div className="w-9 h-9 rounded-xl bg-white/20 flex items-center justify-center">
          <MdAutoAwesome className="text-white text-xl" />
        </div>
        <div>
          <p className="text-white font-bold text-sm leading-tight">Event Manager</p>
          <p className="text-white/60 text-xs">Intelligence Platform</p>
        </div>
      </div>

      {/* Nav Items */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {navItems.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            onClick={onClose}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 ${
                isActive
                  ? "bg-white text-violet-700 shadow-md"
                  : "text-white/75 hover:bg-white/15 hover:text-white"
              }`
            }
          >
            <Icon className="text-lg flex-shrink-0" />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="px-6 py-4 border-t border-white/10">
        <p className="text-white/40 text-xs text-center">v4.0.0 — Milestone 4</p>
      </div>
    </aside>
  );
}
