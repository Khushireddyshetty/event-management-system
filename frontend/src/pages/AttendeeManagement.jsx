import React, { useEffect, useState, useCallback } from "react";
import { toast } from "react-toastify";
import { MdSearch, MdEdit, MdDelete, MdVisibility, MdClose, MdSave } from "react-icons/md";
import Spinner from "../components/Spinner.jsx";
import API from "../api/axios.js";

const GENDERS = ["", "Male", "Female", "Non-binary", "Prefer not to say"];
const STATUSES = ["", "registered", "checked_in"];

export default function AttendeeManagement() {
  const [attendees, setAttendees] = useState([]);
  const [total, setTotal] = useState(0);
  const [pages, setPages] = useState(1);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [filterGender, setFilterGender] = useState("");
  const [filterStatus, setFilterStatus] = useState("");
  const [viewModal, setViewModal] = useState(null);
  const [editModal, setEditModal] = useState(null);
  const [deleteId, setDeleteId] = useState(null);
  const [saving, setSaving] = useState(false);

  const fetch = useCallback(async () => {
    setLoading(true);
    try {
      const res = await API.get("/attendees", {
        params: { search, gender: filterGender, status: filterStatus, page, per_page: 10 },
      });
      setAttendees(res.data.attendees);
      setTotal(res.data.total);
      setPages(res.data.pages);
    } catch (e) { toast.error(e.message); }
    finally { setLoading(false); }
  }, [search, filterGender, filterStatus, page]);

  useEffect(() => { fetch(); }, [fetch]);

  const handleDelete = async () => {
    try {
      await API.delete(`/delete/${deleteId}`);
      toast.success("Attendee deleted");
      setDeleteId(null);
      fetch();
    } catch (e) { toast.error(e.message); }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await API.put(`/update/${editModal.id}`, editModal);
      toast.success("Attendee updated");
      setEditModal(null);
      fetch();
    } catch (e) { toast.error(e.message); }
    finally { setSaving(false); }
  };

  const StatusBadge = ({ status }) => (
    <span className={`badge ${status === "checked_in" ? "bg-emerald-100 text-emerald-700" : "bg-violet-100 text-violet-700"}`}>
      {status === "checked_in" ? "Checked In" : "Registered"}
    </span>
  );

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="card">
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <MdSearch className="absolute left-3 top-3 text-gray-400 text-lg" />
            <input
              value={search} onChange={(e) => { setSearch(e.target.value); setPage(1); }}
              placeholder="Search by name, email, college, phone…"
              className="input pl-9"
            />
          </div>
          <select value={filterGender} onChange={(e) => { setFilterGender(e.target.value); setPage(1); }} className="input sm:w-40">
            <option value="">All Genders</option>
            {["Male","Female","Non-binary","Prefer not to say"].map((g) => <option key={g}>{g}</option>)}
          </select>
          <select value={filterStatus} onChange={(e) => { setFilterStatus(e.target.value); setPage(1); }} className="input sm:w-40">
            <option value="">All Status</option>
            <option value="registered">Registered</option>
            <option value="checked_in">Checked In</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="card overflow-x-auto">
        <div className="flex items-center justify-between mb-3">
          <p className="text-sm text-gray-500">{total} attendee{total !== 1 ? "s" : ""} found</p>
        </div>
        {loading ? <div className="py-12"><Spinner size="lg" className="justify-center" /></div> : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-100">
                {["#","Name","Email","Department","College","Status","Actions"].map((h) => (
                  <th key={h} className="pb-2 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide pr-4 whitespace-nowrap">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {attendees.length === 0 && (
                <tr><td colSpan={7} className="py-10 text-center text-gray-400">No attendees found.</td></tr>
              )}
              {attendees.map((a) => (
                <tr key={a.id} className="border-b border-gray-50 hover:bg-gray-50/60 transition">
                  <td className="py-2 pr-4 text-gray-400 font-mono text-xs">#{a.id}</td>
                  <td className="py-2 pr-4 font-medium text-gray-800 whitespace-nowrap">{a.full_name}</td>
                  <td className="py-2 pr-4 text-gray-500 text-xs">{a.email}</td>
                  <td className="py-2 pr-4 text-gray-600">{a.department || "—"}</td>
                  <td className="py-2 pr-4 text-gray-500 text-xs">{a.college || "—"}</td>
                  <td className="py-2 pr-4"><StatusBadge status={a.status} /></td>
                  <td className="py-2">
                    <div className="flex gap-1">
                      <button onClick={() => setViewModal(a)} className="p-1.5 rounded-lg hover:bg-blue-50 text-blue-500 transition" title="View"><MdVisibility /></button>
                      <button onClick={() => setEditModal({ ...a })} className="p-1.5 rounded-lg hover:bg-amber-50 text-amber-500 transition" title="Edit"><MdEdit /></button>
                      <button onClick={() => setDeleteId(a.id)} className="p-1.5 rounded-lg hover:bg-rose-50 text-rose-500 transition" title="Delete"><MdDelete /></button>
                    </div>
                  </td>
                </tr>
              ))}
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

      {/* View Modal */}
      {viewModal && (
        <Modal title="Attendee Details" onClose={() => setViewModal(null)}>
          <div className="grid grid-cols-2 gap-3 text-sm">
            {Object.entries(viewModal).filter(([k]) => k !== "special_requirements").map(([k, v]) => (
              <div key={k}>
                <p className="text-xs text-gray-400 capitalize">{k.replace(/_/g, " ")}</p>
                <p className="font-medium text-gray-800">{v || "—"}</p>
              </div>
            ))}
            {viewModal.special_requirements && (
              <div className="col-span-2">
                <p className="text-xs text-gray-400">Special Requirements</p>
                <p className="font-medium text-gray-800">{viewModal.special_requirements}</p>
              </div>
            )}
          </div>
        </Modal>
      )}

      {/* Edit Modal */}
      {editModal && (
        <Modal title="Edit Attendee" onClose={() => setEditModal(null)} wide>
          <div className="grid grid-cols-2 gap-3 text-sm">
            {["full_name","email","phone","age","gender","role","department","college","city","state","event_name","registration_type","food_preference"].map((k) => (
              <div key={k}>
                <label className="label">{k.replace(/_/g, " ")}</label>
                <input
                  value={editModal[k] || ""}
                  onChange={(e) => setEditModal(prev => ({ ...prev, [k]: e.target.value }))}
                  className="input"
                />
              </div>
            ))}
            <div className="col-span-2">
              <label className="label">Special Requirements</label>
              <textarea
                rows={2}
                value={editModal.special_requirements || ""}
                onChange={(e) => setEditModal(prev => ({ ...prev, special_requirements: e.target.value }))}
                className="input resize-none"
              />
            </div>
          </div>
          <div className="flex justify-end gap-2 mt-4">
            <button onClick={() => setEditModal(null)} className="btn-secondary">Cancel</button>
            <button onClick={handleSave} disabled={saving} className="btn-primary flex items-center gap-1.5">
              {saving ? <span className="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin" /> : <MdSave />}
              Save Changes
            </button>
          </div>
        </Modal>
      )}

      {/* Delete Confirm */}
      {deleteId && (
        <Modal title="Confirm Delete" onClose={() => setDeleteId(null)}>
          <p className="text-gray-600 mb-5">Are you sure you want to delete this attendee? This action cannot be undone.</p>
          <div className="flex justify-end gap-2">
            <button onClick={() => setDeleteId(null)} className="btn-secondary">Cancel</button>
            <button onClick={handleDelete} className="btn-danger">Delete</button>
          </div>
        </Modal>
      )}
    </div>
  );
}

function Modal({ title, children, onClose, wide }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm">
      <div className={`bg-white rounded-2xl shadow-2xl w-full ${wide ? "max-w-2xl" : "max-w-md"} max-h-[90vh] overflow-y-auto`}>
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <h3 className="font-bold text-gray-800">{title}</h3>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-gray-100 text-gray-500"><MdClose /></button>
        </div>
        <div className="p-6">{children}</div>
      </div>
    </div>
  );
}
