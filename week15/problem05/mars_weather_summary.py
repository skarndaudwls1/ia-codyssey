'''
mars_weather_summary.py
화성 날씨 데이터(mars_weathers_data.csv)를 MySQL 의 mars_weather 테이블에
적재하는 도구.

동작 개요
- 한국어 번호 메뉴 CLI 로 동작한다.
- CSV 파일을 직접 한 줄씩 읽어 내용을 확인한다. (표준 라이브러리 csv 모듈을
  쓰지 않고 직접 파싱한다.)
- MySQL 연결 부분에 한해 외부 라이브러리 사용이 허용된다. pymysql 또는
  mysql-connector-python 중 설치된 것을 자동으로 감지해서 사용한다.
- CSV 의 각 행을 INSERT 쿼리로 변환해서 반복적으로 실행한다.

보너스
- 데이터베이스 연결과 쿼리 실행을 쉽게 다루기 위한 MySQLHelper 클래스를 둔다.

CSV 컬럼 안내
- 제공 파일의 헤더는 weather_id,mars_date,temp,stom 이다. 마지막 컬럼명
  'stom' 은 storm(모래 폭풍)의 오타로 보고 storm 컬럼에 적재한다.
- weather_id 는 테이블에서 자동 증가 값이므로 INSERT 시에는 넣지 않고
  mars_date, temp, storm 세 컬럼만 입력한다.

실행은 본 파일이 있는 폴더에서 한다.
접속 정보는 아래 상수에서 직접 고치거나 환경 변수로 덮어쓸 수 있다.
'''

import os

# ---------------------------------------------------------------------------
# MySQL 드라이버 자동 감지 (이 부분에 한해 외부 라이브러리 허용)
# ---------------------------------------------------------------------------
# 두 드라이버 모두 DB-API 2.0 을 따르므로 connect / cursor / execute /
# executemany / commit / fetchall 의 사용법이 동일하다. 자리표시자도 둘 다
# '%s' 를 쓴다. 설치된 쪽을 골라서 사용하고, 둘 다 없으면 None 으로 둔다.
try:
    import pymysql as _driver
    _DRIVER_NAME = 'pymysql'
except ImportError:
    try:
        import mysql.connector as _driver
        _DRIVER_NAME = 'mysql-connector-python'
    except ImportError:
        _driver = None
        _DRIVER_NAME = None


# ---------------------------------------------------------------------------
# 상수
# ---------------------------------------------------------------------------
APP_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILENAME = 'mars_weathers_data.CSV'
CSV_PATH = os.path.join(APP_DIR, CSV_FILENAME)

TABLE_NAME = 'mars_weather'

# 접속 정보. 필요하면 값을 직접 고치거나 환경 변수로 덮어쓴다.
DB_CONFIG = {
    'host': os.environ.get('MYSQL_HOST', '127.0.0.1'),
    'port': int(os.environ.get('MYSQL_PORT', '3306')),
    'user': os.environ.get('MYSQL_USER', 'mars'),
    'password': os.environ.get('MYSQL_PASSWORD', 'mars1234'),
    'database': os.environ.get('MYSQL_DATABASE', 'mars_db'),
}


