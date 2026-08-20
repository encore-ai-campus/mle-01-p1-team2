import os
os.environ.setdefault("ARROW_DEFAULT_MEMORY_POOL", "system")
#from fil import Image
import streamlit as st

st.title("🐶 동물 구조대")

if "messages" not in st.session_state:
    st.session_state.messages = []

st.markdown(
    """
***동물 구조대

- **📊 데이터 대시보드**: 펭귄 데이터 필터·지표·차트
- **💬 챗봇**: 기존 챗봇 시스템(core.chatbot_core) 연동
- **📚 문서 Q&A**: 기존 RAG 시스템(core.rag_core) 연동, 답변 + 출처

멀티페이지의 핵심:
1. 엔트리(`main.py`)에서 `st.navigation` 으로 페이지 등록
2. 각 페이지는 `pages/` 폴더의 독립 파일
3. 페이지 사이에 공유할 값은 `st.session_state` 에 둔다(예: 대화 이력)
"""
)

st.info("사이드바에서 원하는 화면을 선택해 보세요.")