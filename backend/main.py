from fastapi import FastAPI, Request, HTTPException, Path, Body, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os, requests, random, string
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client

import LLM_topic_decider

load_dotenv()

SUPABASE_URL     = os.getenv("SUPABASE_URL")
SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
BACKEND_PORT     = int(os.getenv("BACKEND_PORT", "8000"))

if not SUPABASE_URL or not SERVICE_ROLE_KEY:
    raise RuntimeError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")

supabase = create_client(SUPABASE_URL, SERVICE_ROLE_KEY)

app = FastAPI(title="AdaptiveLearning API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── helpers ──────────────────────────────────────────────────────────────────

def get_user(request: Request):
    token = request.headers.get("authorization", "").replace("Bearer ", "").strip()
    if not token:
        raise HTTPException(401, "Missing token")
    resp = requests.get(f"{SUPABASE_URL}/auth/v1/user", headers={"Authorization": f"Bearer {token}"})
    if resp.status_code != 200:
        raise HTTPException(401, "Invalid token")
    return resp.json()

def rand_code(n=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=n))


# ─── models ──────────────────────────────────��────────────────────────────────

class StartSessionRequest(BaseModel):
    title: str | None = None

class AnswerPayload(BaseModel):
    question_id:    str
    selected_index: int
    correct:        bool

class CreateClassRequest(BaseModel):
    name: str

class JoinClassRequest(BaseModel):
    join_code: str

class LinkChildRequest(BaseModel):
    child_id: str  # parent submits the kid's user_id


# ─── questions ────────────────────────────────────────────────────────────────

@app.get("/api/questions")
def get_questions(limit: int = 100, subject: str | None = None, difficulty: str | None = None):
    q = supabase.table("questions").select("*").limit(limit)
    if subject:    q = q.eq("subject", subject)
    if difficulty: q = q.eq("difficulty", difficulty)
    res = q.execute()
    return res.data or []


# ─── llm generation ────────────────────────────────────────────────────────────────
@app.get("/api/generate-question")
def generate_question(user_id: str = Query(...)):
    # user_id = requests.request.args.get("user_id")
    # if not user_id:
    #     return jsonify({"error": "Missing user_id"}), 400
    question = LLM_topic_decider.LLM_topic_decider(user_id)

    if not question:
        raise HTTPException(status_code=500, detail="Failed to generate question")
    return question


# ─── sessions ─────────────────────────────────────────────────────────────────

@app.post("/api/sessions/start")
def start_session(payload: StartSessionRequest, request: Request):
    user = get_user(request)
    obj  = {
        "user_id":            user["id"],
        "title":              payload.title or "Practice Session",
        "started_at":         datetime.utcnow().isoformat(),
        "questions_answered": 0,
        "correct_answers":    0,
    }
    res = supabase.table("sessions").insert(obj).execute()
    return res.data[0]

@app.post("/api/sessions/{session_id}/answer")
def record_answer(session_id: str = Path(...), payload: AnswerPayload = Body(...), request: Request = None):
    user = get_user(request)
    supabase.table("session_answers").insert({
        "session_id":     session_id,
        "user_id":        user["id"],
        "question_id":    payload.question_id,
        "selected_index": payload.selected_index,
        "correct":        payload.correct,
        "answered_at":    datetime.utcnow().isoformat(),
    }).execute()
    sess = supabase.table("sessions").select("*").eq("id", session_id).single().execute()
    if not sess.data:
        raise HTTPException(404, "Session not found")
    cur = sess.data
    supabase.table("sessions").update({
        "questions_answered": (cur.get("questions_answered") or 0) + 1,
        "correct_answers":    (cur.get("correct_answers") or 0) + (1 if payload.correct else 0),
    }).eq("id", session_id).execute()
    return {"ok": True}