# ---------------------------------------------------------------------------
# 보너스: MySQLHelper 클래스
# ---------------------------------------------------------------------------
class MySQLHelper:
    '''MySQL 연결과 쿼리 실행을 간단히 다루기 위한 도우미.

    with 문과 함께 쓰면 블록을 빠져나갈 때 연결이 자동으로 닫힌다.

        with MySQLHelper(**DB_CONFIG) as db:
            db.execute('...')
    '''

    def __init__(self, host, port, user, password, database):
        if _driver is None:
            raise RuntimeError(
                'MySQL 드라이버가 없습니다. '
                'pymysql 또는 mysql-connector-python 을 설치하세요.'
            )
        self._host = host
        self._port = port
        self._user = user
        self._password = password
        self._database = database
        self._connection = None

    def connect(self):
        '''데이터베이스에 연결한다. 이미 연결돼 있으면 그대로 둔다.'''
        if self._connection is not None:
            return self._connection
        self._connection = _driver.connect(
            host=self._host,
            port=self._port,
            user=self._user,
            password=self._password,
            database=self._database,
        )
        return self._connection

    def execute(self, query, params=None):
        '''INSERT / UPDATE / DELETE / DDL 류 쿼리를 실행하고 커밋한다.

        반영된 행 수를 돌려준다.
        '''
        connection = self.connect()
        cursor = connection.cursor()
        try:
            cursor.execute(query, params or ())
            connection.commit()
            return cursor.rowcount
        finally:
            cursor.close()

    def execute_many(self, query, params_list):
        '''같은 쿼리를 여러 행에 한꺼번에 실행하고 마지막에 한 번만
        커밋한다. 드라이버가 제공하는 executemany 를 쓰므로 한 줄씩
        보내는 것보다 빠르다.

        반영된 행 수를 돌려준다.
        '''
        connection = self.connect()
        cursor = connection.cursor()
        try:
            cursor.executemany(query, list(params_list))
            connection.commit()
            return cursor.rowcount
        finally:
            cursor.close()

    def fetch_all(self, query, params=None):
        '''SELECT 쿼리를 실행하고 모든 행을 리스트로 돌려준다.'''
        connection = self.connect()
        cursor = connection.cursor()
        try:
            cursor.execute(query, params or ())
            return cursor.fetchall()
        finally:
            cursor.close()

    def close(self):
        '''연결을 닫는다.'''
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
        return False


# ---------------------------------------------------------------------------
# CSV 읽기 (csv 모듈을 쓰지 않고 직접 파싱한다)
# ---------------------------------------------------------------------------
def read_csv_file(path):
    '''CSV 파일을 읽어 (헤더, 행목록) 을 돌려준다.

    각 행은 mars_date, temp, storm 값을 담은 튜플이다. 첫 컬럼인
    weather_id 는 테이블에서 자동 증가하므로 읽기만 하고 버린다.
    '''
    with open(path, 'r', encoding='utf-8') as csv_file:
        lines = [line.strip() for line in csv_file if line.strip()]

    if not lines:
        return [], []

    header = lines[0].split(',')
    rows = []
    for line in lines[1:]:
        fields = line.split(',')
        # 컬럼은 weather_id, mars_date, temp, stom 순서다. 숫자 인덱스 대신
        # 이름으로 풀어 두면 어떤 값을 쓰는지 한눈에 보인다. weather_id 는
        # 테이블에서 자동 증가하므로 읽기만 하고 버린다(_ 로 표시).
        if len(fields) != 4:
            print('형식이 맞지 않아 건너뜁니다:', line)
            continue
        _weather_id, mars_date, temp, storm = fields
        rows.append((mars_date, float(temp), int(storm)))
    return header, rows


def print_csv_content(header, rows, preview=5):
    '''읽어 들인 CSV 내용을 사람이 확인할 수 있게 출력한다.'''
    print('CSV 헤더:', ','.join(header))
    print('총 데이터 행 수:', len(rows))
    print('앞쪽 {0}개 미리보기:'.format(preview))
    for mars_date, temp, storm in rows[:preview]:
        print('  날짜={0}, 기온={1}, 폭풍={2}'.format(mars_date, temp, storm))


# ---------------------------------------------------------------------------
# 테이블 작업
# ---------------------------------------------------------------------------
def create_table(db):
    '''mars_weather 테이블을 생성한다(없을 때만).'''
    query = (
        'CREATE TABLE IF NOT EXISTS ' + TABLE_NAME + ' ('
        '    weather_id INT NOT NULL AUTO_INCREMENT,'
        '    mars_date  DATETIME NOT NULL,'
        '    temp       FLOAT,'
        '    storm      INT,'
        '    PRIMARY KEY (weather_id)'
        ')'
    )
    db.execute(query)
    print('테이블 "{0}" 준비 완료.'.format(TABLE_NAME))


