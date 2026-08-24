# 🐾 동물 건강 관리 챗봇

> RAG 기반 반려동물 건강 정보 질의응답 챗봇

## 📌 프로젝트 소개

반려동물의 건강 및 질병 관련 정보를 기반으로  
사용자의 질문에 적절한 정보를 검색하고 답변하는  
RAG 기반 챗봇입니다.

Streamlit으로 웹 UI를 구성했으며,  
반려동물 건강 상담, 동물병원 검색, 반려동물 보고서 분석 기능을 제공합니다.

## 🎯 프로젝트 목표

- 반려동물 건강 정보 검색 자동화
- LLM의 환각 문제 완화
- 신뢰할 수 있는 문서 기반 답변 제공
- 동물병원 데이터 기반 검색 기능 제공
- 반려동물 관련 보고서 분석 지원

## 🛠 기술 스택

- Python
- Streamlit
- LangChain
- ChromaDB
- OpenAI
- HuggingFace Embeddings
- SQLite
- Pandas
- Plotly
- RAG

## 🏗 시스템 구조

```text
사용자 질문
↓
Query Processing
↓
Embedding
↓
ChromaDB 검색
↓
Relevant Documents
↓
LLM
↓
답변
```

동물병원 검색 질문은 별도 SQL 검색 흐름을 사용합니다.

```text
사용자 질문
↓
질문 분류
↓
지역/병원 검색 조건 추출
↓
SQLite 검색
↓
동물병원 정보 반환
```

## 📂 프로젝트 구조

```text
.
├── main.py
├── pages/
│   ├── home.py
│   ├── rag.py
│   ├── hospital.py
│   └── data.py
├── src/
│   ├── ui.py
│   ├── keys.py
│   ├── fonts.py
│   ├── data_utils.py
│   └── data_charts.py
├── data/
│   ├── df.csv
│   ├── df_val.csv
│   ├── hospital.db
│   ├── hospital_completed.csv
│   ├── chroma_db/
│   └── 2025 한국 반려동물 보고서.pdf
├── notebooks/
│   ├── pdf_to_vectordb.ipynb
│   ├── rag_retrieval_evaluation.ipynb
│   ├── docs/
│   └── outputs/
├── tests/
│   ├── test_rag_refactor_helpers.py
│   └── test_rag_secrets.py
├── pyproject.toml
└── README.md
```

## 📊 데이터

- AI Hub 반려견 성장 및 질병 관련 말뭉치
- KB 2025 반려동물 보고서
- 공공데이터포털 동물병원 데이터

## 🚀 실행 방법

### 1. 의존성 설치

```bash
uv sync
```

### 2. OpenAI API Key 설정

`.streamlit/secrets.toml` 파일에 OpenAI API Key를 설정합니다.

```toml
OPENAI_API_KEY = "..."
```

또는 환경 변수로 설정할 수 있습니다.

```bash
OPENAI_API_KEY=...
```

### 3. Streamlit 실행

```bash
uv run streamlit run main.py
```

### 4. 테스트 실행

```bash
uv run python -m unittest discover -s tests -v
```

## 💡 주요 기능

### 1. 반려동물 건강 RAG 챗봇

- 반려동물 건강 및 질병 관련 질문 응답
- ChromaDB 기반 유사 문서 검색
- 검색 문서 기반 답변 생성
- 대화 기록을 반영한 후속 질문 처리

### 2. 동물병원 검색

- 지역명, 병원명 기반 동물병원 검색
- SQLite 기반 동물병원 데이터 조회
- 병원 주소 및 링크 정보 제공

### 3. 반려동물 보고서 분석

- KB 2025 반려동물 보고서 기반 질의응답
- 통계, 추이, 비교, 비중 관련 질문 처리
- 보고서 문서 검색 결과 기반 답변 생성

### 4. 데이터 시각화

- 질병 분포 시각화
- 진료과 분포 시각화
- 지역별 동물병원 분포 시각화

## 👤 담당 업무

- ...
- ...
- ...

## 📈 결과

- RAG 답변 유사도 평가 결과: `notebooks/docs/rag_answer_similarity_evaluation.md`
- 평가 산출물: `notebooks/outputs/`
- ...

## 🔧 트러블슈팅

### 문제 1

문제 → OpenAI API Key가 없을 때 답변 생성이 제한됨  
원인 → `.streamlit/secrets.toml` 또는 환경 변수에 `OPENAI_API_KEY`가 설정되지 않음  
해결 → secrets 파일 또는 환경 변수에 API Key 추가

### 문제 2

문제 → RAG 검색 결과가 질문 의도와 다르게 나옴  
원인 → 검색 쿼리, 메타데이터 필터, 벡터 DB 품질의 영향  
해결 → validation 데이터 기반 검색 성능 평가 및 chunking 방식 개선

### 문제 3

문제 → ...

원인 → ...

해결 → ...

## 🔮 향후 개선

- RAG 검색 정확도 개선
- chunking 전략 고도화
- validation 데이터 기반 정량 평가 강화
- 동물병원 검색 UX 개선
- 배포 환경 구성
- ...