@app.post("/api/sessions/{session_id}/end")
def end_session(session_id: str = Path(...), request: Request = None):
    user = get_user(request)
    sess = supabase.table("sessions").select("*").eq("id", session_id).single().execute()
    if not sess.data:
        raise HTTPException(404, "Session not found")
    data = sess.data
    supabase.table("sessions").update({"ended_at": datetime.utcnow().isoformat()}).eq("id", session_id).execute()

    total_q = data.get("questions_answered") or 0
    correct  = data.get("correct_answers")   or 0

    # upsert user_stats
    existing = supabase.table("user_stats").select("*").eq("user_id", user["id"]).execute()
    if existing.data:
        s = existing.data[0]
        supabase.table("user_stats").update({
            "total_questions": (s.get("total_questions") or 0) + total_q,
            "total_correct":   (s.get("total_correct")   or 0) + correct,
            "last_session_at": datetime.utcnow().isoformat(),
            "updated_at":      datetime.utcnow().isoformat(),
        }).eq("user_id", user["id"]).execute()
    else:
        supabase.table("user_stats").insert({
            "user_id":          user["id"],
            "total_questions":  total_q,
            "total_correct":    correct,
            "current_streak":   0,
            "best_streak":      0,
            "last_session_at":  datetime.utcnow().isoformat(),
        }).execute()
    return {"ok": True}

@app.get("/api/sessions")
def list_sessions(request: Request):
    user = get_user(request)
    res  = supabase.table("sessions").select("*").eq("user_id", user["id"]).order("started_at", desc=True).execute()
    return res.data or []


# ─── stats ────────────────────────────────────────────────────────────────────

@app.get("/api/stats/me")
def my_stats(request: Request):
    user = get_user(request)
    res  = supabase.table("user_stats").select("*").eq("user_id", user["id"]).execute()
    if not res.data:
        return {"total_questions": 0, "total_correct": 0, "current_streak": 0, "best_streak": 0}
    return res.data[0]

@app.get("/api/stats/student/{student_id}")
def student_stats(student_id: str, request: Request):
    # parents and teachers can call this
    get_user(request)
    res = supabase.table("user_stats").select("*").eq("user_id", student_id).execute()
    if not res.data:
        return {"total_questions": 0, "total_correct": 0, "current_streak": 0, "best_streak": 0}
    return res.data[0]

@app.get("/api/sessions/student/{student_id}")
def student_sessions(student_id: str, request: Request):
    get_user(request)
    res = supabase.table("sessions").select("*").eq("user_id", student_id).order("started_at", desc=True).limit(20).execute()
    return res.data or []

@app.get("/api/performance/student/{student_id}")
def student_performance(student_id: str, request: Request):
    get_user(request)
    res = supabase.table("user_math_performance") \
        .select("*, math_topics(topic_name)") \
        .eq("user_id", student_id).execute()
    return res.data or []


# ─── leaderboard ─────────────────────────────────────────────────────────────

@app.get("/api/leaderboard")
def leaderboard(request: Request, limit: int = 20):
    get_user(request)
    # query user_stats joined with auth metadata via supabase admin
    res = supabase.table("user_stats") \
        .select("user_id, total_correct, total_questions, current_streak, best_streak") \
        .order("total_correct", desc=True) \
        .limit(limit) \
        .execute()
    rows = res.data or []
    # fetch display names from auth.users via admin API
    enriched = []
    for i, row in enumerate(rows):
        uid = row["user_id"]
        try:
            u = supabase.auth.admin.get_user_by_id(uid)
            email    = u.user.email or ""
            metadata = u.user.user_metadata or {}
            name     = metadata.get("display_name") or email.split("@")[0]
        except Exception:
            name = "Unknown"
        enriched.append({**row, "display_name": name, "rank": i + 1})
    return enriched


# ─── classes ─────────────────────────────────────────────────────────────────

@app.post("/api/classes")
def create_class(payload: CreateClassRequest, request: Request):
    user = get_user(request)
    if user.get("user_metadata", {}).get("role") != "teacher":
        raise HTTPException(403, "Only teachers can create classes")
    code = rand_code()
    # keep trying until unique
    for _ in range(5):
        existing = supabase.table("classes").select("id").eq("join_code", code).execute()
        if not existing.data:
            break
        code = rand_code()
    res = supabase.table("classes").insert({
        "teacher_id": user["id"],
        "name":       payload.name,
        "join_code":  code,
    }).execute()
    return res.data[0]

@app.get("/api/classes")
def my_classes(request: Request):
    user = get_user(request)
    role = user.get("user_metadata", {}).get("role", "student")
    if role == "teacher":
        res = supabase.table("classes").select("*, class_memberships(count)").eq("teacher_id", user["id"]).execute()
    else:
        # return classes the student is in
        memberships = supabase.table("class_memberships").select("class_id").eq("student_id", user["id"]).execute()
        ids = [m["class_id"] for m in (memberships.data or [])]
        if not ids:
            return []
        res = supabase.table("classes").select("*").in_("id", ids).execute()
    return res.data or []

