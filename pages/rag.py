import csv
import json
import os
import re
import sqlite3
import tomllib
from datetime import date
from pathlib import Path
from typing import Literal

import streamlit as st
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

PROJECT_DIR = Path(__file__).resolve().parents[1]
CHROMA_DIR = PROJECT_DIR / "data" / "chroma_db"
TRAINING_DATA_PATH = PROJECT_DIR / "data" / "training" / "df.csv"
DB_PATH = PROJECT_DIR / "data" / "hospital.db"

ALL_FILTER = "전체"
ETC_DISEASE = "기타"
NONE_DISEASE = "None"
DEPARTMENT_OPTIONS = [ALL_FILTER, "내과", "외과", "안과", "치과", "피부과"]


load_dotenv(PROJECT_DIR / ".env")


RAG_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """아래 [검색 데이터]를 근거로 사용자의 질문에 답하세요.
검색된 데이터에 근거해서만 간결하게 답하고, 데이터에 없는 내용은 추측하지 마세요.

[선택 조건]
{filters}

[검색 데이터]
{context}
"""),
    ("human", "{question}"),
])


@st.cache_resource(show_spinner=False)
def load_vector_db():
    embedding_model = HuggingFaceEmbeddings(
        model_name="jhgan/ko-sroberta-multitask",
        encode_kwargs={"normalize_embeddings": True},
    )
    return Chroma(
        collection_name="pet_care",
        embedding_function=embedding_model,
        persist_directory=str(CHROMA_DIR),
    )


def get_openai_api_key():
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        return api_key

    secrets_path = PROJECT_DIR / ".streamlit" / "secrets.toml"
    if not secrets_path.exists():
        return None
    with secrets_path.open("rb") as file:
        secrets = tomllib.load(file)
    return secrets.get("OPENAI_API_KEY")


@st.cache_resource(show_spinner=False)
def load_rag_chain():
    api_key = get_openai_api_key()
    if not api_key:
        return None
    return RAG_PROMPT | ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        api_key=api_key,
    ) | StrOutputParser()


@st.cache_resource(show_spinner=False)
def initialize_rag():
    db = load_vector_db()
    return db, load_rag_chain()


def build_filter_context(filters):
    labels = {
        "life_cycle": "나이 단계",
        "department": "진료과",
        "disease": "질병 종류",
    }
    items = [
        f"{labels[key]}: {value}"
        for key, value in (filters or {}).items()
        if value and value != ALL_FILTER and key in labels
    ]
    return "\n".join(items) if items else "선택 조건 없음"


def build_metadata_filter(filters):
    key_map = {
        "life_cycle": "meta.lifeCycle",
        "department": "meta.department",
        "disease": "meta.disease",
    }
    conditions = []
    for key, value in (filters or {}).items():
        if key not in key_map or not value or value == ALL_FILTER:
            continue
        if key == "disease" and value == ETC_DISEASE:
            conditions.append({"$or": [
                {"meta.disease": ETC_DISEASE},
                {"meta.disease": NONE_DISEASE},
            ]})
        else:
            conditions.append({key_map[key]: value})
    if not conditions:
        return None
    return conditions[0] if len(conditions) == 1 else {"$and": conditions}


def ask_rag(question, k=3, filters=None):
    if not question or not question.strip():
        raise ValueError("질문을 입력해 주세요.")
    db, rag_chain = initialize_rag()
    docs = db.similarity_search(
        question,
        k=k,
        filter=build_metadata_filter(filters),
    )
    context = "\n\n".join(
        f"질문: {doc.page_content}\n답변: {doc.metadata.get('qa.output', '')}"
        for doc in docs
    )
    if rag_chain is None:
        answer = "유사도 검색은 성공했습니다. 답변 생성에는 OPENAI_API_KEY가 필요합니다."
    else:
        answer = rag_chain.invoke({
            "context": context,
            "filters": build_filter_context(filters),
            "question": question,
        })
    return {"answer": answer, "evidence_rows": [doc.metadata for doc in docs]}


