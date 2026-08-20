import os

os.environ.setdefault("ARROW_DEFAULT_MEMORY_POOL", "system")

import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="VetCare 데이터 대시보드",
    page_icon=":material/pets:",
    layout="wide",
)

DATA_PATH = "data/training/df.csv"


@st.cache_data
def load_data():
    data = pd.read_csv(DATA_PATH)
    data = data.rename(
        columns={
            "meta.lifeCycle": "나이 단계",
            "meta.department": "진료과",
            "meta.disease": "질병명",
            "qa.instruction": "안내문",
            "qa.input": "질문",
            "qa.output": "답변",
        }
    )
    return data


try:
    df = load_data()
except FileNotFoundError:
    st.error(f"데이터 파일을 찾을 수 없습니다: {DATA_PATH}")
    st.stop()


st.title("🐶 반려견 건강 데이터 대시보드")
st.caption("나이 단계, 견종, 진료과를 선택하면 조건에 맞는 데이터를 보여줍니다.")

# 필터를 페이지 본문에 배치해 결과와 함께 바로 확인할 수 있도록 합니다.
filter_col1, filter_col2, filter_col3 = st.columns([1, 1, 1])

with filter_col1:
    st.markdown("**나이**")
    life_cycle_labels = {"자견": "자견", "성견": "성견", "노령견": "노견"}
    selected_life_cycles = [
        life_cycle
        for life_cycle, label in life_cycle_labels.items()
        if st.checkbox(label, value=True, key=f"age_{life_cycle}")
    ]

with filter_col2:
    breed_keyword = st.text_input(
        "견종",
        placeholder="예: 진돗개, 푸들",
        help="원본 데이터에 견종 컬럼이 없어 질문·안내문·답변 내용에서 검색합니다.",
    ).strip()

with filter_col3:
    departments = ["내과", "안과", "외과", "치과", "피부과"]
    departments = [department for department in departments if department in df["진료과"].unique()]
    selected_departments = st.multiselect(
        "진료과",
        options=departments,
        default=departments,
        placeholder="진료과를 선택하세요",
    )

filtered_df = df[
    df["나이 단계"].isin(selected_life_cycles)
    & df["진료과"].isin(selected_departments)
].copy()

if breed_keyword:
    searchable_text = (
        filtered_df["안내문"].fillna("")
        + " "
        + filtered_df["질문"].fillna("")
        + " "
        + filtered_df["답변"].fillna("")
    )
    filtered_df = filtered_df[
        searchable_text.str.contains(breed_keyword, case=False, na=False, regex=False)
    ]

metric_col1, metric_col2, metric_col3 = st.columns(3)
metric_col1.metric("검색 결과", f"{len(filtered_df):,}건")
metric_col2.metric("선택한 나이 단계", f"{len(selected_life_cycles)}개")
metric_col3.metric("선택한 진료과", f"{len(selected_departments)}개")

st.divider()

if filtered_df.empty:
    st.info("선택한 조건에 맞는 데이터가 없습니다.")
else:
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.subheader("나이 단계별 질문 수")
        life_cycle_counts = (
            filtered_df["나이 단계"]
            .value_counts()
            .rename_axis("나이 단계")
            .reset_index(name="질문 수")
        )
        st.bar_chart(life_cycle_counts.set_index("나이 단계"))

    with chart_col2:
        st.subheader("진료과별 질문 수")
        department_counts = (
            filtered_df["진료과"]
            .value_counts()
            .rename_axis("진료과")
            .reset_index(name="질문 수")
        )
        st.bar_chart(department_counts.set_index("진료과"))

    st.subheader("질문 목록")
    display_df = filtered_df[["나이 단계", "진료과", "질병명", "질문"]].reset_index(drop=True)
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    st.subheader("답변 상세")
    for row_number, row in filtered_df.reset_index(drop=True).iterrows():
        question_preview = row["질문"].replace("\n", " ")[:80]
        with st.expander(f"{row_number + 1}. {question_preview}..."):
            st.markdown(f"**분류:** {row['나이 단계']} / {row['진료과']} / {row['질병명']}")
            st.markdown("**질문**")
            st.write(row["질문"])
            st.markdown("**답변**")
            st.write(row["답변"])
