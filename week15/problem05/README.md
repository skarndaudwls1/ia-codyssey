# 문제5 화성의 날씨 데이터를 데이터베이스에 담아라

화성 날씨 데이터(`mars_weathers_data.CSV`)를 MySQL 의 `mars_weather`
테이블에 적재하는 과제다.

## 파일 구성

| 파일 | 설명 |
|------|------|
| `mars_weather_summary.py` | 핵심 과제. CSV 읽기 + MySQL 적재 + 번호 메뉴 CLI |
| `schema.sql` | `mars_weather` 테이블 생성 스크립트 (Workbench / `mysql` CLI 용) |
| `mars_weathers_data.CSV` | 제공된 원본 데이터 (1000행) |

## 테이블 구조 (`mars_weather`)

| 컬럼 | 타입 | 비고 |
|------|------|------|
| `weather_id` | `INT` | Primary Key, 자동 증가(AUTO_INCREMENT) |
| `mars_date` | `DATETIME` | 필수 입력(NOT NULL) |
| `temp` | `INT` | 화성 기온 (명세에 맞춰 정수) |
| `storm` | `INT` | 모래 폭풍 세기 |

> 과제 명세의 표에 `temp` 가 `int` 로 적혀 있어 정수 컬럼으로 둔다.
> 제공된 CSV 의 기온 값은 소수(예: `21.4`, `24.67`)이므로, 적재 시
> `round()` 로 반올림해서 넣는다(예: `21.4 → 21`, `24.67 → 25`).

## 사전 준비

1. MySQL 서버를 설치하고 실행한다.
2. MySQL Workbench 로 접속한 뒤 `schema.sql` 을 실행해 데이터베이스와
   테이블을 만든다. (또는 `mysql -u root -p < schema.sql`)
3. MySQL 연결용 파이썬 드라이버를 설치한다. 아래 둘 중 **설치된 것을
   자동으로 감지**해서 사용한다.
   - `pip install pymysql`
   - `pip install mysql-connector-python`

> MySQL 연결 부분에 한해 외부 라이브러리 사용이 허용된다. 그 외 CSV
> 파싱 등은 파이썬 기본 기능만 사용한다.

## 접속 정보 설정 (`.env`)

접속 정보는 코드에 박지 않고, 같은 폴더의 `.env` 파일(또는 셸 환경
변수)에서 읽는다. `.env` 는 민감 정보이므로 깃에 올리지 않는다
(`.gitignore` 에 등록됨). 실행 전에 같은 폴더에 `.env` 를 만들고 아래
키를 채운다.

```
# week15/problem05/.env
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=mars
MYSQL_PASSWORD=mars1234
MYSQL_DATABASE=mars_db
```

| 키 | 설명 |
|-----|------|
| `MYSQL_HOST` | DB 서버 주소 |
| `MYSQL_PORT` | DB 포트 |
| `MYSQL_USER` | 접속 계정 |
| `MYSQL_PASSWORD` | 접속 비밀번호 |
| `MYSQL_DATABASE` | 사용할 데이터베이스 이름 |

> 우선순위는 **셸 환경 변수 > `.env` 파일** 이다. `.env` 읽기는 외부
> 라이브러리 없이 내장 기능만으로 직접 파싱한다(`load_env`). `.env` 가
> 없거나 값이 비면 DB 작업(2·3·4번 메뉴)은 실행되지 않고 어떤 키가
> 비었는지 안내한다. (CSV 만 보는 1번 메뉴는 `.env` 없이도 동작한다.)

## 실행

본 파일이 있는 폴더에서 실행한다.

```
python3 mars_weather_summary.py
```

번호 메뉴 CLI 로 동작한다.

```
1. CSV 내용 확인          # 파일을 읽어 헤더와 앞쪽 데이터를 보여준다
2. mars_weather 테이블 생성
3. CSV 데이터를 테이블에 입력   # 각 행을 INSERT 쿼리로 반복 실행
4. 테이블 내용 조회        # 적재된 전체 행을 보여준다
0. 종료
```

종료는 `0` 외에 `Ctrl+C` / `Ctrl+D` 로도 가능하며, 이때 오류 추적 없이
깔끔하게 끝난다.

## CSV 파일 선택

특정 파일명을 코드에 박지 않고, 실행 시점에 **같은 폴더의 `.csv`
파일(대소문자 무관)** 을 훑어서 사용한다.

- `.csv` 가 한 개면 그 파일을 자동으로 사용한다.
- 여러 개면 번호 메뉴로 사용할 파일을 직접 고른다(`0` 은 취소).
- 한 개도 없으면 안내만 하고 메뉴로 돌아간다.

## 데이터 검증 (전체 반영 방식)

CSV 의 각 행이 테이블 속성과 맞는지 먼저 확인한다.

- `mars_date` 는 `YYYY-MM-DD` 형식이어야 한다(DATETIME).
- `temp`, `storm` 은 정수로 바꿀 수 있어야 한다(INT). `temp` 의 소수
  값은 `round()` 로 반올림한다.

한 행이라도 맞지 않으면 **일부만 넣지 않고 그 파일 전체를 반영하지
않는다.** 어떤 줄이 왜 문제인지 안내한 뒤 메뉴로 돌아간다(부분 적재로
데이터가 어긋나는 것을 막기 위함).

## 동작 메모

- CSV 헤더의 마지막 컬럼명 `stom` 은 `storm` 의 오타로 보고 `storm`
  컬럼에 적재한다.
- `weather_id` 는 자동 증가 값이므로 INSERT 시에는 넣지 않고
  `mars_date`, `temp`, `storm` 세 컬럼만 입력한다.
- 재실행 시 데이터 중복을 막기 위해 입력 전에 테이블을 `TRUNCATE` 한다.

## 보너스

데이터베이스 연결과 쿼리 실행을 쉽게 다루기 위한 `MySQLHelper` 클래스를
제공한다. `with` 문과 함께 쓰면 블록을 빠져나갈 때 연결이 자동으로 닫힌다.

```python
with MySQLHelper(**DB_CONFIG) as db:
    db.execute('INSERT INTO mars_weather (mars_date, temp, storm) '
               'VALUES (%s, %s, %s)', ('2050-01-01', 21.4, 56))
    rows = db.fetch_all('SELECT * FROM mars_weather LIMIT 5')
```
