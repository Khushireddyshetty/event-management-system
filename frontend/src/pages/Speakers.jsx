import React,{useEffect,useState} from "react";
import {MdAdd,MdPerson,MdAutoAwesome} from "react-icons/md";
import {toast} from "react-toastify";
import API from "../api/axios.js";
import {PageHeader,LoadingState,EmptyState,ErrorState,Modal,CardActions,getList,value} from "../components/OperationsUI.jsx";

const blank={name:"",designation:"",organization:"",email:"",phone:"",expertise:"",availability_start:"09:00",availability_end:"17:00",rating:"4.5",biography:""};
function Form({initial,onSave,onClose,saving}){
  const [f,setF]=useState({...blank,...initial});
  const set=(key,val)=>setF(prev=>({...prev,[key]:val}));
  return <form onSubmit={e=>{e.preventDefault();onSave({...f,rating:Number(f.rating||0)})}} className="grid sm:grid-cols-2 gap-4">
    {Object.entries(blank).map(([key])=><label className="label" key={key}>{key.replaceAll("_"," ")}
      <input required={["name","email","expertise"].includes(key)} type={key==="rating"?"number":key==="email"?"email":"text"} min={key==="rating"?0:undefined} max={key==="rating"?5:undefined} step={key==="rating"?.5:undefined} className="input mt-1" value={f[key]||""} onChange={e=>set(key,e.target.value)}/>
    </label>)}
    <div className="sm:col-span-2 flex justify-end gap-2"><button type="button" onClick={onClose} className="btn-secondary">Cancel</button><button disabled={saving} className="btn-primary">{saving?"Saving…":"Save speaker"}</button></div>
  </form>;
}
export default function Speakers(){
  const[items,setItems]=useState([]),[loading,setLoading]=useState(true),[error,setError]=useState(false),[modal,setModal]=useState(null),[saving,setSaving]=useState(false),[form,setForm]=useState({topic:"",required_expertise:"",start_time:"",end_time:""}),[result,setResult]=useState(null);
  const load=()=>{setLoading(true);API.get("/speakers").then(r=>setItems(getList(r.data,["speakers"]))).catch(()=>setError(true)).finally(()=>setLoading(false))};
  useEffect(load,[]);
  const save=async f=>{setSaving(true);try{modal?.id?await API.put(`/speakers/${modal.id}`,f):await API.post("/speakers",f);toast.success("Speaker saved");setModal(null);load()}catch(e){toast.error(e.message)}finally{setSaving(false)}};
  const del=async id=>{if(!window.confirm("Delete this speaker?"))return;try{await API.delete(`/speakers/${id}`);toast.success("Speaker deleted");load()}catch(e){toast.error(e.message)}};
  const rec=async e=>{e.preventDefault();try{const r=await API.post("/speakers/recommend",form);setResult(getList(r.data,["recommendations","speakers"]))}catch(e){toast.error(e.message)}};
  return <div className="page-enter"><PageHeader eyebrow="Milestone 2 · People" title="Speaker operations" description="Manage profiles, expertise and workload before the room fills." action={<button onClick={()=>setModal({})} className="btn-primary inline-flex gap-2 items-center"><MdAdd/> Add speaker</button>}/>
    {loading?<LoadingState/>:error?<ErrorState onRetry={()=>{setError(false);load()}}/>:!items.length?<EmptyState title="No speakers yet" text="Create a speaker profile to power recommendations." action={<button onClick={()=>setModal({})} className="btn-primary">Add speaker</button>}/>:<div className="grid md:grid-cols-2 gap-4">{items.map(s=><div className="card" key={s.id}><div className="flex justify-between"><div className="flex gap-3"><div className="w-10 h-10 rounded-xl bg-indigo-100 text-indigo-600 flex items-center justify-center"><MdPerson/></div><div><h3 className="font-bold">{value(s,["name"])}</h3><p className="text-xs text-gray-400">{value(s,["designation"])} · {value(s,["organization"])}</p></div></div><CardActions onEdit={()=>setModal(s)} onDelete={()=>del(s.id)}/></div><p className="text-sm text-gray-600 mt-4 line-clamp-2">{value(s,["biography"],"No biography added")}</p><div className="flex flex-wrap gap-2 mt-4"><span className="badge bg-violet-100 text-violet-700">{value(s,["expertise"])}</span><span className="badge bg-emerald-100 text-emerald-700">Rating {value(s,["rating"])}</span><span className="badge bg-amber-100 text-amber-700">{value(s,["assigned_sessions"],0)} sessions</span></div><p className="text-xs text-gray-400 mt-3">Availability: {value(s,["availability_start"])}–{value(s,["availability_end"])} · {value(s,["email"])}</p></div>)}</div>}
    <div className="card mt-6"><div className="flex items-center gap-2 mb-4"><MdAutoAwesome className="text-violet-600"/><h3 className="font-bold">Recommend a speaker</h3></div><form onSubmit={rec} className="grid sm:grid-cols-4 gap-3">{Object.entries(form).map(([k,v])=><label className="label" key={k}>{k.replaceAll("_"," ")}<input required className="input mt-1" type={k.includes("time")?"datetime-local":"text"} value={v} onChange={e=>setForm(x=>({...x,[k]:e.target.value}))}/></label>)}<button className="btn-primary self-end">Find match</button></form>{result?.length>0&&<div className="mt-4 space-y-2">{result.slice(0,3).map(s=><div className="p-3 rounded-xl bg-violet-50 text-sm" key={s.id}><strong>{s.name}</strong> · {s.match_score}% match — {s.reason}</div>)}</div>}</div>
    {modal&&<Modal title={modal.id?"Edit speaker":"Add speaker"} onClose={()=>setModal(null)}><Form initial={modal} onSave={save} onClose={()=>setModal(null)} saving={saving}/></Modal>}
  </div>;
}