def format_evidence_row(row, index):
    life_cycle = row.get("meta.lifeCycle") or row.get("lifeCycle") or "-"
    department = row.get("meta.department") or row.get("department") or "-"
    disease = row.get("meta.disease") or row.get("disease") or "-"
    answer = row.get("qa.output") or row.get("answer") or ""
    return {
        "title": f"{index + 1}. {life_cycle} / {department} / {disease}",
        "body": f"**답변**\n\n{answer}",
    }


@tool
def rag_tool(question: str) -> str:
    """반려견의 증상, 질병, 치료 등 건강 관련 질문에 학습 데이터를 검색해 답합니다."""
    result = ask_rag(question, k=3)
    return result["answer"]


SQL_GENERATION_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """사용자의 병원 검색 질문을 SQLite SQL로 변환하세요.
사용할 수 있는 테이블은 hospital 하나뿐이며 컬럼은 다음과 같습니다.
ids, name, new_address, x_coor, y_coor, old_address
반드시 읽기 전용 SELECT 문 하나만 출력하세요.
주소 검색은 new_address와 old_address를 LIKE로 함께 고려하고, 결과는 최대 10개로 제한하세요.
SQL 코드 블록이나 설명 없이 SQL만 출력하세요.""",
    ),
    ("human", "{question}"),
])

SQL_ANSWER_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        "검색된 동물병원 데이터만 근거로 간결하게 답하세요. 검색 결과가 없으면 찾지 못했다고 말하세요.",
    ),
    ("human", "질문: {question}\n검색 결과: {rows}"),
])

COUNT_QUERY_KEYWORDS = ("몇개", "몇 개", "개수", "몇곳", "몇 곳", "몇군데", "몇 군데")
HOSPITAL_QUERY_KEYWORDS = ("동물병원", "병원 주소", "병원 목록", "병원 검색")
LOCATION_ALIASES = {
    "서울시": "서울특별시",
    "부산시": "부산광역시",
    "대구시": "대구광역시",
    "인천시": "인천광역시",
    "광주시": "광주광역시",
    "대전시": "대전광역시",
    "울산시": "울산광역시",
    "세종시": "세종특별자치시",
}


@st.cache_resource(show_spinner=False)
def load_chat_model():
    api_key = get_openai_api_key()
    if not api_key:
        return None
    return ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=api_key)


def validate_sql(sql: str) -> str:
    cleaned = sql.strip()
    if cleaned.startswith("```") and cleaned.endswith("```"):
        cleaned = cleaned[3:-3].strip()
    if cleaned.lower().startswith("sql"):
        cleaned = cleaned[3:].strip()

    cleaned = cleaned.rstrip(";").strip()
    normalized = cleaned.lower()
    if not normalized.startswith("select"):
        raise ValueError("읽기 전용 SELECT 문만 실행할 수 있습니다.")
    if ";" in cleaned or "--" in cleaned or "/*" in cleaned:
        raise ValueError("여러 문장이나 주석이 포함된 SQL은 실행할 수 없습니다.")
    if "hospital" not in normalized:
        raise ValueError("hospital 테이블만 조회할 수 있습니다.")
    return cleaned


def fallback_sql(question: str) -> str:
    """LLM 키가 없을 때도 기본적인 지역 병원 검색은 수행합니다."""
    keywords = extract_search_parameters(question)
    if is_count_query(question):
        if not keywords:
            return "SELECT COUNT(*) AS count FROM hospital"
        conditions = " OR ".join(
            "new_address LIKE ? OR old_address LIKE ?" for _ in keywords
        )
        return f"SELECT COUNT(*) AS count FROM hospital WHERE {conditions}"

    if not keywords:
        return "SELECT name, new_address, old_address FROM hospital LIMIT 10"
    conditions = " OR ".join(
        "new_address LIKE ? OR old_address LIKE ?" for _ in keywords
    )
    return f"SELECT name, new_address, old_address FROM hospital WHERE {conditions} LIMIT 10"


def is_count_query(question: str) -> bool:
    normalized = "".join(question.lower().split())
    return any("".join(keyword.split()) in normalized for keyword in COUNT_QUERY_KEYWORDS)


def is_hospital_question(question: str) -> bool:
    normalized = " ".join(question.lower().split())
    compact = "".join(normalized.split())
    if "동물병원" in compact:
        return True
    return any(keyword in normalized for keyword in HOSPITAL_QUERY_KEYWORDS)


