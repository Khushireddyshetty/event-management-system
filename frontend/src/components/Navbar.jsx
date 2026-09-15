import React from "react";
import { useLocation } from "react-router-dom";
import { MdMenu, MdNotifications, MdEventNote } from "react-icons/md";

const titles = {
  "/dashboard":   "Dashboard",
  "/register":    "Registration",
  "/attendees":   "Attendee Management",
  "/checkin":     "Check-In",
  "/analytics":   "Analytics",
  "/ai-insights": "AI Insights",
  "/import":      "Import Registrations",
  "/export":      "Export Registrations",
  "/venues":      "Venue Operations",
  "/speakers":    "Speaker Operations",
  "/scheduling":  "Schedule Studio",
  "/executive-dashboard": "Executive Dashboard",
  "/intelligence": "Event Intelligence",
};

export default function Navbar({ onMenuClick }) {
  const { pathname } = useLocation();
  const title = titles[pathname] || "Event Manager";

  return (
    <header className="bg-white border-b border-gray-100 px-4 md:px-6 py-3.5 flex items-center justify-between shadow-sm z-10">
      <div className="flex items-center gap-3">
        {/* Mobile hamburger */}
        <button
          onClick={onMenuClick}
          className="md:hidden p-2 rounded-lg hover:bg-gray-100 text-gray-600"
        >
          <MdMenu className="text-xl" />
        </button>
        <div>
          <h1 className="text-lg font-bold text-gray-800">{title}</h1>
          <p className="text-xs text-gray-400 hidden sm:block">
            Intelligent Event Management Platform
          </p>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <button className="relative p-2 rounded-xl hover:bg-gray-100 text-gray-500 transition">
          <MdNotifications className="text-xl" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-violet-500 rounded-full" />
        </button>
        <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center shadow-sm">
          <MdEventNote className="text-white text-lg" />
        </div>
      </div>
    </header>
  );
}
