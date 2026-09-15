import React, { useState, useRef } from "react";
import { toast } from "react-toastify";
import { MdUpload, MdCheckCircle, MdWarning, MdDownload } from "react-icons/md";
import API from "../api/axios.js";

const CSV_SAMPLE = `full_name,email,phone,age,gender,role,department,college,city,state,event_name,registration_type,food_preference,special_requirements
Alice Smith,alice@example.com,9876543210,22,Female,Student,Computer Science,MIT,Mumbai,Maharashtra,TechFest 2025,General,Vegetarian,
Bob Jones,bob@example.com,9876543211,25,Male,Professional,Electronics,IIT Delhi,Delhi,Delhi,TechFest 2025,VIP,Non-Vegetarian,
`;

const JSON_SAMPLE = JSON.stringify([
  { full_name: "Alice Smith", email: "alice@example.com", phone: "9876543210", age: 22, gender: "Female", role: "Student", department: "Computer Science", college: "MIT", city: "Mumbai", state: "Maharashtra", event_name: "TechFest 2025", registration_type: "General", food_preference: "Vegetarian", special_requirements: "" },
  { full_name: "Bob Jones",   email: "bob@example.com",   phone: "9876543211", age: 25, gender: "Male",   role: "Professional", department: "Electronics", college: "IIT Delhi", city: "Delhi", state: "Delhi", event_name: "TechFest 2025", registration_type: "VIP", food_preference: "Non-Vegetarian", special_requirements: "" },
], null, 2);

export default function ImportRegistrations() {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
  const inputRef = useRef(null);

  const handleFile = (e) => {
    const f = e.target.files[0];
    if (!f) return;
    const ext = f.name.split(".").pop().toLowerCase();
    if (!["csv", "json"].includes(ext)) { toast.error("Only CSV or JSON files are supported."); return; }
    setFile(f);
    setResult(null);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const f = e.dataTransfer.files[0];
    if (f) {
      const ext = f.name.split(".").pop().toLowerCase();
      if (!["csv", "json"].includes(ext)) { toast.error("Only CSV or JSON files are supported."); return; }
      setFile(f);
      setResult(null);
    }
  };

  const handleUpload = async () => {
    if (!file) { toast.error("Please select a file first."); return; }
    setUploading(true);
    const fd = new FormData();
    fd.append("file", file);
    try {
      const res = await API.post("/import", fd, { headers: { "Content-Type": "multipart/form-data" } });
      setResult(res.data);
      toast.success(res.data.message);
    } catch (e) { toast.error(e.message); }
    finally { setUploading(false); }
  };

  const downloadSample = (type) => {
    const content = type === "csv" ? CSV_SAMPLE : JSON_SAMPLE;
    const mime = type === "csv" ? "text/csv" : "application/json";
    const blob = new Blob([content], { type: mime });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `sample_import.${type}`;
    a.click();
  };

  return (
    <div className="max-w-2xl mx-auto space-y-5">
      {/* Drop Zone */}
      <div
        onDrop={handleDrop}
        onDragOver={(e) => e.preventDefault()}
        onClick={() => inputRef.current?.click()}
        className="card border-2 border-dashed border-violet-200 hover:border-violet-400 cursor-pointer transition-colors text-center py-12"
      >
        <MdUpload className="text-5xl text-violet-300 mx-auto mb-2" />
        <p className="text-gray-600 font-medium">Drop your CSV or JSON file here</p>
        <p className="text-gray-400 text-sm mt-1">or click to browse</p>
        {file && <p className="mt-3 text-violet-600 font-semibold text-sm">📎 {file.name} ({(file.size / 1024).toFixed(1)} KB)</p>}
        <input ref={inputRef} type="file" accept=".csv,.json" onChange={handleFile} className="hidden" />
      </div>

      {/* Action Buttons */}
      <div className="flex flex-col sm:flex-row gap-3">
        <button
          onClick={handleUpload}
          disabled={!file || uploading}
          className="btn-primary flex items-center justify-center gap-2 flex-1 disabled:opacity-50"
        >
          {uploading ? <><span className="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin" />Importing…</> : <><MdUpload />Import File</>}
        </button>
        <button onClick={() => downloadSample("csv")} className="btn-secondary flex items-center gap-2">
          <MdDownload />Sample CSV
        </button>
        <button onClick={() => downloadSample("json")} className="btn-secondary flex items-center gap-2">
          <MdDownload />Sample JSON
        </button>
      </div>

      {/* Result */}
      {result && (
        <div className="card border border-emerald-100 bg-emerald-50">
          <div className="flex items-start gap-3">
            <MdCheckCircle className="text-emerald-500 text-2xl flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-emerald-800">{result.message}</p>
              <p className="text-sm text-emerald-600 mt-1">
                ✅ Inserted: {result.inserted} &nbsp;·&nbsp; ⏭ Skipped: {result.skipped}
              </p>
              {result.errors?.length > 0 && (
                <div className="mt-3">
                  <p className="text-xs font-semibold text-amber-700 flex items-center gap-1"><MdWarning />Warnings:</p>
                  <ul className="mt-1 space-y-0.5">
                    {result.errors.map((e, i) => <li key={i} className="text-xs text-amber-700">{e}</li>)}
                  </ul>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Format Guide */}
      <div className="card">
        <h3 className="font-semibold text-gray-700 mb-3">Supported Formats</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
          <div className="bg-gray-50 rounded-xl p-4">
            <p className="font-semibold text-gray-700 mb-2">CSV Format</p>
            <p className="text-gray-500 text-xs">First row must be the header row with exact column names. Each subsequent row is one attendee.</p>
          </div>
          <div className="bg-gray-50 rounded-xl p-4">
            <p className="font-semibold text-gray-700 mb-2">JSON Format</p>
            <p className="text-gray-500 text-xs">A JSON array of objects. Each object must have at minimum <code className="bg-gray-200 px-1 rounded">full_name</code> and <code className="bg-gray-200 px-1 rounded">email</code>.</p>
          </div>
        </div>
        <p className="text-xs text-gray-400 mt-3">Duplicate emails are automatically skipped. Download a sample to see the expected format.</p>
      </div>
    </div>
  );
}
