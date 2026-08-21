# 기타 미포함 세로 막대그래프
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from pathlib import Path

df = pd.read_csv('./data/training/df.csv')

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

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
plt.show()

from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

# Q&A 데이터 파일 경로
qa_file_path = Path(
    r"C:\Users\Playdata\Desktop\MLE-01-p1-team2-mytest\data\training\df.csv"
)

# 동물병원 데이터와 구분하기 위해 qa_df 사용
qa_df = pd.read_csv(
    qa_file_path,
    low_memory=False
)

# 컬럼 확인
print(qa_df.columns.tolist())

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

print(department_counts)

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
plt.show()