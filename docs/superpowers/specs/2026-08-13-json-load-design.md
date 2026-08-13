# JSON 학습 데이터 로딩 설계

## 목적

`data/training` 아래의 모든 JSON 파일을 하나의 pandas DataFrame으로 결합한다. JSON 내부의 중첩 객체 키는 개별 컬럼으로 펼쳐, `meta.lifeCycle`과 `qa.input`처럼 원래 경로를 식별할 수 있는 컬럼명을 사용한다.

## 입력과 데이터 흐름

1. 노트북 위치를 기준으로 `data/training` 경로를 설정한다.
2. `Path.rglob("*.json")`으로 하위 폴더를 포함한 JSON 파일을 찾는다.
3. 각 파일을 UTF-8 JSON으로 읽는다.
4. JSON 최상위 값이 리스트이면 리스트의 각 항목을 행 후보로 추가하고, 객체이면 객체 하나를 행 후보로 추가한다.
5. `pandas.json_normalize(records, sep=".")`로 중첩 키를 평탄화한다.
6. 결과를 `df`에 저장하고 파일 수, 행 수, 컬럼 목록, 샘플을 출력한다.

## 결과 컬럼

현재 데이터 구조에서는 다음 컬럼이 생성된다.

- `meta.lifeCycle`
- `meta.department`
- `meta.disease`
- `qa.instruction`
- `qa.input`
- `qa.output`

JSON 파일마다 일부 키가 없더라도 전체 키의 합집합을 기준으로 컬럼을 만들며, 누락된 값은 pandas의 결측값으로 둔다. 향후 JSON에 키가 추가되면 별도 코드 수정 없이 새 컬럼이 생성된다.

## 오류 처리와 범위

- JSON 파일은 UTF-8로 읽는다.
- 개별 JSON 파싱 오류는 전체 로딩을 조용히 중단하지 않고 파일 경로와 오류를 기록한 뒤 다음 파일을 계속 처리한다.
- 현재 요청 범위에는 CSV 저장, 데이터 정제, 텍스트 인코딩 복구, 스키마 검증을 포함하지 않는다.

## 검증 기준

- 노트북의 모든 코드 셀이 오류 없이 실행된다.
- `df`가 생성되고 행 수가 0보다 크다.
- `df.columns`에 중첩 키가 평탄화된 컬럼이 포함된다.
- 탐색한 JSON 파일 수와 생성된 DataFrame 행 수가 출력된다.
