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
| `temp` | `FLOAT` | 화성 기온 |
| `storm` | `INT` | 모래 폭풍 세기 |

> 과제 명세의 표에는 `temp` 가 `int` 로 적혀 있으나, 제공된 CSV 의 기온
> 값이 소수(예: `21.4`, `24.67`)이므로 값 손실을 막기 위해 `FLOAT` 로
> 정의했다.

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

## 접속 정보 설정

`mars_weather_summary.py` 상단의 `DB_CONFIG` 값을 직접 고치거나, 환경
변수로 덮어쓸 수 있다.

| 환경 변수 | 기본값 |
|-----------|--------|
| `MYSQL_HOST` | `localhost` |
| `MYSQL_PORT` | `3306` |
| `MYSQL_USER` | `root` |
| `MYSQL_PASSWORD` | (빈 문자열) |
| `MYSQL_DATABASE` | `mars_db` |

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
4. 테이블 내용 조회        # 적재 결과를 확인한다
0. 종료
```

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
