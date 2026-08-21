import os
from pathlib import Path
import sqlite3
import streamlit as st
import pandas as pd
from pyproj import Transformer

con = sqlite3.connect('./data/hospital.db')
cursor = con.cursor()

SOURCE_CRS = "EPSG:5174"
TARGET_CRS = "EPSG:4326"

transformer = Transformer.from_crs(
    SOURCE_CRS,
    TARGET_CRS,
    always_xy=True
)

st.title("지역별 동물 병원 찾기")


big_list=['서울', '부산', '대전', '대구', '광주']
seoul_list=["종로구", "중구", "용산구", "성동구", "광진구", "동대문구",
    "중랑구", "성북구", "강북구", "도봉구", "노원구", "은평구", "서대문구", "마포구",
    "양천구", "강서구", "구로구", "금천구", "영등포구", "동작구", "관악구",
    "서초구", "강남구", "송파구", "강동구"]
busan_list = ["중구", "서구", "동구", "영도구", "부산진구", "동래구", "남구", "북구", "해운대구", "사하구", "금정구",
    "강서구", "연제구", "수영구", "사상구", "기장군"]
daejeon_list = ["동구", "중구", "서구", "유성구", "대덕구"]
daegu_gun_gu = ["남구","달서구", "달성군", "동구", "북구","서구","수성구","중구","군위군",]
gwangju_list = ["동구", "서구", "남구", "북구", "광산구"]

# with st.form(key='form'):
#     st.subheader('검색할 구/군을 고르세요')
#     small = st.selectbox('구를 고르세요', seoul_list)
#     st.success(f" {small}을 조회했습니다!")
#     st.form_submit_button("제출")

# if st.button("병원 조회"):
#     cursor.execute("SELECT * FROM hospital WHERE old_address LIKE ?", (f"%{small}%",))
#     st.success(f" {small}을 조회했습니다!")
#     rows = cursor.fetchall()
#     df = pd.DataFrame(rows, columns=["ids", "name", "new_address", "x_coor", "y_coor", "old_address"])
#     st.dataframe(df)

with st.form(key='form'):
    st.subheader('검색할 시/구를 고르세요' \
    '시를 누르고 제출을 눌러야 구를 제대로 고를 수 있습니다.')
    big = st.selectbox('구를 고르세요', big_list)
    # st.success(f" {big}을 조회했습니다!")
    # st.form_submit_button("제출")
    if big == '서울' :
        small = st.selectbox('구를 고르세요', seoul_list)
    elif big == '부산':
        small = st.selectbox('구를 고르세요', busan_list)
    elif big == '대전':
        small = st.selectbox('구를 고르세요', daejeon_list)
    elif big == '대구':
        small = st.selectbox('구를 고르세요', daejeon_list)
    elif big == '광주':
        small = st.selectbox('구를 고르세요', daejeon_list)
    st.success(f"{big}, {small}을 조회했습니다!")
    st.form_submit_button("제출")

if st.button("병원 조회"):
    cursor.execute("SELECT * FROM hospital WHERE new_address LIKE ? AND new_address LIKE ?", (f"{big}%",f"%{small}%",))
    st.success(f"{big} {small}을 조회했습니다!")
    rows = cursor.fetchall()
    df = pd.DataFrame(rows, columns=["ids", "name", "new_address", "x_coor", "y_coor", "old_address"])
    st.dataframe(df)

    df["x_coor"] = pd.to_numeric(df["x_coor"], errors="coerce")
    df["y_coor"] = pd.to_numeric(df["y_coor"], errors="coerce")
    valid_df = df.dropna(subset=["x_coor", "y_coor"])
    long, lat = transformer.transform(
    valid_df["x_coor"].to_numpy(),
    valid_df["y_coor"].to_numpy())
    lat_list = lat.tolist()
    long_list = long.tolist()

    data = pd.DataFrame({
        'lat' : lat_list,
        'lon' : long_list})
    st.map(data, latitude='lat', longitude='lon')

    