def extract_search_parameters(question: str) -> list[str]:
    locations = re.findall(
        r"[가-힣]+(?:특별시|광역시|특별자치시|특별자치도|도|시|군|구|동|읍|면)",
        question,
    )
    if len(locations) > 1:
        specific_locations = [
            location
            for location in locations
            if not location.endswith(("특별시", "광역시", "특별자치시", "도", "시"))
        ]
        if specific_locations:
            locations = specific_locations
    return list(dict.fromkeys(LOCATION_ALIASES.get(location, location) for location in locations))


def format_sql_result(data: list[dict]) -> str:
    if len(data) == 1 and "count" in data[0]:
        return f"조건에 맞는 동물병원은 {data[0]['count']}개입니다."
    return json.dumps(data, ensure_ascii=False)


@tool
def sql_tool(question: str) -> str:
    """지역, 주소, 병원명으로 동물병원 SQLite 데이터를 검색합니다."""
    model = load_chat_model()
    parameters = extract_search_parameters(question)

    if model is None or is_count_query(question):
        sql = fallback_sql(question)
    else:
        sql = (SQL_GENERATION_PROMPT | model | StrOutputParser()).invoke(
            {"question": question}
        )

    sql = validate_sql(sql)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    try:
        if parameters and "?" in sql:
            values = [f"%{word}%" for word in parameters for _ in range(2)]
            rows = connection.execute(sql, values).fetchall()
        else:
            rows = connection.execute(sql).fetchall()
    finally:
        connection.close()

    data = [dict(row) for row in rows]
    if model is None:
        return format_sql_result(data)
    return (SQL_ANSWER_PROMPT | model | StrOutputParser()).invoke(
        {"question": question, "rows": json.dumps(data, ensure_ascii=False)}
    )


class RouteDecision(BaseModel):
    route: Literal["rag", "sql", "none"] = Field(
        description="rag: 건강/질병, sql: 병원 검색, none: 인사 및 기타 대화"
    )


ROUTER_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """질문을 사용할 도구로 분류하세요.
- rag: 반려견 증상, 질병, 치료, 건강 정보
- sql: 동물병원 이름, 주소, 지역, 병원 목록 검색
- none: 인사, 감사, 자기소개, 기능 문의 등 도구가 필요 없는 질문
인사말은 별도 직접 응답 분기로 만들지 말고 반드시 none으로 분류하세요.""",
    ),
    ("human", "{question}"),
])


OUT_OF_SCOPE_KEYWORDS = ("날씨", "기온", "미세먼지", "뉴스", "주식", "환율")
AGE_PATTERN = re.compile(r"(\d+)\s*(개월|살|세)")
DEPARTMENT_KEYWORDS = {
    "내과": (
        "내과",
        "구토",
        "토해",
        "설사",
        "소화",
        "식욕",
        "복통",
        "복부",
        "기침",
        "호흡",
        "열",
        "발열",
        "당뇨",
        "간",
        "신장",
    ),
    "외과": ("외과", "골절", "절뚝", "파행", "상처", "수술", "탈구", "다리"),
    "안과": ("안과", "눈", "눈곱", "충혈", "결막", "각막", "백내장"),
    "치과": ("치과", "치아", "잇몸", "구강", "입냄새", "치석"),
    "피부과": ("피부과", "피부", "가려", "긁", "털", "탈모", "발진", "귀"),
}


def is_date_question(question: str) -> bool:
    normalized = "".join(question.lower().split())
    return "날짜" in normalized or "며칠" in normalized or "몇일" in normalized


def current_date_answer() -> str:
    today = date.today()
    return f"오늘은 {today.year}년 {today.month}월 {today.day}일입니다."


def is_out_of_scope_question(question: str) -> bool:
    normalized = "".join(question.lower().split())
    return any(keyword in normalized for keyword in OUT_OF_SCOPE_KEYWORDS)


