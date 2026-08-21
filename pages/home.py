import os
os.environ.setdefault("ARROW_DEFAULT_MEMORY_POOL", "system")
from PIL import Image
import streamlit as st

image = Image.open('pages\화면 캡처 2026-08-20 110623.png')

st.title("🐶 동물 구조대")

if "messages" not in st.session_state:
    st.session_state.messages = []

st.markdown(
    """
## 동물 구조대

동물 구조대는 반려견 보호자가 건강 정보를 찾고 가까운 동물 병원을 확인할 수 있도록 돕는 데이터 기반 반려동물 케어 서비스입니다.

591만 반려동물 가구 시대에 보호자가 반려견의 증상에 관한 정보를 더 빠르게 확인하고, 필요한 진료를 받을 수 있도록 돕는 것을 목표로 합니다.

자료 출처: KB경영연구소
"""
)
st.image(image, caption= '반려동물 비율')

st.markdown(
    """
## 페이지 소개

### 데이터 소개
진료과, 기타를 제외한 질병 순위, 지역별 동물병원 수 시각화

### 질병 문의
반려견의 증상이나 질병을 질문하면 나이 단계, 진료과, 질병 종류를 기준으로 관련 학습 데이터를 검색하고 근거를 바탕으로 답변합니다.

### 지역별 동물 병원 찾기
지역을 선택해 해당 지역의 동물 병원 정보를 확인하고, 병원의 위치를 지도에서 살펴볼 수 있습니다.  
    """

)

st.info("사이드바에서 원하는 화면을 선택해 보세요.")
