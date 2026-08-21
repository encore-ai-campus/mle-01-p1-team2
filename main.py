import os
os.environ.setdefault("ARROW_DEFAULT_MEMORY_POOL", "system")
import streamlit as st

st.set_page_config(page_title="PetCare AI", page_icon=":material/pets:", layout="wide")

with st.sidebar:
    st.session_state.sidebar_slot = st.empty()
    st.divider()

pg = st.navigation(
    {
        "소개페이지": [
            st.Page("pages/home.py", title="home", icon="🏠", default=True),
        ],
        "데이터 소개": [
            st.Page("pages/data.py", title="데이터 소개", icon="📊"),
        ],
        "챗봇": [
            st.Page("pages/rag.py", title="질병 문의", icon="💬"),
            st.Page("pages/hospital.py", title="병원 검색", icon="🏥"),
        ],
    }
)

pg.run()