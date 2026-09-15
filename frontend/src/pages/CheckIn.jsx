import React, { useEffect, useState, useCallback } from "react";
import { toast } from "react-toastify";
import { MdSearch, MdFactCheck, MdUndo, MdPin, MdCheckCircle } from "react-icons/md";
import Spinner from "../components/Spinner.jsx";
import API from "../api/axios.js";

// ---------------------------------------------------------------------------
// PIN Check-In Panel
// ---------------------------------------------------------------------------
function PinCheckIn() {
  const [pin, setPin]           = useState("");
  const [loading, setLoading]   = useState(false);
  const [result, setResult]     = useState(null); // { success, attendee, message }

  const handleSubmit = async (e) => {
    e.preventDefault();
    const trimmed = pin.trim();
    if (!trimmed) { toast.warning("Please enter a PIN."); return; }
    if (!/^\d{6}$/.test(trimmed)) { toast.warning("PIN must be exactly 6 digits."); return; }

    setLoading(true);
    setResult(null);
    try {
      const res = await API.post("/checkin/pin", { pin: trimmed });
      setResult({ success: true, attendee: res.data.attendee, message: res.data.message });
      toast.success(res.data.message || "Check-in successful!");
      setPin("");
    } catch (err) {
      const errMsg = err.response?.data?.error || err.message;
      const alreadyIn = err.response?.data?.attendee;
      if (alreadyIn) {
        setResult({ success: false, attendee: alreadyIn, message: errMsg });
      } else {
        setResult({ success: false, attendee: null, message: errMsg });
      }
      toast.error(errMsg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <div className="flex items-center gap-3 mb-4">
        <div className="w-9 h-9 rounded-xl bg-violet-100 flex items-center justify-center">
          <MdPin className="text-violet-600 text-lg" />
        </div>
        <div>
          <h2 className="text-base font-bold text-gray-800">PIN Check-In</h2>
          <p className="text-xs text-gray-500">Enter the 6-digit PIN from the attendee's confirmation email</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="flex gap-3 items-end flex-wrap">
        <div className="flex-1 min-w-[200px]">
          <label className="label">Attendee PIN</label>
          <input
            type="text"
            inputMode="numeric"
            maxLength={6}
            value={pin}
            onChange={(e) => { setPin(e.target.value.replace(/\D/g, "")); setResult(null); }}
            placeholder="e.g. 482951"
            className="input font-mono text-lg tracking-widest text-center"
            disabled={loading}
          />
        </div>
        <button
          type="submit"
          disabled={loading || pin.trim().length !== 6}
          className="btn-primary flex items-center gap-2 h-[42px] px-6 disabled:opacity-50"
        >
          {loading
            ? <span className="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin" />
            : <MdFactCheck />}
          {loading ? "Checking…" : "Check In"}
        </button>
      </form>

      {/* Result panel */}
      {result && (
        <div className={`mt-4 rounded-xl border p-4 ${
          result.success
            ? "bg-emerald-50 border-emerald-200"
            : "bg-rose-50 border-rose-200"
        }`}>
          {result.success ? (
            <>
              <div className="flex items-center gap-2 mb-3">
                <MdCheckCircle className="text-emerald-500 text-xl" />
                <span className="font-semibold text-emerald-700">Check-In Successful!</span>
              </div>
              {result.attendee && <AttendeeCard attendee={result.attendee} />}
            </>
          ) : (
            <>
              <div className="flex items-center gap-2 mb-2">
                <span className="text-rose-500 text-xl font-bold">✗</span>
                <span className="font-semibold text-rose-700">
                  {result.message || "Invalid PIN"}
                </span>
              </div>
              {result.attendee && (
                <div className="mt-2">
                  <p className="text-xs text-rose-500 mb-2">Attendee details:</p>
                  <AttendeeCard attendee={result.attendee} />
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}

function AttendeeCard({ attendee: a }) {
  return (
    <div className="grid grid-cols-2 gap-x-6 gap-y-1 text-sm">
      {[
        ["Name",            a.full_name],
        ["Email",           a.email],
        ["Registration ID", a.registration_id || "—"],
        ["Event",           a.event_name || "—"],
        ["Status",          a.status === "checked_in" ? "✓ Checked In" : "Pending"],
        ["Check-In Time",   a.checkin_time || "—"],
      ].map(([label, value]) => (
        <div key={label} className="flex gap-2">
          <span className="text-gray-400 w-32 shrink-0">{label}:</span>
          <span className="font-medium text-gray-700 break-all">{value}</span>
        </div>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main CheckIn page
// ---------------------------------------------------------------------------
export default function CheckIn() {
  const [attendees, setAttendees] = useState([]);
  const [total, setTotal]         = useState(0);
  const [pages, setPages]         = useState(1);
  const [page, setPage]           = useState(1);
  const [search, setSearch]       = useState("");
  const [loading, setLoading]     = useState(true);
  const [actionId, setActionId]   = useState(null);

  const fetchAttendees = useCallback(async () => {
    setLoading(true);
    try {
      const res = await API.get("/attendees", {
        params: { search, page, per_page: 10 },
      });
      setAttendees(res.data.attendees);
      setTotal(res.data.total);
      setPages(res.data.pages);
    } catch (e) { toast.error(e.message); }
    finally { setLoading(false); }
  }, [search, page]);

  useEffect(() => { fetchAttendees(); }, [fetchAttendees]);

  const handleCheckIn = async (id) => {
    setActionId(id);
    try {
      await API.post(`/checkin/${id}`);
      toast.success("Checked in successfully!");
      fetchAttendees();
    } catch (e) { toast.error(e.message); }
    finally { setActionId(null); }
  };

  const handleUndo = async (id) => {
    setActionId(id);
    try {
      await API.post(`/undo-checkin/${id}`);
      toast.info("Check-in reversed.");
      fetchAttendees();
    } catch (e) { toast.error(e.message); }
    finally { setActionId(null); }
  };

  const checkedCount = attendees.filter((a) => a.status === "checked_in").length;

  return (
    <div className="space-y-4">
      {/* ── PIN Check-In ─────────────────────────────────────────── */}
      <PinCheckIn />

      {/* ── Search ───────────────────────────────────────────────── */}
      <div className="card">
        <div className="relative">
          <MdSearch className="absolute left-3 top-3 text-gray-400 text-lg" />
          <input
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            placeholder="Search attendees by name, email…"
            className="input pl-9"
          />
        </div>
      </div>

      {/* ── Summary ──────────────────────────────────────────────── */}
      <div className="grid grid-cols-3 gap-4">
        {[
          { label: "Total on Page", value: attendees.length,               cls: "text-gray-700" },
          { label: "Checked In",    value: checkedCount,                    cls: "text-emerald-600" },
          { label: "Pending",       value: attendees.length - checkedCount, cls: "text-amber-600" },
        ].map(({ label, value, cls }) => (
          <div key={label} className="card text-center">
            <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">{label}</p>
            <p className={`text-2xl font-bold ${cls}`}>{value}</p>
          </div>
        ))}
      </div>

      {/* ── Table ────────────────────────────────────────────────── */}
      <div className="card overflow-x-auto">
        {loading
          ? <div className="py-12"><Spinner size="lg" className="justify-center" /></div>
          : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-100">
                  {["#","Name","Email","PIN","Reg. Status","Check-In","Time","Action"].map((h) => (
                    <th key={h} className="pb-2 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide pr-4 whitespace-nowrap">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {attendees.length === 0 && (
                  <tr><td colSpan={8} className="py-10 text-center text-gray-400">No attendees found.</td></tr>
                )}
                {attendees.map((a) => {
                  const isCheckedIn = a.status === "checked_in";
                  const busy = actionId === a.id;
                  return (
                    <tr key={a.id} className="border-b border-gray-50 hover:bg-gray-50/60 transition">
                      <td className="py-2.5 pr-4 text-gray-400 font-mono text-xs">#{a.id}</td>
                      <td className="py-2.5 pr-4 font-medium text-gray-800 whitespace-nowrap">{a.full_name}</td>
                      <td className="py-2.5 pr-4 text-gray-500 text-xs">{a.email}</td>
                      <td className="py-2.5 pr-4">
                        <span className="font-mono text-xs bg-amber-50 text-amber-700 border border-amber-200 px-2 py-0.5 rounded">
                          {a.unique_pin || "—"}
                        </span>
                      </td>
                      <td className="py-2.5 pr-4">
                        <span className="badge bg-violet-100 text-violet-700">Registered</span>
                      </td>
                      <td className="py-2.5 pr-4">
                        <span className={`badge ${isCheckedIn ? "bg-emerald-100 text-emerald-700" : "bg-gray-100 text-gray-500"}`}>
                          {isCheckedIn ? "Checked In" : "Not Yet"}
                        </span>
                      </td>
                      <td className="py-2.5 pr-4 text-gray-400 text-xs">
                        {a.checkin_time || "—"}
                      </td>
                      <td className="py-2.5">
                        {isCheckedIn ? (
                          <button
                            onClick={() => handleUndo(a.id)}
                            disabled={busy}
                            className="flex items-center gap-1 text-xs bg-amber-100 hover:bg-amber-200 text-amber-700 font-medium px-3 py-1.5 rounded-lg transition disabled:opacity-50"
                          >
                            {busy
                              ? <span className="w-3 h-3 border-2 border-amber-400 border-t-amber-700 rounded-full animate-spin" />
                              : <MdUndo className="text-sm" />}
                            Undo
                          </button>
                        ) : (
                          <button
                            onClick={() => handleCheckIn(a.id)}
                            disabled={busy}
                            className="flex items-center gap-1 text-xs bg-emerald-100 hover:bg-emerald-200 text-emerald-700 font-medium px-3 py-1.5 rounded-lg transition disabled:opacity-50"
                          >
                            {busy
                              ? <span className="w-3 h-3 border-2 border-emerald-400 border-t-emerald-700 rounded-full animate-spin" />
                              : <MdFactCheck className="text-sm" />}
                            Check In
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}

        {/* Pagination */}
        {pages > 1 && (
          <div className="flex items-center justify-center gap-2 mt-4">
            <button disabled={page === 1} onClick={() => setPage(p => p - 1)} className="btn-secondary py-1.5 px-3 text-sm disabled:opacity-40">Prev</button>
            {[...Array(pages)].map((_, i) => (
              <button key={i} onClick={() => setPage(i + 1)} className={`w-8 h-8 rounded-lg text-sm font-medium transition ${page === i + 1 ? "bg-violet-600 text-white" : "hover:bg-gray-100 text-gray-600"}`}>{i + 1}</button>
            ))}
            <button disabled={page === pages} onClick={() => setPage(p => p + 1)} className="btn-secondary py-1.5 px-3 text-sm disabled:opacity-40">Next</button>
          </div>
        )}
      </div>
    </div>
  );
}
