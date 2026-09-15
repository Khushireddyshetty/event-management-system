import React from "react";
import { MdClose, MdDeleteOutline, MdEdit, MdRefresh } from "react-icons/md";

export function PageHeader({ eyebrow, title, description, action }) {
  return <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 mb-6">
    <div><p className="text-xs font-bold uppercase tracking-[.18em] text-violet-500">{eyebrow}</p><h2 className="text-2xl font-bold text-gray-800 mt-1">{title}</h2><p className="text-sm text-gray-500 mt-1">{description}</p></div>{action}
  </div>;
}
export function LoadingState() { return <div className="grid grid-cols-1 md:grid-cols-2 gap-4">{[1,2,3,4].map(i=><div key={i} className="card animate-pulse h-44 bg-violet-50/40"><div className="h-4 bg-violet-100 rounded w-1/3 mb-4"/><div className="h-3 bg-violet-100 rounded w-2/3 mb-3"/><div className="h-3 bg-violet-100 rounded w-1/2"/></div>)}</div>; }
export function EmptyState({ title, text, action }) { return <div className="card text-center py-14 border-dashed"><div className="mx-auto w-12 h-12 rounded-2xl bg-violet-100 text-violet-600 flex items-center justify-center text-xl">+</div><h3 className="font-semibold text-gray-700 mt-3">{title}</h3><p className="text-sm text-gray-400 mt-1">{text}</p>{action && <div className="mt-4">{action}</div>}</div>; }
export function ErrorState({ onRetry }) { return <div className="card text-center py-10"><p className="text-rose-500 font-medium">Could not load this workspace.</p><button onClick={onRetry} className="btn-secondary mt-4 inline-flex items-center gap-2"><MdRefresh/> Retry</button></div>; }
export function Modal({ title, onClose, children }) { return <div className="fixed inset-0 z-50 bg-slate-950/40 p-4 flex items-center justify-center"><div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto"><div className="px-5 py-4 border-b flex justify-between items-center"><h3 className="font-bold text-gray-800">{title}</h3><button aria-label="Close" onClick={onClose} className="p-2 rounded-lg hover:bg-gray-100"><MdClose/></button></div><div className="p-5">{children}</div></div></div>; }
export function CardActions({ onEdit, onDelete }) { return <div className="flex gap-1"><button aria-label="Edit" onClick={onEdit} className="p-2 text-violet-500 hover:bg-violet-50 rounded-lg"><MdEdit/></button><button aria-label="Delete" onClick={onDelete} className="p-2 text-rose-500 hover:bg-rose-50 rounded-lg"><MdDeleteOutline/></button></div>; }
export const getList = (data, keys) => { if (Array.isArray(data)) return data; for (const k of keys) if (Array.isArray(data?.[k])) return data[k]; return []; };
export const value = (obj, keys, fallback="—") => { for (const k of keys) if (obj?.[k] !== undefined && obj?.[k] !== null && obj?.[k] !== "") return obj[k]; return fallback; };