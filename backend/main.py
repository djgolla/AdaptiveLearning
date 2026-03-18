from fastapi import FastAPI, Request, HTTPException, Path
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import requests
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8000"))

if not SUPABASE_URL or not SERVICE_ROLE_KEY:
    raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in environment")

supabase = create_client(SUPABASE_URL, SERVICE_ROLE_KEY)

app = FastAPI(title="AdaptiveLearning Backend")

# allow local dev and deployment of any fe
origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "*",  # for dev
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_user_from_token(access_token: str):
    """
    Returns the user object for a given Supabase access token.
    Uses Supabase Auth REST endpoint /auth/v1/user
    """
    if not access_token:
        return None
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"{SUPABASE_URL}/auth/v1/user"
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        return None
    return resp.json()


class StartSessionRequest(BaseModel):
    title: str | None = None


class AnswerPayload(BaseModel):
    question_id: str
    selected_index: int
    correct: bool


@app.get("/api/questions")
def get_questions(limit: int = 10, subject: str | None = None, difficulty: str | None = None):
    q = supabase.table("questions").select("*").limit(limit)
    if subject:
        q = q.eq("subject", subject)
    if difficulty:
        q = q.eq("difficulty", difficulty)
    res = q.execute()
    if res.error:
        raise HTTPException(status_code=500, detail=res.error.message)
    return res.data


@app.post("/api/sessions/start")
def start_session(payload: StartSessionRequest, request: Request):
    token = request.headers.get("authorization", "").replace("Bearer ", "")
    user = get_user_from_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or missing token")

    session_obj = {
        "user_id": user["id"],
        "title": payload.title or "Practice Session",
        "started_at": datetime.utcnow().isoformat(),
        "questions_answered": 0,
        "correct_answers": 0,
    }
    res = supabase.table("sessions").insert(session_obj).execute()
    if res.error:
        raise HTTPException(status_code=500, detail=res.error.message)
    return res.data[0]


@app.post("/api/sessions/{session_id}/answer")
def record_answer(session_id: str = Path(...), payload: AnswerPayload = None, request: Request = None):
    token = request.headers.get("authorization", "").replace("Bearer ", "")
    user = get_user_from_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or missing token")

    # insert record into session_answers
    ans = {
        "session_id": session_id,
        "user_id": user["id"],
        "question_id": payload.question_id,
        "selected_index": payload.selected_index,
        "correct": payload.correct,
        "answered_at": datetime.utcnow().isoformat(),
    }
    res = supabase.table("session_answers").insert(ans).execute()
    if res.error:
        raise HTTPException(status_code=500, detail=res.error.message)

    # update sessions table counters
    inc = {"questions_answered": 1}
    if payload.correct:
        inc["correct_answers"] = 1
    # fetch current and increment
    sess = supabase.table("sessions").select("*").eq("id", session_id).single().execute()
    if sess.error or not sess.data:
        raise HTTPException(status_code=404, detail="Session not found")
    current = sess.data
    update_data = {
        "questions_answered": (current.get("questions_answered") or 0) + 1,
        "correct_answers": (current.get("correct_answers") or 0) + (1 if payload.correct else 0),
    }
    upd = supabase.table("sessions").update(update_data).eq("id", session_id).execute()
    if upd.error:
        raise HTTPException(status_code=500, detail=upd.error.message)

    return {"ok": True}
@app.post("/api/sessions/{session_id}/end")
def end_session(session_id: str = Path(...), request: Request = None):
    token = request.headers.get("authorization", "").replace("Bearer ", "")
    user = get_user_from_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or missing token")

    sess = supabase.table("sessions").select("*").eq("id", session_id).single().execute()
    if sess.error or not sess.data:
        raise HTTPException(status_code=404, detail="Session not found")
    data = sess.data
    ended_at = datetime.utcnow().isoformat()
    # update session
    upd = supabase.table("sessions").update({"ended_at": ended_at}).eq("id", session_id).execute()
    if upd.error:
        raise HTTPException(status_code=500, detail=upd.error.message)

    # upsert user_stats
    total_q = data.get("questions_answered") or 0
    correct = data.get("correct_answers") or 0
    # fetch stats
    stats = supabase.table("user_stats").select("*").eq("user_id", user["id"]).single().execute()
    if stats.error and "Results contain 0 rows" not in str(stats.error):
        # if other::
        pass

    if stats.data:
        new_total_questions = (stats.data.get("total_questions") or 0) + total_q
        new_total_correct = (stats.data.get("total_correct") or 0) + correct
        supabase.table("user_stats").update({
            "total_questions": new_total_questions,
            "total_correct": new_total_correct
        }).eq("user_id", user["id"]).execute()
    else:
        supabase.table("user_stats").insert({
            "user_id": user["id"],
            "total_questions": total_q,
            "total_correct": correct,
            "current_streak": 0,
            "best_streak": 0
        }).execute()

    return {"ok": True}


@app.get("/api/stats/me")
def my_stats(request: Request):
    token = request.headers.get("authorization", "").replace("Bearer ", "")
    user = get_user_from_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or missing token")

    res = supabase.table("user_stats").select("*").eq("user_id", user["id"]).single().execute()
    if res.error and "Results contain 0 rows" in str(res.error):
        return {"total_questions": 0, "total_correct": 0, "current_streak": 0, "best_streak": 0}
    if res.error:
        raise HTTPException(status_code=500, detail=res.error.message)
    return res.data


@app.get("/api/sessions")
def list_sessions(request: Request):
    token = request.headers.get("authorization", "").replace("Bearer ", "")
    user = get_user_from_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or missing token")

    res = supabase.table("sessions").select("*").eq("user_id", user["id"]).order("started_at", desc=True).execute()
    if res.error:
        raise HTTPException(status_code=500, detail=res.error.message)
    return res.data


@app.post("/api/llm/generate")
def llm_generate(count: int = 1, request: Request = None):
    """
    Generate `count` questions using OpenAI and insert into questions table.
    Requires OPENAI_API_KEY. Returns newly created questions.
    """
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=403, detail="LLM generation not enabled on server")

    #call OpenAI to generate a JSON question set
    try:
        import openai
        openai.api_key = OPENAI_API_KEY
        prompts = []
        created = []
        for _ in range(count):
            prompt = (
                "Create one short multiple-choice algebra question in JSON with fields: "
                "question_text, options (array of 4 strings), correct_index (0-3), difficulty, subject. "
                "Keep options concise."
            )
            resp = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{"role":"user","content": prompt}],
                max_tokens=400,
                temperature=0.3,
            )
            text = resp["choices"][0]["message"]["content"]
            # attempt to load JSON from text
            import json
            try:
                qobj = json.loads(text)
            except Exception:
                # naive fallback: wrap text fields
                qobj = {"question_text": text.strip(), "options": ["A","B","C","D"], "correct_index": 0, "difficulty":"medium", "subject":"math"}
            # insert
            ins = supabase.table("questions").insert(qobj).execute()
            if ins.error:
                continue
            created.append(ins.data[0])
        return {"created": created}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=BACKEND_PORT, reload=True)