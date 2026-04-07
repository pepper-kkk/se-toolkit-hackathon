from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
FRONTEND_DIR = PROJECT_ROOT / "frontend"
IMAGES_DIR = FRONTEND_DIR / "images"

load_dotenv(PROJECT_ROOT / ".env")
raw_db_path = Path(os.getenv("SQLITE_DB_PATH", "data/ecotales.db"))
DB_PATH = raw_db_path if raw_db_path.is_absolute() else PROJECT_ROOT / raw_db_path


TOPIC_CONFIG: dict[str, dict] = {
    "water_pollution": {
        "code": "1",
        "label": {"ru": "Загрязнение воды", "en": "Water pollution"},
        "text": {
            "ru": (
                "Проблема загрязнения воды пластиком стала особенно актуальной. "
                "Пластиковые отходы не разлагаются быстро и могут вредить здоровью людей и животных. "
                "Важно использовать многоразовые бутылки, не оставлять мусор у воды и объяснять детям, "
                "как простые ежедневные привычки помогают сохранять водные ресурсы."
            ),
            "en": (
                "Plastic pollution in water is a serious problem. "
                "Plastic waste does not decompose quickly and can harm people and wildlife. "
                "Using reusable bottles, keeping rivers and lakes clean, and teaching eco habits to children "
                "are practical steps to protect water resources."
            ),
        },
    },
    "recycling": {
        "code": "3",
        "label": {"ru": "Переработка", "en": "Recycling"},
        "text": {
            "ru": (
                "Переработка помогает получать новые материалы из отходов и снижает нагрузку на природу. "
                "Разделяйте бумагу, пластик и стекло, используйте контейнеры для вторсырья и давайте вещам "
                "вторую жизнь. Такие шаги формируют экологическое мышление у детей."
            ),
            "en": (
                "Recycling helps turn waste into useful materials and reduces pressure on nature. "
                "Sort paper, plastic, and glass, use recycling bins, and reuse items whenever possible. "
                "These simple actions build strong environmental habits in children."
            ),
        },
    },
    "clean_air": {
        "code": "4",
        "label": {"ru": "Чистый воздух", "en": "Clean air"},
        "text": {
            "ru": (
                "Чистый воздух важен для здоровья детей и взрослых. "
                "Высаживайте растения, не сжигайте мусор и выбирайте пешие прогулки на коротких расстояниях. "
                "Обсуждайте с детьми, как загрязнение воздуха влияет на людей, животных и растения."
            ),
            "en": (
                "Clean air is essential for everyone’s health. "
                "Plant trees, avoid burning waste, and choose walking for short trips when possible. "
                "Discuss with children how air pollution affects people, animals, and plants."
            ),
        },
    },
    "eco_habits": {
        "code": "5",
        "label": {"ru": "Эко-привычки", "en": "Eco habits"},
        "text": {
            "ru": (
                "Экологические привычки формируются через ежедневные действия: прогулки на природе, "
                "уход за растениями, бережное отношение к воде и энергии. "
                "Личный пример семьи помогает детям осознанно заботиться об окружающей среде."
            ),
            "en": (
                "Eco habits grow through daily actions: nature walks, gardening, and careful use of water and energy. "
                "A positive family example helps children understand how to care for the environment in real life."
            ),
        },
    },
    "protecting_animals": {
        "code": "2",
        "label": {"ru": "Защита животных", "en": "Protecting animals"},
        "text": {
            "ru": (
                "Защита животных начинается с уважения к их среде обитания. "
                "Не оставляйте мусор в лесах и парках, поддерживайте чистоту водоемов и рассказывайте детям, "
                "почему важно сохранять биоразнообразие и безопасные места для диких животных."
            ),
            "en": (
                "Protecting animals starts with respecting their habitats. "
                "Keep forests, parks, and rivers clean, and teach children why biodiversity matters. "
                "Small responsible actions help wildlife stay safe."
            ),
        },
    },
}


class MaterialRequest(BaseModel):
    topic: str = Field(min_length=1, max_length=100)
    language: str = Field(min_length=2, max_length=2)
    content_type: str = Field(min_length=4, max_length=20)


class MaterialResponse(BaseModel):
    topic: str
    topic_label: str
    language: str
    content_type: str
    result_value: str
    created_at: str


def get_db_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with get_db_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS material_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic TEXT NOT NULL,
                language TEXT NOT NULL,
                content_type TEXT NOT NULL,
                result_value TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.commit()


def find_checklist_image(topic_code: str, language: str) -> str | None:
    lang_token = "англ" if language == "en" else "рус"

    for image_file in IMAGES_DIR.glob(f"{topic_code}_*"):
        if lang_token in image_file.name.lower():
            return f"/images/{image_file.name}"

    return None


def resolve_material(topic: str, language: str, content_type: str) -> tuple[str, str]:
    if topic not in TOPIC_CONFIG:
        raise HTTPException(status_code=400, detail="Unsupported topic")

    if language not in {"ru", "en"}:
        raise HTTPException(status_code=400, detail="Unsupported language")

    if content_type not in {"text", "checklist"}:
        raise HTTPException(status_code=400, detail="Unsupported content_type")

    topic_data = TOPIC_CONFIG[topic]
    topic_label = topic_data["label"][language]

    if content_type == "text":
        return topic_label, topic_data["text"][language]

    checklist_path = find_checklist_image(topic_data["code"], language)
    if not checklist_path:
        raise HTTPException(
            status_code=404,
            detail="Checklist is not available for selected topic/language",
        )
    return topic_label, checklist_path


def save_request(
    topic: str,
    language: str,
    content_type: str,
    result_value: str,
    created_at: str,
) -> None:
    with get_db_connection() as connection:
        connection.execute(
            """
            INSERT INTO material_requests (topic, language, content_type, result_value, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (topic, language, content_type, result_value, created_at),
        )
        connection.commit()


def read_history(limit: int = 10) -> list[dict]:
    with get_db_connection() as connection:
        rows = connection.execute(
            """
            SELECT topic, language, content_type, result_value, created_at
            FROM material_requests
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return [dict(row) for row in rows]


app = FastAPI(title="EcoTales Materials API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/api/material", response_model=MaterialResponse)
def material(request_data: MaterialRequest) -> MaterialResponse:
    topic = request_data.topic.strip()
    language = request_data.language.strip().lower()
    content_type = request_data.content_type.strip().lower()

    topic_label, result_value = resolve_material(topic, language, content_type)

    created_at = datetime.now(timezone.utc).isoformat()
    save_request(
        topic=topic,
        language=language,
        content_type=content_type,
        result_value=result_value,
        created_at=created_at,
    )

    return MaterialResponse(
        topic=topic,
        topic_label=topic_label,
        language=language,
        content_type=content_type,
        result_value=result_value,
        created_at=created_at,
    )


@app.get("/api/history")
def history(limit: int = 10) -> dict:
    safe_limit = max(1, min(limit, 50))
    return {"items": read_history(limit=safe_limit)}


app.mount("/data", StaticFiles(directory=DATA_DIR), name="data")

if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