@app.post("/api/classes/join")
def join_class(payload: JoinClassRequest, request: Request):
    user = get_user(request)
    cls  = supabase.table("classes").select("*").eq("join_code", payload.join_code.upper()).execute()
    if not cls.data:
        raise HTTPException(404, "Class not found — check the code")
    class_id = cls.data[0]["id"]
    # check not already joined
    already = supabase.table("class_memberships").select("id") \
        .eq("class_id", class_id).eq("student_id", user["id"]).execute()
    if already.data:
        raise HTTPException(409, "Already in this class")
    supabase.table("class_memberships").insert({
        "class_id":  class_id,
        "student_id": user["id"],
    }).execute()
    return cls.data[0]

@app.get("/api/classes/{class_id}/students")
def class_students(class_id: str, request: Request):
    user = get_user(request)
    memberships = supabase.table("class_memberships").select("student_id, joined_at") \
        .eq("class_id", class_id).execute()
    students = []
    for m in (memberships.data or []):
        sid = m["student_id"]
        stats_res = supabase.table("user_stats").select("*").eq("user_id", sid).execute()
        stats = stats_res.data[0] if stats_res.data else {"total_questions": 0, "total_correct": 0, "current_streak": 0}
        try:
            u    = supabase.auth.admin.get_user_by_id(sid)
            email = u.user.email or ""
            meta  = u.user.user_metadata or {}
            name  = meta.get("display_name") or email.split("@")[0]
        except Exception:
            name  = "Unknown"
            email = ""
        students.append({
            "user_id":   sid,
            "name":      name,
            "email":     email,
            "joined_at": m["joined_at"],
            **stats,
        })
    return students


# ─── parent endpoints ─────────────────────────────────────────────────────────

@app.post("/api/parent/link-child")
def link_child(payload: LinkChildRequest, request: Request):
    user = get_user(request)
    if user.get("user_metadata", {}).get("role") != "parent":
        raise HTTPException(403, "Only parents can link children")
    # verify child exists
    try:
        child = supabase.auth.admin.get_user_by_id(payload.child_id)
        if not child.user:
            raise HTTPException(404, "Child account not found")
        if child.user.user_metadata.get("role") != "student":
            raise HTTPException(400, "That account is not a student")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(404, "Child account not found")
    # check not already linked
    already = supabase.table("parent_child_links").select("id") \
        .eq("parent_id", user["id"]).eq("child_id", payload.child_id).execute()
    if already.data:
        raise HTTPException(409, "Already linked to this child")
    supabase.table("parent_child_links").insert({
        "parent_id": user["id"],
        "child_id":  payload.child_id,
    }).execute()
    return {"ok": True, "child_id": payload.child_id, "child_name": child.user.email.split("@")[0]}

@app.get("/api/parent/children")
def my_children(request: Request):
    user = get_user(request)
    links = supabase.table("parent_child_links").select("child_id, created_at") \
        .eq("parent_id", user["id"]).execute()
    children = []
    for lnk in (links.data or []):
        cid = lnk["child_id"]
        stats_res = supabase.table("user_stats").select("*").eq("user_id", cid).execute()
        stats = stats_res.data[0] if stats_res.data else {"total_questions": 0, "total_correct": 0, "current_streak": 0, "best_streak": 0}
        sess_res = supabase.table("sessions").select("*").eq("user_id", cid).order("started_at", desc=True).limit(5).execute()
        perf_res = supabase.table("user_math_performance").select("*, math_topics(topic_name)").eq("user_id", cid).execute()
        try:
            u    = supabase.auth.admin.get_user_by_id(cid)
            email = u.user.email or ""
            meta  = u.user.user_metadata or {}
            name  = meta.get("display_name") or email.split("@")[0]
        except Exception:
            name  = "Unknown"
            email = ""
        children.append({
            "user_id":     cid,
            "name":        name,
            "email":       email,
            "linked_at":   lnk["created_at"],
            "stats":       stats,
            "sessions":    sess_res.data or [],
            "performance": perf_res.data or [],
        })
    return children


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=BACKEND_PORT, reload=True)