def insert_weathers(db, rows):
    '''CSV 행들을 INSERT 쿼리로 변환해서 반복적으로 실행한다.

    재실행 시 데이터가 중복되지 않도록 먼저 테이블을 비운다.
    '''
    db.execute('TRUNCATE TABLE ' + TABLE_NAME)
    query = (
        'INSERT INTO ' + TABLE_NAME +
        ' (mars_date, temp, storm) VALUES (%s, %s, %s)'
    )
    inserted = db.execute_many(query, rows)
    print('{0}개 행을 "{1}" 테이블에 입력했습니다.'.format(inserted, TABLE_NAME))


def show_table(db, preview=5):
    '''테이블에 적재된 내용을 일부 조회해서 확인한다.'''
    total = db.fetch_all('SELECT COUNT(*) FROM ' + TABLE_NAME)
    print('테이블 행 수:', total[0][0] if total else 0)
    rows = db.fetch_all(
        'SELECT weather_id, mars_date, temp, storm FROM ' + TABLE_NAME +
        ' ORDER BY weather_id LIMIT %s',
        (preview,),
    )
    print('앞쪽 {0}개:'.format(preview))
    for weather_id, mars_date, temp, storm in rows:
        print('  id={0}, 날짜={1}, 기온={2}, 폭풍={3}'.format(
            weather_id, mars_date, temp, storm))


# ---------------------------------------------------------------------------
# 메뉴 CLI
# ---------------------------------------------------------------------------
def print_menu():
    print()
    print('===== 화성 날씨 데이터 적재 =====')
    print('드라이버:', _DRIVER_NAME or '없음(설치 필요)')
    print('1. CSV 내용 확인')
    print('2. mars_weather 테이블 생성')
    print('3. CSV 데이터를 테이블에 입력')
    print('4. 테이블 내용 조회')
    print('0. 종료')


def run_with_db(action):
    '''DB 가 필요한 동작을 안전하게 실행한다.

    드라이버가 없거나 접속에 실패하면 메시지만 보여주고 넘어간다.
    '''
    if _driver is None:
        print('MySQL 드라이버가 없습니다. '
              'pymysql 또는 mysql-connector-python 을 설치하세요.')
        return
    try:
        with MySQLHelper(**DB_CONFIG) as db:
            action(db)
    except Exception as error:
        # 접속 실패, 권한 문제 등은 프로그램을 끝내지 않고 메시지로 안내한다.
        print('데이터베이스 작업 실패:', error)


def read_csv_or_warn():
    '''CSV 파일을 읽어 (헤더, 행목록) 을 돌려준다.

    파일이 없으면 안내 메시지를 출력하고 (None, None) 을 돌려준다.
    파일 존재 확인 코드가 메뉴 곳곳에 중복되지 않도록 한 곳에 모았다.
    '''
    if not os.path.exists(CSV_PATH):
        print('CSV 파일을 찾을 수 없습니다:', CSV_PATH)
        return None, None
    return read_csv_file(CSV_PATH)


def main():
    while True:
        print_menu()
        choice = input('선택> ').strip()

        if choice == '1':
            header, rows = read_csv_or_warn()
            if header is not None:
                print_csv_content(header, rows)
        elif choice == '2':
            run_with_db(create_table)
        elif choice == '3':
            _, rows = read_csv_or_warn()
            if rows:
                run_with_db(lambda db: insert_weathers(db, rows))
        elif choice == '4':
            run_with_db(show_table)
        elif choice == '0':
            print('종료합니다.')
            break
        else:
            print('잘못된 선택입니다. 0 ~ 4 중에서 고르세요.')


if __name__ == '__main__':
    main()