def classify_question(question: str) -> str:
    if is_out_of_scope_question(question):
        return "none"
    if is_hospital_question(question):
        return "sql"

    model = load_chat_model()
    if model is not None:
        decision = (ROUTER_PROMPT | model.with_structured_output(RouteDecision)).invoke(
            {"question": question}
        )
        return decision.route

    normalized = question.lower()
    if any(word in normalized for word in ("병원", "주소", "지역", "동물병원")):
        return "sql"
    if any(word in normalized for word in ("증상", "질병", "아파", "구토", "치료")):
        return "rag"
    return "none"


def answer_without_tool(question: str) -> str:
    model = load_chat_model()
    if model is None:
        return "안녕하세요. 반려견 건강이나 동물병원에 관해 질문해 주세요."
    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "도구가 필요하지 않은 일반 대화에 짧고 자연스럽게 답하세요. 의료 정보를 추측해서 답하지 마세요.",
        ),
        ("human", "{question}"),
    ])
    return (prompt | model | StrOutputParser()).invoke({"question": question})


def infer_life_cycle_filter(question: str) -> str | None:
    for age_text, unit in AGE_PATTERN.findall(question):
        age = int(age_text)
        if unit == "개월":
            return "자견" if age <= 12 else "성견"
        if age <= 1:
            return "자견"
        if 2 <= age <= 6:
            return "성견"
        return "노령견"
    return None


def infer_department_filter(question: str) -> str | None:
    normalized = question.lower()
    for department in DEPARTMENT_OPTIONS:
        if department != "전체" and department in normalized:
            return department

    compact = "".join(normalized.split())
    for department, keywords in DEPARTMENT_KEYWORDS.items():
        if any(keyword in compact for keyword in keywords):
            return department
    return None


def infer_rag_filters(question: str) -> dict[str, str]:
    filters = {}
    life_cycle = infer_life_cycle_filter(question)
    department = infer_department_filter(question)
    if life_cycle:
        filters["life_cycle"] = life_cycle
    if department:
        filters["department"] = department
    return filters


def chatbot(
    question: str,
    *,
    top_k: int = 3,
) -> dict[str, str]:
    """질문을 분류한 뒤 rag, sql, 또는 도구 없는 일반 응답을 실행합니다."""
    if not question or not question.strip():
        raise ValueError("질문을 입력해 주세요.")

    if is_date_question(question):
        return {"route": "none", "answer": current_date_answer()}

    route = classify_question(question)
    if route == "rag":
        rag_result = ask_rag(question, k=top_k, filters=infer_rag_filters(question))
        return {
            "route": route,
            "answer": rag_result["answer"],
            "evidence_rows": rag_result["evidence_rows"],
        }
    elif route == "sql":
        answer = sql_tool.invoke({"question": question})
    else:
        answer = answer_without_tool(question)
    return {"route": route, "answer": answer}


def render_page():
    st.title("반려견 AI 상담")
    st.caption("질병 질문은 RAG로, 병원 검색은 SQLite로 처리합니다.")

    top_k = st.slider(
        "참고할 근거 수",
        min_value=1,
        max_value=5,
        value=3,
        key="rag_top_k",
    )

    if "fixing_messages" not in st.session_state:
        st.session_state.fixing_messages = []
    for message in st.session_state.fixing_messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    question = st.chat_input(
        "예: 강아지가 계속 구토해요 / 강남구 병원을 알려주세요."
    )
    if not question:
        return

    st.session_state.fixing_messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.write(question)
    with st.chat_message("assistant"):
        try:
            with st.spinner(
                " 답변을 생성하는 중입니다. 잠시만 기다리세요"
            ):
                result = chatbot(question, top_k=top_k)

            st.write(result["answer"])
            st.session_state.fixing_messages.append(
                {"role": "assistant", "content": result["answer"]}
            )

            evidence_rows = result.get("evidence_rows", [])
            if evidence_rows:
                st.markdown("#### 검색 근거")
                for index, row in enumerate(evidence_rows):
                    evidence = format_evidence_row(row, index)
                    with st.expander(evidence["title"]):
                        st.markdown(evidence["body"])
        except Exception as exc:
            st.error(f"실행 중 오류가 발생했습니다: {exc}")


def is_streamlit_runtime():
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx
    except Exception:
        return False
    return get_script_run_ctx(suppress_warning=True) is not None


if is_streamlit_runtime():
    render_page()
