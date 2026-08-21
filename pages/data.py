import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]

st.title('데이터 소개')

df = pd.read_csv(BASE_DIR / 'data' / 'training' / 'df.csv')

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

tab1, tab2, tab3 = st.tabs(["진료과 별 분포", "기타를 제외한 질병 순위", "지역별 동물병원 수"])

with tab1:
# '기타'를 제외한 뒤 질병별 개수 계산
    disease_counts = (
        df.loc[df['meta.disease'] != '기타', 'meta.disease']
        .value_counts()
        .head(10)
    )

# 세로 막대그래프
    plt.figure(figsize=(12, 6))

    disease_counts.plot(
        kind='bar',
        color='skyblue'
    )

    plt.title('기타를 제외한 질병 분류 TOP 10')
    plt.xlabel('질병 분류')
    plt.ylabel('데이터 개수')

    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    st.pyplot(plt.gcf())
    plt.close()

with tab2:
# Q&A 데이터 파일 경로
    qa_file_path = Path(__file__).resolve().parents[1] / 'data' / 'training' / 'df.csv'

# 동물병원 데이터와 구분하기 위해 qa_df 사용
    qa_df = pd.read_csv(
        qa_file_path,
        low_memory=False
    )

# 컬럼 확인
# 한글 폰트 설정
    plt.rcParams['font.family'] = 'Malgun Gothic'
    plt.rcParams['axes.unicode_minus'] = False

# 진료과별 개수 계산
    department_counts = (
        qa_df['meta.department']
        .astype('string')
        .str.strip()
        .fillna('결측')
        .value_counts()
    )

# 진료과별 색상
    colors = plt.get_cmap('Set3').colors[:len(department_counts)]

# 진료과 이름과 데이터 개수를 함께 표시
    labels = [
        f'{department}\n({count:,}건)'
        for department, count in department_counts.items()
    ]

# 파이그래프
    plt.figure(figsize=(9, 9))

    plt.pie(
        department_counts.values,
        labels=labels,
        autopct='%1.1f%%',
        startangle=90,
        counterclock=False,
        colors=colors,
        wedgeprops={
        'edgecolor': 'white',
        'linewidth': 1
        },
        textprops={
            'fontsize': 11
        }
    )

    plt.title('진료과별 데이터 비율')
    plt.axis('equal')
    plt.tight_layout()
    st.pyplot(plt.gcf())
    plt.close()

with tab3:

    # 도로명주소의 첫 번째 토큰을 시·도로 사용해 동물병원 수를 계산
    hospital_file_path = BASE_DIR / 'data' / 'hospital_completed.csv'
    hospital_df = pd.read_csv(hospital_file_path, index_col=0, low_memory=False)

    province_aliases = {
        '서울': '서울특별시',
        '부산': '부산광역시',
        '대구': '대구광역시',
        '인천': '인천광역시',
        '광주': '광주광역시',
        '대전': '대전광역시',
        '울산': '울산광역시',
        '세종': '세종특별자치시',
        '경기': '경기도',
        '강원': '강원특별자치도',
        '충북': '충청북도',
        '충남': '충청남도',
        '전북': '전북특별자치도',
        '전남': '전라남도',
        '경북': '경상북도',
        '경남': '경상남도',
        '제주': '제주특별자치도',
    }
    province_names = tuple(province_aliases.values())


    def normalize_province(address):
        if pd.isna(address):
            return '주소 없음'

        compact_address = ''.join(str(address).split())
        for province in province_names:
            if compact_address.startswith(''.join(province.split())):
                return province

        for alias, province in province_aliases.items():
            if compact_address.startswith(alias):
                return province

        return str(address).strip().split()[0]


    province_counts = (
        hospital_df['도로명주소']
        .map(normalize_province)
        .value_counts()
        .sort_values(ascending=False)
    )

    plt.figure(figsize=(12, 6))
    province_counts.plot(kind='bar', color='seagreen')
    plt.title('도로명주소 기준 시·도별 동물병원 수')
    plt.xlabel('시·도')
    plt.ylabel('동물병원 수')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    st.pyplot(plt.gcf())
    plt.close() 