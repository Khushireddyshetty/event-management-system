import React, { useState } from "react";
import { MdAutoAwesome, MdRefresh } from "react-icons/md";
import { toast } from "react-toastify";
import Spinner from "../components/Spinner.jsx";
import API from "../api/axios.js";

const INSIGHT_KEYS = [
  { key: "registration_summary",    label: "Registration Summary" },
  { key: "attendance_prediction",   label: "Attendance Prediction" },
  { key: "peak_registration_hours", label: "Peak Registration Hours" },
  { key: "volunteer_suggestions",   label: "Volunteer Suggestions" },
  { key: "crowd_insights",          label: "Crowd Insights" },
  { key: "department_trends",       label: "Department Trends" },
  { key: "event_recommendations",   label: "Event Recommendations" },
];

export default function AIInsights() {
  const [insights, setInsights] = useState(null);
  const [loading, setLoading] = useState(false);

  const generate = async () => {
    setLoading(true);
    setInsights(null);
    try {
      const res = await API.post("/generate-ai");
      setInsights(res.data.insights);
      toast.success("AI insights generated!");
    } catch (e) {
      toast.error(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-5">
      {/* Header Card */}
      <div className="card bg-gradient-to-r from-violet-50 to-purple-50 border-violet-100">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center shadow-md">
              <MdAutoAwesome className="text-white text-2xl" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-gray-800">AI-Powered Insights</h2>
              <p className="text-xs text-gray-500">Powered by Google Gemini (mock fallback if no API key)</p>
            </div>
          </div>
          <button
            onClick={generate}
            disabled={loading}
            className="btn-primary flex items-center gap-2 min-w-[180px] justify-center"
          >
            {loading ? (
              <><span className="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin" />Generating…</>
            ) : (
              <><MdAutoAwesome />Generate AI Insights</>
            )}
          </button>
        </div>
      </div>

      {/* Loading shimmer */}
      {loading && (
        <div className="space-y-3">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="card animate-pulse">
              <div className="h-4 bg-gray-100 rounded w-1/3 mb-2" />
              <div className="h-3 bg-gray-100 rounded w-full mb-1" />
              <div className="h-3 bg-gray-100 rounded w-4/5" />
            </div>
          ))}
        </div>
      )}

      {/* Results */}
      {insights && !loading && (
        <div className="space-y-3">
          {INSIGHT_KEYS.map(({ key, label }) => {
            const text = insights[key];
            if (!text) return null;
            return (
              <div key={key} className="card hover:shadow-md transition-shadow">
                <div className="flex items-start gap-3">
                  <div>
                    <h3 className="font-semibold text-gray-800 mb-1.5">{label}</h3>
                    <p className="text-gray-600 text-sm leading-relaxed whitespace-pre-line">{text}</p>
                  </div>
                </div>
              </div>
            );
          })}

          <button onClick={generate} className="btn-secondary w-full flex items-center justify-center gap-2 py-3">
            <MdRefresh className="text-lg" /> Regenerate Insights
          </button>
        </div>
      )}

      {/* Empty state */}
      {!insights && !loading && (
        <div className="card text-center py-16">
          <MdAutoAwesome className="text-5xl text-violet-200 mx-auto mb-3" />
          <p className="text-gray-500 font-medium mb-1">No insights yet</p>
          <p className="text-gray-400 text-sm">Click "Generate AI Insights" to analyze your attendee data.</p>
        </div>
      )}
    </div>
  );
}
