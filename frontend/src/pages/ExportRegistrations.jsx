import React, { useEffect, useState } from "react";
import { toast } from "react-toastify";
import { MdDownload, MdTableChart, MdCode } from "react-icons/md";
import API from "../api/axios.js";

export default function ExportRegistrations() {
  const [total, setTotal] = useState(null);
  const [exporting, setExporting] = useState(null);

  useEffect(() => {
    API.get("/analytics").then((r) => setTotal(r.data.total)).catch(console.error);
  }, []);

  const handleExport = async (format) => {
    setExporting(format);
    try {
      const response = await API.get(`/export?format=${format}`, { responseType: "blob" });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const a = document.createElement("a");
      a.href = url;
      a.download = `attendees.${format}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      toast.success(`Exported as ${format.toUpperCase()} successfully!`);
    } catch (e) {
      toast.error("Export failed. Please try again.");
    } finally {
      setExporting(null);
    }
  };

  return (
    <div className="max-w-xl mx-auto space-y-5">
      {/* Summary */}
      <div className="card text-center bg-gradient-to-br from-violet-50 to-purple-50 border-violet-100">
        <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">Total Records Available</p>
        <p className="text-4xl font-bold text-violet-700 mb-1">{total ?? "…"}</p>
        <p className="text-gray-500 text-sm">registered attendees ready to export</p>
      </div>

      {/* Export Options */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {/* CSV */}
        <div className="card hover:shadow-md transition-shadow">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-xl bg-emerald-100 flex items-center justify-center">
              <MdTableChart className="text-emerald-600 text-xl" />
            </div>
            <div>
              <p className="font-semibold text-gray-800">CSV Export</p>
              <p className="text-xs text-gray-400">Open in Excel, Google Sheets</p>
            </div>
          </div>
          <ul className="text-xs text-gray-500 space-y-1 mb-4">
            <li>✓ All attendee fields included</li>
            <li>✓ Compatible with Excel / Google Sheets</li>
            <li>✓ UTF-8 encoded</li>
          </ul>
          <button
            onClick={() => handleExport("csv")}
            disabled={exporting !== null || total === 0}
            className="w-full btn-primary flex items-center justify-center gap-2 disabled:opacity-50"
          >
            {exporting === "csv" ? <span className="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin" /> : <MdDownload />}
            {exporting === "csv" ? "Exporting…" : "Download CSV"}
          </button>
        </div>

        {/* JSON */}
        <div className="card hover:shadow-md transition-shadow">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-xl bg-blue-100 flex items-center justify-center">
              <MdCode className="text-blue-600 text-xl" />
            </div>
            <div>
              <p className="font-semibold text-gray-800">JSON Export</p>
              <p className="text-xs text-gray-400">For developers and integrations</p>
            </div>
          </div>
          <ul className="text-xs text-gray-500 space-y-1 mb-4">
            <li>✓ Structured array of objects</li>
            <li>✓ All fields with original types</li>
            <li>✓ Pretty-printed for readability</li>
          </ul>
          <button
            onClick={() => handleExport("json")}
            disabled={exporting !== null || total === 0}
            className="w-full btn-primary flex items-center justify-center gap-2 disabled:opacity-50"
          >
            {exporting === "json" ? <span className="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin" /> : <MdDownload />}
            {exporting === "json" ? "Exporting…" : "Download JSON"}
          </button>
        </div>
      </div>

      {total === 0 && (
        <div className="card text-center py-8 text-gray-400">
          <p className="font-medium">No attendees registered yet.</p>
          <p className="text-sm mt-1">Register some attendees before exporting.</p>
        </div>
      )}
    </div>
  );
}
