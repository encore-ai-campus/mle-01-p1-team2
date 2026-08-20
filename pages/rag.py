import os
import tomllib
import csv
from pathlib import Path

from dotenv import load_dotenv
import streamlit as st
from langchain_chroma import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI


PROJECT_DIR = Path(__file__).resolve().parents[1]
CHROMA_DIR = PROJECT_DIR / "data" / "chroma_db"
TRAINING_DATA_PATH = PROJECT_DIR / "data" / "training" / "df.csv"

ALL_FILTER = "전체"
ETC_DISEASE = "기타"
NONE_DISEASE = "None"
LIFE_CYCLE_OPTIONS = [ALL_FILTER, "노령견", "자견", "성견"]
DEPARTMENT_OPTIONS = [ALL_FILTER, "내과", "외과", "안과", "치과", "피부과"]

load_dotenv(PROJECT_DIR / ".env")

PROMPT = ChatPromptTemplate.from_messages([
    ("system", """아래 [검색 데이터]를 근거로 사용자의 질문에 답하세요.
규칙:
1. 검색된 데이터에 근거해서만 답변하세요.
2. 데이터에 없는 내용은 임의로 추측하지 마세요.
3. 답변은 간결하게 작성하세요.
4. [선택 조건]이 있으면 해당 조건을 우선 고려하세요.

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
    return PROMPT | ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=api_key) | StrOutputParser()


def selected_filter_items(filters):
    if not filters:
        return []

    labels = {
        "life_cycle": "나이 단계",
        "department": "진료과",
        "disease": "질병 종류",
    }
    return [
        (labels[key], value)
        for key, value in filters.items()
        if value and value != ALL_FILTER and key in labels
    ]


def build_filter_context(filters):
    items = selected_filter_items(filters)
    if not items:
        return "선택 조건 없음"
    return "\n".join(f"{label}: {value}" for label, value in items)


def build_search_query(question, filters=None):
    filter_context = build_filter_context(filters)
    if filter_context == "선택 조건 없음":
        return question
    return f"{question}\n{filter_context}"


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
            conditions.append({
                "$or": [
                    {"meta.disease": ETC_DISEASE},
                    {"meta.disease": NONE_DISEASE},
                ]
            })
            continue
        conditions.append({key_map[key]: value})

    if not conditions:
        return None
    if len(conditions) == 1:
        return conditions[0]
    return {"$and": conditions}


def normalize_disease_options(diseases):
    normalized = {
        ETC_DISEASE if disease == NONE_DISEASE else disease
        for disease in diseases
        if disease
    }
    options = sorted(disease for disease in normalized if disease != ETC_DISEASE)
    if ETC_DISEASE in normalized:
        options.append(ETC_DISEASE)
    return [ALL_FILTER, *options]


def load_disease_options():
    if not TRAINING_DATA_PATH.exists():
        return [ALL_FILTER]

    with TRAINING_DATA_PATH.open(encoding="utf-8", newline="") as file:
        diseases = {
            row.get("meta.disease", "").strip()
            for row in csv.DictReader(file)
            if row.get("meta.disease", "").strip()
        }

    return normalize_disease_options(diseases)

def ask_rag(question, k=3, filters=None):
    if not question or not question.strip():
        raise ValueError("질문을 입력해 주세요.")

    search_query = build_search_query(question, filters)
    metadata_filter = build_metadata_filter(filters)
    docs = load_vector_db().similarity_search(
        search_query,
        k=k,
        filter=metadata_filter,
    )
    context = "\n\n".join(
        f"질문: {doc.page_content}\n답변: {doc.metadata.get('qa.output', '')}"
        for doc in docs
    )

    rag_chain = load_rag_chain()
    if rag_chain is None:
        answer = "유사도 검색은 성공했습니다. 답변 생성에는 OPENAI_API_KEY가 필요합니다."
    else:
        answer = rag_chain.invoke({
            "context": context,
            "filters": build_filter_context(filters),
            "question": question,
        })

    evidence_rows = [doc.metadata for doc in docs]
    return {"answer": answer, "evidence_rows": evidence_rows}


def format_evidence_row(row, index):
    life_cycle = row.get("meta.lifeCycle") or row.get("lifeCycle") or "-"
    department = row.get("meta.department") or row.get("department") or "-"
    disease = row.get("meta.disease") or row.get("disease") or "-"
    answer = row.get("qa.output") or row.get("answer") or ""

    return {
        "title": f"{index + 1}. {life_cycle} / {department} / {disease}",
        "body": f"**답변**\n\n{answer}",
    }


def render_rag_page():
    st.title("질병 문의")
    st.caption("반려견 증상을 질문하면 학습 데이터에서 관련 사례를 찾고, 검색 근거를 바탕으로 답변합니다.")

    filter_col1, filter_col2, filter_col3, filter_col4 = st.columns([1, 1, 1, 1])
    with filter_col1:
        life_cycle = st.selectbox("나이 단계", LIFE_CYCLE_OPTIONS)
    with filter_col2:
        department = st.selectbox("진료과", DEPARTMENT_OPTIONS)
    with filter_col3:
        disease = st.selectbox("질병 종류", load_disease_options())
    with filter_col4:
        top_k = st.slider("참고할 근거 수", min_value=1, max_value=5, value=3)

    filters = {
        "life_cycle": life_cycle,
        "department": department,
        "disease": disease,
    }

    if "rag_messages" not in st.session_state:
        st.session_state.rag_messages = []

    for message in st.session_state.rag_messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    question = st.chat_input("예: 강아지가 계속 구토해요")
    if not question:
        return

    st.session_state.rag_messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.write(question)

    with st.chat_message("assistant"):
        try:
            with st.spinner("관련 사례를 검색하고 답변을 생성하는 중입니다..."):
                result = ask_rag(question, k=top_k, filters=filters)
        except Exception as exc:
            st.error(f"RAG 실행 중 오류가 발생했습니다: {exc}")
            return

        st.write(result["answer"])
        st.session_state.rag_messages.append(
            {"role": "assistant", "content": result["answer"]}
        )

        if result["evidence_rows"]:
            st.markdown("#### 검색 근거")
            for index, row in enumerate(result["evidence_rows"]):
                evidence = format_evidence_row(row, index)
                with st.expander(evidence["title"]):
                    st.markdown(evidence["body"])


def is_streamlit_runtime():
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx
    except Exception:
        return False
    return get_script_run_ctx(suppress_warning=True) is not None


if is_streamlit_runtime():
    render_rag_page()
