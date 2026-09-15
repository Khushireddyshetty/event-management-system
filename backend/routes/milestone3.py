"""Milestone 3 sponsorship, incident, alert and rule-based AI APIs."""
from datetime import datetime
from flask import Blueprint, jsonify, request
from database import get_db

m3_bp = Blueprint("milestone3", __name__)

def rows(conn, sql, args=()):
    return [dict(r) for r in conn.execute(sql, args).fetchall()]

def body():
    return request.get_json(silent=True) or {}

@m3_bp.route("/sponsors", methods=["GET", "POST"])
def sponsors():
    conn = get_db()
    if request.method == "POST":
        d = body()
        if not d.get("name") or not d.get("company"):
            conn.close(); return jsonify(error="Name and company are required."), 400
        cur = conn.execute("""INSERT INTO sponsors
          (name,company,contact_person,email,phone,tier,amount,contract_status,payment_status,
           benefits,deliverables,deliverable_status,event_name,start_date,end_date,performance_score,roi,notes)
          VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
          tuple(d.get(k, "") for k in ["name","company","contact_person","email","phone","tier"]) +
          (float(d.get("amount", 0) or 0), d.get("contract_status","Prospect"), d.get("payment_status","Pending"),
           d.get("benefits",""), d.get("deliverables",""), d.get("deliverable_status","Pending"), d.get("event_name",""),
           d.get("start_date",""), d.get("end_date",""), float(d.get("performance_score",0) or 0), float(d.get("roi",0) or 0), d.get("notes","")))
        conn.commit(); item = dict(conn.execute("SELECT * FROM sponsors WHERE id=?", (cur.lastrowid,)).fetchone()); conn.close()
        return jsonify(item), 201
    data = rows(conn, "SELECT * FROM sponsors ORDER BY amount DESC"); conn.close(); return jsonify({"sponsors": data})

@m3_bp.route("/sponsors/<int:item_id>", methods=["PUT", "DELETE"])
def sponsor(item_id):
    conn = get_db()
    if request.method == "DELETE":
        conn.execute("DELETE FROM sponsors WHERE id=?", (item_id,)); conn.commit(); conn.close(); return jsonify(ok=True)
    d = body()
    allowed = ["name","company","contact_person","email","phone","tier","amount","contract_status","payment_status","benefits","deliverables","deliverable_status","event_name","start_date","end_date","performance_score","roi","notes"]
    sets = ", ".join(f"{k}=?" for k in allowed if k in d)
    vals = [d[k] for k in allowed if k in d]
    if sets: conn.execute(f"UPDATE sponsors SET {sets} WHERE id=?", vals+[item_id]); conn.commit()
    item = conn.execute("SELECT * FROM sponsors WHERE id=?", (item_id,)).fetchone(); conn.close()
    return (jsonify(dict(item)) if item else (jsonify(error="Sponsor not found."),404))

@m3_bp.route("/sponsors/analytics")
def sponsor_analytics():
    conn=get_db(); data=rows(conn,"SELECT * FROM sponsors"); conn.close()
    return jsonify({"total":len(data),"active":sum(x["contract_status"] in ("Active","Confirmed") for x in data),
      "revenue":sum(x["amount"] or 0 for x in data),"average_performance":round(sum(x["performance_score"] or 0 for x in data)/len(data),1) if data else 0,
      "roi":round(sum(x["roi"] or 0 for x in data)/len(data),2) if data else 0,
      "pending_payments":sum(x["payment_status"]!="Paid" for x in data),"pending_deliverables":sum(x["deliverable_status"]!="Complete" for x in data)})

@m3_bp.route("/incidents", methods=["GET","POST"])
def incidents():
    conn=get_db()
    if request.method=="POST":
        d=body()
        if not d.get("title"): conn.close(); return jsonify(error="Title is required."),400
        sev=d.get("severity","Medium"); priority=d.get("priority") or {"Critical":"Critical","High":"High","Medium":"Medium","Low":"Low"}.get(sev,"Medium")
        cur=conn.execute("""INSERT INTO incidents (title,description,category,location,event_name,reported_by,assigned_to,priority,severity,status,due_date,comments)
          VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""", tuple(d.get(k,"") for k in ["title","description","category","location","event_name","reported_by","assigned_to"]) + (priority,sev,d.get("status","Open"),d.get("due_date",""),d.get("comments","")))
        conn.commit(); item=dict(conn.execute("SELECT * FROM incidents WHERE id=?",(cur.lastrowid,)).fetchone()); conn.close(); return jsonify(item),201
    data=rows(conn,"SELECT * FROM incidents ORDER BY CASE priority WHEN 'Critical' THEN 1 WHEN 'High' THEN 2 WHEN 'Medium' THEN 3 ELSE 4 END, updated_at DESC"); conn.close(); return jsonify({"incidents":data})

@m3_bp.route("/incidents/<int:item_id>", methods=["PUT","DELETE"])
def incident(item_id):
    conn=get_db()
    if request.method=="DELETE": conn.execute("DELETE FROM incidents WHERE id=?",(item_id,)); conn.commit(); conn.close(); return jsonify(ok=True)
    d=body(); allowed=["title","description","category","location","assigned_to","priority","severity","status","due_date","resolution_notes","comments"]
    sets=", ".join(f"{k}=?" for k in allowed if k in d)+", updated_at=datetime('now','localtime')"; vals=[d[k] for k in allowed if k in d]
    if d.get("status") in ("Resolved","Closed"): sets+=", resolution_date=datetime('now','localtime')"
    conn.execute(f"UPDATE incidents SET {sets} WHERE id=?",vals+[item_id]); conn.commit(); item=conn.execute("SELECT * FROM incidents WHERE id=?",(item_id,)).fetchone(); conn.close(); return jsonify(dict(item))

@m3_bp.route("/incidents/<int:item_id>/escalate", methods=["POST"])
def escalate(item_id):
    conn=get_db(); conn.execute("UPDATE incidents SET escalation_level=MIN(escalation_level+1,3), status='Escalated', priority=CASE WHEN priority='Low' THEN 'Medium' WHEN priority='Medium' THEN 'High' ELSE priority END, updated_at=datetime('now','localtime') WHERE id=?",(item_id,)); conn.commit(); item=conn.execute("SELECT * FROM incidents WHERE id=?",(item_id,)).fetchone(); conn.close(); return jsonify(dict(item))

@m3_bp.route("/alerts")
def alerts():
    conn=get_db(); data=rows(conn,"SELECT * FROM operational_alerts ORDER BY CASE severity WHEN 'Critical' THEN 1 WHEN 'High' THEN 2 ELSE 3 END, created_at DESC"); conn.close(); return jsonify({"alerts":data})

@m3_bp.route("/alerts/<int:item_id>/<action>", methods=["PUT"])
def alert_action(item_id, action):
    status={"acknowledge":"Acknowledged","resolve":"Resolved"}.get(action)
    if not status: return jsonify(error="Unknown alert action."),400
    conn=get_db(); conn.execute("UPDATE operational_alerts SET status=? WHERE id=?",(status,item_id)); conn.commit(); item=conn.execute("SELECT * FROM operational_alerts WHERE id=?",(item_id,)).fetchone(); conn.close(); return jsonify(dict(item))

@m3_bp.route("/monitoring")
def monitoring():
    conn=get_db(); s=rows(conn,"SELECT * FROM sponsors"); i=rows(conn,"SELECT * FROM incidents"); a=rows(conn,"SELECT * FROM operational_alerts"); conn.close()
    return jsonify({"active_sponsors":sum(x["contract_status"] in ("Active","Confirmed") for x in s),"revenue":sum(x["amount"] for x in s),"open_incidents":sum(x["status"] not in ("Resolved","Closed") for x in i),"critical_incidents":sum(x["priority"]=="Critical" for x in i),"active_alerts":sum(x["status"]!="Resolved" for x in a),"pending_deliverables":sum(x["deliverable_status"]!="Complete" for x in s),"pending_payments":sum(x["payment_status"]!="Paid" for x in s),"incidents_by_priority":{p:sum(x["priority"]==p for x in i) for p in ["Critical","High","Medium","Low"]}})

@m3_bp.route("/ai/<kind>", methods=["POST"])
def ai(kind):
    conn=get_db(); sponsors_data=rows(conn,"SELECT * FROM sponsors"); incidents_data=rows(conn,"SELECT * FROM incidents"); conn.close()
    q=(body().get("question") or "").lower()
    if kind=="sponsorship":
        best=max(sponsors_data,key=lambda x:x["roi"],default=None)
        answer=f"{best['company']} has the highest ROI at {best['roi']}x." if best and "roi" in q else f"There are {len(sponsors_data)} sponsors generating ₹{sum(x['amount'] for x in sponsors_data):,.0f}. Follow up on payment and deliverable risks." 
    elif kind=="incident":
        critical=[x for x in incidents_data if x["priority"] in ("Critical","High") and x["status"] not in ("Resolved","Closed")]
        answer=f"{len(critical)} incidents require immediate attention: "+", ".join(x["title"] for x in critical) if critical else "No unresolved high-risk incidents. Continue routine monitoring."
    else: answer="Prioritize the Hall B crowd response, follow up with CloudNine, and close the badge-printer issue with IT."
    return jsonify({"answer":answer,"mode":"local rule-based fallback"})