from fastapi import FastAPI, HTTPException, Depends, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, timezone
import os
import uuid

from .security import hash_password, verify_password, create_access_token, decode_access_token
from .storage import JsonStore, atomic_write


DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))
USERS_PATH = os.path.join(DATA_DIR, 'users.json')
QUIZZES_PATH = os.path.join(DATA_DIR, 'quizzes.json')
RESULTS_PATH = os.path.join(DATA_DIR, 'results.json')

os.makedirs(DATA_DIR, exist_ok=True)


class UserCreate(BaseModel):
    name: str = Field(min_length=1)
    email: EmailStr
    password: str = Field(min_length=6)
    role: str = Field(pattern=r"^(student|admin)$")


class User(BaseModel):
    id: str
    name: str
    email: EmailStr
    password_hash: str
    role: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class QuizQuestion(BaseModel):
    id: str
    text: str
    options: List[str] = Field(min_items=4, max_items=4)
    correct_option_index: int = Field(ge=0, le=3)


class QuizCreate(BaseModel):
    title: str
    description: str
    time_limit_minutes: int = Field(ge=1, le=240)
    questions: List[QuizQuestion]


class Quiz(BaseModel):
    id: str
    title: str
    description: str
    time_limit_minutes: int
    questions: List[QuizQuestion]


class PublicQuizQuestion(BaseModel):
    id: str
    text: str
    options: List[str]


class PublicQuiz(BaseModel):
    id: str
    title: str
    description: str
    time_limit_minutes: int
    questions: List[PublicQuizQuestion]


class StartAttemptResponse(BaseModel):
    attempt_id: str
    start_time: str


class Answer(BaseModel):
    question_id: str
    chosen_index: int


class SubmitRequest(BaseModel):
    attempt_id: str
    answers: List[Answer]


class SubmitResult(BaseModel):
    score: int
    total: int
    details: List[Dict[str, Any]]


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

