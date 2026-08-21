import pandas as pd
import requests
import re
import time
import tomllib
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
INPUT_FILE = PROJECT_ROOT / "data" / "hospital_missing_address_or_coordinates.csv"
OUTPUT_FILE = PROJECT_ROOT / "data" / "hospital_filled.csv"
SECRETS_FILE = PROJECT_ROOT / ".streamlit" / "secrets.toml"
SOURCE_FILE = OUTPUT_FILE if OUTPUT_FILE.exists() else INPUT_FILE

with SECRETS_FILE.open("rb") as file:
    REST_API_KEY = tomllib.load(file)["Default Rest API Key"]

df = pd.read_csv(SOURCE_FILE, keep_default_na=False)

headers = {
    "Authorization": f"KakaoAK {REST_API_KEY}"
}


def clean_address(address):
    if pd.isna(address):
        return None

    address = str(address).strip()

    # 괄호 안 내용 제거
    address = re.sub(r"\([^)]*\)", "", address)

    # 쉼표 뒤 상세주소 제거
    address = address.split(",")[0]

    # 층 정보 제거
    address = re.sub(r"\s+\d+(?:~\d+)?층.*$", "", address)

    # 호수 정보 제거
    address = re.sub(r"\s+\d+(?:-\d+)?호.*$", "", address)

    # 불필요한 공백 정리
    address = re.sub(r"\s+", " ", address)

    return address.strip()


def search_address(address):
    url = "https://dapi.kakao.com/v2/local/search/address.json"

    response = requests.get(
        url,
        headers=headers,
        params={"query": address},
        timeout=10
    )

    if response.status_code != 200:
        return None

    documents = response.json().get("documents", [])

    if not documents:
        return None

    doc = documents[0]

    road_address = None

    if doc.get("road_address"):
        road_address = doc["road_address"].get("address_name")

    return {
        "x": doc.get("x"),
        "y": doc.get("y"),
        "road_address": road_address
    }


def search_with_clean_address(*addresses):
    searched = set()

    for address in addresses:
        for query in (address, clean_address(address)):
            if not query or query in searched:
                continue

            searched.add(query)
            result = search_address(query)
            if result is not None:
                return result

    return None


def extract_sigungu(*addresses):
    for address in addresses:
        cleaned = clean_address(address)
        if not cleaned:
            continue

        tokens = cleaned.split()
        for position, token in enumerate(tokens[1:], start=1):
            if token.endswith(("시", "군", "구")):
                if token.endswith("시") and position + 1 < len(tokens):
                    next_token = tokens[position + 1]
                    if next_token.endswith("구"):
                        return f"{token} {next_token}"
                return token

    return ""


def search_keyword(query):
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"

    response = requests.get(
        url,
        headers=headers,
        params={"query": query, "size": 15},
        timeout=10
    )

    if response.status_code != 200:
        return None

    documents = response.json().get("documents", [])
    if not documents:
        return None

    for doc in documents:
        if doc.get("x") and doc.get("y"):
            return {
                "x": doc["x"],
                "y": doc["y"],
                "road_address": doc.get("road_address_name") or None
            }

    return None


def search_hospital_by_keyword(row):
    sigungu = extract_sigungu(row["도로명주소"], row["지번주소"])
    query = f"{row['사업장명']} {sigungu}".strip()
    return query, search_keyword(query)


drop_indices = []


for i, row in df.iterrows():

    x_missing = row["좌표정보(X)"] == ""
    y_missing = row["좌표정보(Y)"] == ""
    road_missing = row["도로명주소"].strip() == ""

    # 이미 모든 정보가 있으면 건너뜀
    if not x_missing and not y_missing and not road_missing:
        continue

    query, result = search_hospital_by_keyword(row)

    if result is None:
        if x_missing or y_missing:
            drop_indices.append(i)
            print(f"검색 실패 및 삭제: {row['사업장명']} / {query}")
        else:
            print(f"검색 실패: {row['사업장명']} / {query}")
        continue

    if x_missing:
        df.at[i, "좌표정보(X)"] = float(result["x"])

    if y_missing:
        df.at[i, "좌표정보(Y)"] = float(result["y"])

    if road_missing and result["road_address"]:
        df.at[i, "도로명주소"] = result["road_address"]

    print(f"{i + 1}/{len(df)} {row['사업장명']} 처리 완료")

    time.sleep(0.05)


df = df.drop(index=drop_indices)
df.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)

print("완료:", OUTPUT_FILE)