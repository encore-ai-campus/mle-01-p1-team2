import os
os.environ.setdefault("ARROW_DEFAULT_MEMORY_POOL", "system")
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import seaborn as sns
import streamlit as st

from src.fonts import apply_korean_font
from src.data_utils import first_address_word_counts
apply_korean_font()

st.title("📊 반려동물 데이터 대시보드")

@st.cache_data
def load_pet():
    """개 건강 데이터를 읽어 돌려준다(한 번만 읽고 캐싱)."""
    return pd.read_csv(r'data\training\df.csv')

@st.cache_data
def load_hospital():
    """동물병원 데이터를 읽어 돌려준다(한 번만 읽고 캐싱)."""
    return pd.read_csv(r'data\hospital_completed.csv')

df = load_pet()
df2 = load_hospital()

tab1, tab2, tab3 = st.tabs(["진료과 별 분포", "기타를 제외한 질병 순위", "지역별 동물병원 수"])

with tab1:
    department_counts = (
        df["meta.department"]
        .astype("string")
        .str.strip()
        .fillna("결측")
        .value_counts()
        .rename_axis("department")
        .reset_index(name="count")
    )

    fig1 = px.pie(
        data_frame=department_counts,
        names="department",
        values="count",
        title="진료과별 분포"
    )

    st.plotly_chart(fig1)

with tab2:
    st.subheader('기타 14,774건을 제외한 4,432건 ')
    disease_counts = (
        df.loc[df["meta.disease"] != "기타", "meta.disease"]
        .dropna()
        .value_counts()
        .head(10)
    )

    fig2, ax = plt.subplots()
    sns.barplot(
        x=disease_counts.index,
        y=disease_counts.values,
        ax=ax
    )

    ax.set_xlabel("질병")
    ax.set_ylabel("건수")
    ax.tick_params(axis="x", rotation=45)

    st.pyplot(fig2)

with tab3:
    hospital_counts = first_address_word_counts(df2["도로명주소"])

    fig3, ax = plt.subplots(figsize=(10, 6))
    ax.bar(
        hospital_counts.index,
        hospital_counts.values,
        color="skyblue"
    )

    ax.set_xlabel("주소 첫 단어")
    ax.set_ylabel("동물병원 수")
    ax.set_title("주소 첫 단어별 동물병원 수")
    ax.tick_params(axis="x", rotation=45)

    fig3.tight_layout()
    st.pyplot(fig3)
