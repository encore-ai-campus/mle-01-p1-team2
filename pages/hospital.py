import os
from pathlib import Path
import sqlite3
import streamlit as st
import pandas as pd

con = sqlite3.connect('./data/hospital.db')
cursor = con.cursor()

st.title("지역별 동물 병원 찾기")


big_list=['서울', '부산', '대전', '대구', '광주']
seoul_list=["종로구", "중구", "용산구", "성동구", "광진구", "동대문구",
    "중랑구", "성북구", "강북구", "도봉구", "노원구", "은평구", "서대문구", "마포구",
    "양천구", "강서구", "구로구", "금천구", "영등포구", "동작구", "관악구",
    "서초구", "강남구", "송파구", "강동구",
]

with st.form(key='form'):
    st.subheader('검색할 구/군을 고르세요')
    small = st.selectbox('구를 고르세요', seoul_list)
    st.success(f" {small}을 조회했습니다!")
    st.form_submit_button("제출")

if st.button("병원 조회"):
    cursor.execute("SELECT * FROM hospital WHERE old_address LIKE ?", (f"%{small}%",))
    st.success(f" {small}을 조회했습니다!")
    rows = cursor.fetchall()
    df = pd.DataFrame(rows, columns=["ids", "name", "new_address", "x_coor", "y_coor", "old_address"])
    st.dataframe(df)


    