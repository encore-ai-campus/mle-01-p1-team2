from pathlib import Path

import pandas as pd
import streamlit as st

from src.data_charts import (
    build_department_figure,
    build_disease_figure,
    build_province_figure,
    normalize_province,
)
from src.ui import apply_app_theme, render_page_header


apply_app_theme()

BASE_DIR = Path(__file__).resolve().parents[1]
PLOTLY_CONFIG = {
    "displaylogo": False,
    "responsive": True,
    "toImageButtonOptions": {"format": "png", "filename": "petcare-chart"},
}

render_page_header(
    "데이터 소개",
    eyebrow="신뢰할 수 있는 데이터",
    description="반려동물 건강과 동물병원 데이터를 한눈에 확인하고, 필요한 인사이트를 찾아보세요.",
    accent="데이터로 살펴보는 반려동물 생활",
)

df_path = BASE_DIR / "data" / "df.csv"

if not df_path.exists() or df_path.stat().st_size <= 2:
    st.warning(f"그래프 데이터 파일이 비어 있습니다: {df_path}")
    st.stop()

try:
    df = pd.read_csv(df_path)
except pd.errors.EmptyDataError:
    st.warning(f"그래프 데이터 파일을 읽을 수 없습니다: {df_path}")
    st.stop()
required_columns = {"meta.disease", "meta.department"}
missing_columns = required_columns.difference(df.columns)
if missing_columns:
    st.warning(f"데이터에 필요한 컬럼이 없습니다: {', '.join(sorted(missing_columns))}")
    st.stop()

tab1, tab2, tab3 = st.tabs(
    ["기타를 제외한 질병 순위", "진료과 별 분포", "지역별 동물병원 수"]
)

with tab1:
    disease_counts = (
        df.loc[df["meta.disease"] != "기타", "meta.disease"]
        .value_counts()
        .head(10)
    )
    st.plotly_chart(
        build_disease_figure(disease_counts),
        width="stretch",
        config=PLOTLY_CONFIG,
    )

with tab2:
    department_counts = (
        df["meta.department"]
        .astype("string")
        .str.strip()
        .fillna("결측")
        .value_counts()
    )
    st.plotly_chart(
        build_department_figure(department_counts),
        width="stretch",
        config=PLOTLY_CONFIG,
    )

with tab3:
    hospital_df = pd.read_csv(
        BASE_DIR / "data" / "hospital_completed.csv",
        index_col=0,
        low_memory=False,
    )
    province_counts = (
        hospital_df["도로명주소"]
        .map(normalize_province)
        .value_counts()
        .sort_values(ascending=False)
    )
    st.plotly_chart(
        build_province_figure(province_counts),
        width="stretch",
        config=PLOTLY_CONFIG,
    )