app = FastAPI(title="Quiz API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


users_store = JsonStore(USERS_PATH, default=[])  # list[User]
quizzes_store = JsonStore(QUIZZES_PATH, default=[])  # list[Quiz]
results_store = JsonStore(RESULTS_PATH, default=[])  # list[result]


def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    payload = decode_access_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    users = users_store.read()
    user = next((u for u in users if u["id"] == user_id), None)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return User(**user)


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")
    return user


def require_student(user: User = Depends(get_current_user)) -> User:
    if user.role != "student":
        raise HTTPException(status_code=403, detail="Student role required")
    return user


@app.get("/api/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


def _ensure_seed_data():
    users = users_store.read()
    if not any(u.get("role") == "admin" for u in users):
        admin = User(
            id=str(uuid.uuid4()),
            name="Admin User",
            email="admin@example.com",
            password_hash=hash_password("Admin123!"),
            role="admin",
        )
        users.append(admin.model_dump())
        users_store.write(users)
    quizzes = quizzes_store.read()
    if not quizzes:
        sample_quiz = Quiz(
            id=str(uuid.uuid4()),
            title="Sample JavaScript Basics",
            description="A quick check on JS fundamentals",
            time_limit_minutes=5,
            questions=[
                QuizQuestion(id=str(uuid.uuid4()), text="What is the result of typeof null?", options=["'null'", "'object'", "'undefined'", "'number'"], correct_option_index=1),
                QuizQuestion(id=str(uuid.uuid4()), text="Which method converts JSON to JS object?", options=["JSON.parse", "JSON.stringify", "toObject", "fromJSON"], correct_option_index=0),
                QuizQuestion(id=str(uuid.uuid4()), text="Which keyword declares a block-scoped variable?", options=["var", "const", "function", "with"], correct_option_index=1),
            ],
        )
        quizzes.append(sample_quiz.model_dump())
        quizzes_store.write(quizzes)


_ensure_seed_data()


@app.post("/api/auth/signup", response_model=Dict[str, str])
def signup(data: UserCreate):
    users = users_store.read()
    if any(u["email"].lower() == data.email.lower() for u in users):
        raise HTTPException(status_code=400, detail="Email already registered")

    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        name=data.name,
        email=data.email,
        password_hash=hash_password(data.password),
        role=data.role,
    )
    users.append(user.model_dump())
    users_store.write(users)
    return {"message": "User created. You can now log in."}


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@app.post("/api/auth/login", response_model=TokenResponse)
def login(data: LoginRequest):
    users = users_store.read()
    user = next((u for u in users if u["email"].lower() == data.email.lower()), None)
    if not user or not verify_password(data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": user["id"], "role": user["role"]})
    return TokenResponse(access_token=token)


@app.get("/api/quizzes", response_model=List[PublicQuiz])
def list_quizzes():
    quizzes = [Quiz(**q) for q in quizzes_store.read()]
    public = [
        PublicQuiz(
            id=q.id,
            title=q.title,
            description=q.description,
            time_limit_minutes=q.time_limit_minutes,
            questions=[PublicQuizQuestion(id=qq.id, text=qq.text, options=qq.options) for qq in q.questions],
        )
        for q in quizzes
    ]
    return public


@app.get("/api/quizzes/{quiz_id}", response_model=PublicQuiz)
def get_quiz(quiz_id: str):
    q = next((Quiz(**q) for q in quizzes_store.read() if q["id"] == quiz_id), None)
    if not q:
        raise HTTPException(status_code=404, detail="Quiz not found")
    return PublicQuiz(
        id=q.id,
        title=q.title,
        description=q.description,
        time_limit_minutes=q.time_limit_minutes,
        questions=[PublicQuizQuestion(id=qq.id, text=qq.text, options=qq.options) for qq in q.questions],
    )


@app.post("/api/quizzes", response_model=Quiz)
def create_quiz(data: QuizCreate, _: User = Depends(require_admin)):
    quiz = Quiz(
        id=str(uuid.uuid4()),
        title=data.title,
        description=data.description,
        time_limit_minutes=data.time_limit_minutes,
        questions=[QuizQuestion(**qq.model_dump()) for qq in data.questions],
    )
    quizzes = quizzes_store.read()
    quizzes.append(quiz.model_dump())
    quizzes_store.write(quizzes)
    return quiz


@app.put("/api/quizzes/{quiz_id}", response_model=Quiz)
def update_quiz(quiz_id: str, data: QuizCreate, _: User = Depends(require_admin)):
    quizzes = quizzes_store.read()
    idx = next((i for i, q in enumerate(quizzes) if q["id"] == quiz_id), None)
    if idx is None:
        raise HTTPException(status_code=404, detail="Quiz not found")
    updated = Quiz(id=quiz_id, **data.model_dump())
    quizzes[idx] = updated.model_dump()
    quizzes_store.write(quizzes)
    return updated


@app.delete("/api/quizzes/{quiz_id}", response_model=Dict[str, str])
def delete_quiz(quiz_id: str, _: User = Depends(require_admin)):
    quizzes = quizzes_store.read()
    new_quizzes = [q for q in quizzes if q["id"] != quiz_id]
    if len(new_quizzes) == len(quizzes):
        raise HTTPException(status_code=404, detail="Quiz not found")
    quizzes_store.write(new_quizzes)
    return {"message": "Deleted"}


@app.post("/api/quizzes/{quiz_id}/start", response_model=StartAttemptResponse)
def start_attempt(quiz_id: str, user: User = Depends(require_student)):
    quiz = next((q for q in quizzes_store.read() if q["id"] == quiz_id), None)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    attempt_id = str(uuid.uuid4())
    start_time = datetime.now(timezone.utc).isoformat()
    results = results_store.read()
    results.append({
        "id": attempt_id,
        "quiz_id": quiz_id,
        "user_id": user.id,
        "start_time": start_time,
        "end_time": None,
        "answers": [],
        "score": None,
    })
    results_store.write(results)
    return StartAttemptResponse(attempt_id=attempt_id, start_time=start_time)


@app.post("/api/quizzes/{quiz_id}/submit", response_model=SubmitResult)
def submit_attempt(quiz_id: str, payload: SubmitRequest, user: User = Depends(require_student)):
    # Load quiz and attempt
    quiz_data = next((q for q in quizzes_store.read() if q["id"] == quiz_id), None)
    if not quiz_data:
        raise HTTPException(status_code=404, detail="Quiz not found")
    results = results_store.read()
    attempt = next((r for r in results if r["id"] == payload.attempt_id and r["quiz_id"] == quiz_id and r["user_id"] == user.id), None)
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")
    if attempt.get("end_time"):
        raise HTTPException(status_code=400, detail="Attempt already submitted")

    # Time limit check
    try:
        started = datetime.fromisoformat(attempt["start_time"])
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid attempt start time")
    now = datetime.now(timezone.utc)
    time_limit = timedelta(minutes=int(quiz_data["time_limit_minutes"]))
    if now - started > time_limit + timedelta(seconds=5):  # small grace window
        raise HTTPException(status_code=400, detail="Time limit exceeded")

    # Grade
    quiz = Quiz(**quiz_data)
    question_by_id = {q.id: q for q in quiz.questions}
    correct = 0
    details: List[Dict[str, Any]] = []
    for ans in payload.answers:
        q = question_by_id.get(ans.question_id)
        if not q:
            continue
        is_correct = int(ans.chosen_index) == int(q.correct_option_index)
        correct += 1 if is_correct else 0
        details.append({
            "question_id": q.id,
            "chosen_index": ans.chosen_index,
            "correct_index": q.correct_option_index,
            "is_correct": is_correct,
        })

    attempt["answers"] = [a.model_dump() for a in payload.answers]
    attempt["end_time"] = now.isoformat()
    attempt["score"] = correct
    # persist
    for i, r in enumerate(results):
        if r["id"] == attempt["id"]:
            results[i] = attempt
            break
    results_store.write(results)

    return SubmitResult(score=correct, total=len(quiz.questions), details=details)


@app.get("/api/quizzes/{quiz_id}/results")
def quiz_results(quiz_id: str, _: User = Depends(require_admin)):
    results = [r for r in results_store.read() if r.get("quiz_id") == quiz_id and r.get("end_time")]
    return results


# Admin-only bulk import (optional nice-to-have)
class QuizImport(BaseModel):
    quizzes: List[QuizCreate]


@app.post("/api/quizzes/import")
def import_quizzes(payload: QuizImport, _: User = Depends(require_admin)):
    quizzes = quizzes_store.read()
    created = []
    for qc in payload.quizzes:
        q = Quiz(
            id=str(uuid.uuid4()),
            title=qc.title,
            description=qc.description,
            time_limit_minutes=qc.time_limit_minutes,
            questions=[QuizQuestion(**qq.model_dump()) for qq in qc.questions],
        )
        quizzes.append(q.model_dump())
        created.append(q.model_dump())
    quizzes_store.write(quizzes)
    return {"created": len(created)}


