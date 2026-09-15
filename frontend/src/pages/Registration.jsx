import React, { useState } from "react";
import { toast } from "react-toastify";
import { MdPersonAdd, MdRefresh, MdClose, MdContentCopy } from "react-icons/md";
import API from "../api/axios.js";

const INITIAL = {
  full_name: "", email: "", phone: "", age: "", gender: "", role: "",
  department: "", college: "", city: "", state: "", event_name: "",
  registration_type: "", food_preference: "", special_requirements: "",
};

const GENDERS = ["Male", "Female", "Non-binary", "Prefer not to say"];
const ROLES = ["Student", "Professional", "Faculty", "Researcher", "Other"];
const DEPARTMENTS = ["Computer Science","Information Technology","Electronics","Mechanical","Civil","Business","Finance","Marketing","Design","Law","Other"];
const FOOD_PREFS = ["Vegetarian", "Non-Vegetarian", "Vegan", "Jain", "No Preference"];
const REG_TYPES = ["General", "VIP", "Speaker", "Volunteer", "Media"];

function Field({ label, children, required }) {
  return (
    <div>
      <label className="label">{label}{required && <span className="text-rose-400 ml-0.5">*</span>}</label>
      {children}
    </div>
  );
}

/** Success modal shown after registration — displays Registration ID and PIN */
function SuccessModal({ data, onClose }) {
  const copy = (text) => {
    navigator.clipboard.writeText(text).then(() => toast.info("Copied!"));
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md overflow-hidden animate-fade-in">
        {/* Header */}
        <div className="bg-emerald-500 px-6 py-5 text-white">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-2xl">✓</span>
              <h2 className="text-lg font-bold">Registration Successful!</h2>
            </div>
            <button onClick={onClose} className="p-1 rounded-lg hover:bg-white/20 transition">
              <MdClose className="text-xl" />
            </button>
          </div>
          <p className="text-emerald-100 text-sm mt-1">
            A confirmation email has been sent to <strong>{data.email}</strong>
          </p>
        </div>

        {/* Body */}
        <div className="px-6 py-5 space-y-4">
          {/* Registration ID */}
          <div className="bg-violet-50 border border-violet-200 rounded-xl p-4">
            <p className="text-xs text-violet-500 uppercase tracking-widest font-semibold mb-1">
              Registration ID
            </p>
            <div className="flex items-center justify-between">
              <span className="text-xl font-bold text-violet-700 font-mono">
                {data.registration_id}
              </span>
              <button
                onClick={() => copy(data.registration_id)}
                title="Copy Registration ID"
                className="p-1.5 rounded-lg text-violet-400 hover:text-violet-600 hover:bg-violet-100 transition"
              >
                <MdContentCopy />
              </button>
            </div>
          </div>

          {/* Unique PIN */}
          <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
            <p className="text-xs text-amber-500 uppercase tracking-widest font-semibold mb-1">
              Unique Check-In PIN
            </p>
            <div className="flex items-center justify-between">
              <span className="text-4xl font-extrabold text-amber-600 font-mono tracking-widest">
                {data.unique_pin}
              </span>
              <button
                onClick={() => copy(data.unique_pin)}
                title="Copy PIN"
                className="p-1.5 rounded-lg text-amber-400 hover:text-amber-600 hover:bg-amber-100 transition"
              >
                <MdContentCopy />
              </button>
            </div>
            <p className="text-xs text-amber-500 mt-2">
              ⚠ Keep this PIN safe — it is required for event check-in.
            </p>
          </div>

          {/* Details */}
          <div className="text-sm text-gray-600 space-y-1">
            <div className="flex justify-between">
              <span className="text-gray-400">Name</span>
              <span className="font-medium text-gray-700">{data.full_name}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Event</span>
              <span className="font-medium text-gray-700">{data.event_name || "—"}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Registered At</span>
              <span className="font-medium text-gray-700">{data.registration_date || "—"}</span>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 pb-5">
          <button
            onClick={onClose}
            className="w-full btn-primary flex items-center justify-center gap-2"
          >
            <MdPersonAdd /> Register Another Attendee
          </button>
        </div>
      </div>
    </div>
  );
}

