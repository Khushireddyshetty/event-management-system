import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";

import Layout from "./components/Layout.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Registration from "./pages/Registration.jsx";
import AttendeeManagement from "./pages/AttendeeManagement.jsx";
import CheckIn from "./pages/CheckIn.jsx";
import Analytics from "./pages/Analytics.jsx";
import AIInsights from "./pages/AIInsights.jsx";
import ImportRegistrations from "./pages/ImportRegistrations.jsx";
import ExportRegistrations from "./pages/ExportRegistrations.jsx";
import Venues from "./pages/Venues.jsx";
import Speakers from "./pages/Speakers.jsx";
import Scheduling from "./pages/Scheduling.jsx";
import Milestone3 from "./pages/Milestone3.jsx";
import ExecutiveDashboard from "./pages/ExecutiveDashboard.jsx";
import Intelligence from "./pages/Intelligence.jsx";

export default function App() {
  return (
    <>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="register" element={<Registration />} />
          <Route path="attendees" element={<AttendeeManagement />} />
          <Route path="checkin" element={<CheckIn />} />
          <Route path="analytics" element={<Analytics />} />
          <Route path="ai-insights" element={<AIInsights />} />
          <Route path="import" element={<ImportRegistrations />} />
          <Route path="export" element={<ExportRegistrations />} />
          <Route path="venues" element={<Venues />} />
          <Route path="speakers" element={<Speakers />} />
          <Route path="scheduling" element={<Scheduling />} />
          <Route path="sponsors" element={<Milestone3 section="sponsors" />} />
          <Route path="incidents" element={<Milestone3 section="incidents" />} />
          <Route path="monitoring" element={<Milestone3 section="monitoring" />} />
          <Route path="sponsor-agent" element={<Milestone3 section="sponsor-agent" />} />
          <Route path="incident-agent" element={<Milestone3 section="incident-agent" />} />
          <Route path="executive-dashboard" element={<ExecutiveDashboard />} />
          <Route path="intelligence" element={<Intelligence />} />
        </Route>
      </Routes>

      <ToastContainer
        position="top-right"
        autoClose={3500}
        hideProgressBar={false}
        newestOnTop
        closeOnClick
        rtl={false}
        pauseOnFocusLoss={false}
        draggable
        pauseOnHover
        theme="light"
        toastClassName="!rounded-xl !shadow-lg"
      />
    </>
  );
}
