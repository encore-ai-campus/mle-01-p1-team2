import os
os.environ.setdefault("ARROW_DEFAULT_MEMORY_POOL", "system")
from getpass import getpass
from pathlib import Path
from pprint import pprint

import streamlit as st

import chromadb
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI

def main() -> None:
    st.set_page_config(page_title="PetCare AI", page_icon=":material/pets:", layout="wide")
    init_state()

    st.title("PetCare AI", anchor=False)
    st.caption("반려동물 상태 안내와 동물병원 정보 제공")
    if st.session_state.petcare_booking_message:
        st.success(st.session_state.petcare_booking_message, icon=":material/check_circle:")
        st.session_state.petcare_booking_message = None

    with st.sidebar:
        st.header("반려동물 프로필", anchor=False)
        breed = st.selectbox("품종", ["말티즈", "푸들", "포메라니안", "고양이", "기타"])
        lifecycle = st.segmented_control("생애주기", ["어린 반려동물", "성견/성묘", "노령"], default="성견/성묘")
        neutered = st.segmented_control("중성화 여부", ["중성화함", "중성화하지 않음"], default="중성화함")
        symptoms = st.multiselect("주 증상", ["구토", "설사", "무기력", "기침", "피부", "보행 이상", "일반 상담"])
        duration = st.selectbox("증상 기간", ["오늘", "1~2일", "3일 이상", "알 수 없음"])
        severity = st.selectbox("활력 또는 통증", ["평소와 비슷함", "조금 처짐", "많이 처짐/통증 의심", "알 수 없음"])
        st.caption(f"{neutered} · {duration} · {severity}")

    profile = {
        "breed": breed,
        "lifecycle": lifecycle or "미선택",
        "symptoms": symptoms,
        "duration": duration,
        "severity": severity,
    }
    consultation, hospitals = st.tabs(["AI 상담", "병원 찾기"])
    with consultation:
        render_consultation_tab(profile)
    with hospitals:
        render_hospital_tab()


if __name__ == "__main__":
    main()