export default function Registration() {
  const [form, setForm] = useState(INITIAL);
  const [errors, setErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [successData, setSuccessData] = useState(null);

  const set = (k, v) => {
    setForm((prev) => ({ ...prev, [k]: v }));
    setErrors((prev) => ({ ...prev, [k]: "" }));
  };

  const validate = () => {
    const errs = {};
    if (!form.full_name.trim()) errs.full_name = "Full name is required";
    if (!form.email.trim()) errs.email = "Email is required";
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) errs.email = "Enter a valid email";
    if (form.phone && !/^\+?[\d\s\-()]{7,15}$/.test(form.phone)) errs.phone = "Enter a valid phone number";
    if (form.age && (isNaN(form.age) || form.age < 1 || form.age > 120)) errs.age = "Enter a valid age";
    return errs;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const errs = validate();
    if (Object.keys(errs).length) { setErrors(errs); return; }

    setSubmitting(true);
    try {
      const res = await API.post("/register", { ...form, age: form.age ? parseInt(form.age) : null });
      // Show success modal with PIN and registration ID
      setSuccessData({
        full_name: form.full_name,
        email: form.email,
        event_name: form.event_name,
        registration_id: res.data.registration_id,
        unique_pin: res.data.unique_pin,
        registration_date: res.data.registration_date,
      });
      setForm(INITIAL);
      setErrors({});
    } catch (err) {
      toast.error(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const inp = (key, placeholder, type = "text", extra = {}) => (
    <>
      <input
        type={type}
        value={form[key]}
        onChange={(e) => set(key, e.target.value)}
        placeholder={placeholder}
        className={`input ${errors[key] ? "border-rose-400 focus:ring-rose-300" : ""}`}
        {...extra}
      />
      {errors[key] && <p className="text-rose-500 text-xs mt-1">{errors[key]}</p>}
    </>
  );

  const sel = (key, options, placeholder) => (
    <select value={form[key]} onChange={(e) => set(key, e.target.value)} className="input">
      <option value="">{placeholder}</option>
      {options.map((o) => <option key={o} value={o}>{o}</option>)}
    </select>
  );

  return (
    <>
      {/* Success Modal */}
      {successData && (
        <SuccessModal
          data={successData}
          onClose={() => setSuccessData(null)}
        />
      )}

      <div className="max-w-3xl mx-auto">
        <div className="card">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-xl bg-violet-100 flex items-center justify-center">
              <MdPersonAdd className="text-violet-600 text-xl" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-gray-800">New Registration</h2>
              <p className="text-xs text-gray-500">Fill in the attendee details below</p>
            </div>
          </div>

          <form onSubmit={handleSubmit} noValidate>
            {/* Personal Info */}
            <div className="mb-5">
              <p className="text-xs font-bold text-violet-600 uppercase tracking-widest mb-3 pb-1 border-b border-violet-100">Personal Information</p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Field label="Full Name" required>{inp("full_name", "John Doe")}</Field>
                <Field label="Email Address" required>{inp("email", "john@example.com", "email")}</Field>
                <Field label="Phone Number">{inp("phone", "+91 98765 43210", "tel")}</Field>
                <Field label="Age">{inp("age", "22", "number", { min: 1, max: 120 })}</Field>
                <Field label="Gender">{sel("gender", GENDERS, "Select gender")}</Field>
                <Field label="Role">{sel("role", ROLES, "Select role")}</Field>
              </div>
            </div>

            {/* Academic / Professional */}
            <div className="mb-5">
              <p className="text-xs font-bold text-violet-600 uppercase tracking-widest mb-3 pb-1 border-b border-violet-100">Academic / Professional</p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Field label="Department">{sel("department", DEPARTMENTS, "Select department")}</Field>
                <Field label="College / Company">{inp("college", "MIT / Accenture")}</Field>
                <Field label="City">{inp("city", "Mumbai")}</Field>
                <Field label="State">{inp("state", "Maharashtra")}</Field>
              </div>
            </div>

            {/* Event Details */}
            <div className="mb-6">
              <p className="text-xs font-bold text-violet-600 uppercase tracking-widest mb-3 pb-1 border-b border-violet-100">Event Details</p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Field label="Event Name">{inp("event_name", "TechFest 2025")}</Field>
                <Field label="Registration Type">{sel("registration_type", REG_TYPES, "Select type")}</Field>
                <Field label="Food Preference">{sel("food_preference", FOOD_PREFS, "Select preference")}</Field>
                <Field label="Special Requirements">
                  <textarea
                    rows={2}
                    value={form.special_requirements}
                    onChange={(e) => set("special_requirements", e.target.value)}
                    placeholder="Wheelchair access, dietary restriction, etc."
                    className="input resize-none"
                  />
                </Field>
              </div>
            </div>

            {/* Buttons */}
            <div className="flex gap-3 justify-end">
              <button type="button" onClick={() => { setForm(INITIAL); setErrors({}); }} className="btn-secondary flex items-center gap-1.5">
                <MdRefresh /> Reset
              </button>
              <button type="submit" disabled={submitting} className="btn-primary flex items-center gap-1.5 min-w-[120px] justify-center">
                {submitting ? <span className="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin" /> : <MdPersonAdd />}
                {submitting ? "Registering…" : "Register"}
              </button>
            </div>
          </form>
        </div>
      </div>
    </>
  );
}
