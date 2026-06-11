# 문제5 화성의 날씨 데이터를 데이터베이스에 담아라

화성 날씨 데이터(CSV)를 MySQL `mars_weather` 테이블에 적재하는 프로그램이다.
아래는 `mars_weather_summary.py` 를 실행 흐름 순서대로 요약한 내용이다.

## 1. 상수 선언
- `APP_DIR` : 이 파일이 있는 폴더 경로.
- `ENV_PATH` : DB 접속 정보를 담은 `.env` 파일 경로.
- `TABLE_NAME` : 과제에 명시된 `mars_weather`.

컬럼 목록은 코드에 박지 않고, 적재·조회 시 `SHOW COLUMNS` 로 실제 구조를
읽어서 쓴다.

## 2. 환경 설정 (`.env` → `DB_CONFIG`)
`load_env()` 로 `.env` 를 읽어 중요 값만 `DB_CONFIG` 에 넣는다. 비밀번호
같은 민감 정보를 코드에 박지 않으려고 `.env` 로 분리했다.

## 3. 시작과 메뉴
`if __name__ == '__main__':` 에서 `main()` 만 실행한다. `Ctrl+C` / `Ctrl+D`
는 오류 없이 종료되도록 예외 처리했다. `print_menu()` 가 메뉴를 보여주고,
`1 · 2 · 3 · 4 · 0` 으로 과제를 나눴다.

## 4. 1번 — CSV 내용 확인
`read_csv_or_warn()` → `find_csv_files()`(폴더의 `.csv` 검색) →
`choose_csv_file()`(번호로 선택) → `read_csv_file()`(헤더와 row 로 나눠
저장). `print_csv_content()` 로 전체 내용을 출력하며, 파일이 없으면 `None`.

> 행이 많을 때 `print` 를 반복 호출하면 느리므로, 파이썬 `join` 으로 한
> 번에 출력한다(SQL 의 JOIN 과 무관).

## 5. 2번 — 테이블 생성과 DB 연결
`run_with_db()` 로 DB 에 연결한다(보너스인 `MySQLHelper` 클래스로 연결을
간단히 처리). `action` 에는 `create_table` · `insert_weathers` 등이 들어
간다. 드라이버 없음 / 외부 라이브러리 없음 / 접속 정보 비어 있음 / 작업
실패 등의 예외를 처리했다. `create_table()` 이 테이블을 만든다.

## 6. 3번 — CSV 데이터를 테이블에 입력
`insert_weathers()` 가 CSV 를 INSERT 로 변환해 넣되, 테이블 구조에 맞아야
들어간다.

- `get_table_columns()` 로 실제 컬럼/타입을 읽는다(자동증가 컬럼은 제외).
- CSV 를 **위치 + 타입**으로 대조한다. 이름이 아니라 위치로 맞추므로
  헤더의 `stom` 오타도 그대로 적재된다.
- `convert_value()` 로 값이 컬럼 타입에 맞는지 변환해 본다. 날짜는
  `is_valid_mars_date()`(+`_is_leap_year()`)로 실제 존재하는 날짜인지
  확인한다(잘못된 날짜는 MySQL 이 거부하므로 미리 거른다).
- 한 행이라도 안 맞으면 **전체를 반영하지 않고** 사유를 알린다.
- 통과하면 `TRUNCATE` 로 비운 뒤 새로 넣고, 전/후 행 수를 보여준다.

## 7. 4번 — 테이블 내용 조회
`run_with_db(show_table)` 가 실행된다. `show_table()` 이 실제 구조를 읽어
조회하고, `format_table()` 이 실제 DB 테이블처럼 칸을 맞춰 출력한다.

```
+------------+---------------------+------+-------+
| weather_id | mars_date           | temp | storm |
+------------+---------------------+------+-------+
| 1          | 2050-01-01 00:00:00 | 21   | 56    |
+------------+---------------------+------+-------+
```
