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
접속 정보는 코드에 박지 않고 같은 폴더의 .env 파일이나 환경 변수로
받는다. .env 는 깃에 올리지 않는다(.gitignore). 필요한 키 목록은
아래 예시와 같다.

    # .env 예시
    MYSQL_HOST=127.0.0.1
    MYSQL_PORT=3306
    MYSQL_USER=mars
    MYSQL_PASSWORD=mars1234
    MYSQL_DATABASE=mars_db
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
ENV_PATH = os.path.join(APP_DIR, '.env')

TABLE_NAME = 'mars_weather'

# 컬럼 목록을 코드에 고정하지 않는다. CSV 를 적재·조회할 때 SHOW COLUMNS 로
# 실제 테이블 구조(컬럼 이름/타입/자동증가 여부)를 그때그때 읽어, CSV 가 그
# 구조에 맞는지 판단한다. 이렇게 하면 테이블 구조가 바뀌어도 코드를 고치지
# 않고 따라간다.


def load_env(path):
    '''.env 파일을 한 줄씩 직접 읽어 환경 변수로 올린다.

    외부 라이브러리(python-dotenv)를 쓰지 않고 내장 기능만 사용한다.
    'KEY=VALUE' 형식만 처리하고, 빈 줄과 '#' 주석 줄은 건너뛴다.
    이미 셸에서 지정한 환경 변수는 setdefault 로 덮어쓰지 않는다.
    '''
    if not os.path.exists(path):
        return
    with open(path, 'r', encoding='utf-8') as env_file:
        for line in env_file:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, value = line.split('=', 1)
            os.environ.setdefault(key.strip(), value.strip())


# DB_CONFIG 를 만들기 전에 .env 를 먼저 읽어 둔다. 비밀번호 같은 민감 정보는
# 코드에 박지 않고 .env(깃 추적 제외) 또는 셸 환경 변수로만 받는다.
load_env(ENV_PATH)

# 접속 정보는 코드에 값을 남기지 않고 .env(또는 환경 변수)에서만 받는다.
# .env 가 없으면 값이 비어 DB 작업이 실행되지 않으므로, 실행 전에 같은
# 폴더에 .env 를 만들어 채워야 한다(키 목록은 파일 상단 주석 참고).
DB_CONFIG = {
    'host': os.environ.get('MYSQL_HOST', ''),
    'port': int(os.environ.get('MYSQL_PORT', '0')),
    'user': os.environ.get('MYSQL_USER', ''),
    'password': os.environ.get('MYSQL_PASSWORD', ''),
    'database': os.environ.get('MYSQL_DATABASE', ''),
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
            # params_list 는 이미 리스트로 들어오므로 따로 복사하지 않는다.
            cursor.executemany(query, params_list)
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

    헤더와 각 행은 콤마로 나눈 '문자열 필드들의 리스트' 다. 여기서는
    타입 검증이나 변환을 하지 않는다. 테이블 구조에 맞는지 판단하는 일은
    실제 DB 구조를 아는 적재 단계(insert_weathers)에서 한다.
    '''
    with open(path, 'r', encoding='utf-8') as csv_file:
        # 각 줄을 한 번만 strip 한 뒤, 빈 줄을 걸러낸다(strip 중복 호출 제거).
        lines = [stripped for stripped in (line.strip() for line in csv_file)
                 if stripped]

    if not lines:
        return [], []

    header = lines[0].split(',')
    rows = [line.split(',') for line in lines[1:]]
    return header, rows


def _is_leap_year(year):
    '''그레고리력 윤년 여부. (DATETIME 은 그레고리력 기준)'''
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def is_valid_mars_date(value):
    '''mars_date 가 'YYYY-MM-DD' 형식의 실제 존재하는 날짜인지 검사한다.

    DATETIME 컬럼에 들어갈 날짜를 표준 라이브러리 없이 직접 확인한다.
    연-월-일 세 토막이 모두 숫자여야 하고, 월(1~12)과 일이 그 달의 실제
    일수 범위 안이어야 한다(예: 2050-02-31 은 거른다).
    '''
    parts = value.split('-')
    if len(parts) != 3:
        return False
    year, month, day = parts
    if not (year.isdigit() and month.isdigit() and day.isdigit()):
        return False
    if len(year) != 4:
        return False
    year_value, month_value, day_value = int(year), int(month), int(day)
    if not 1 <= month_value <= 12:
        return False
    days_in_month = (31, 29 if _is_leap_year(year_value) else 28, 31, 30,
                     31, 30, 31, 31, 30, 31, 30, 31)
    return 1 <= day_value <= days_in_month[month_value - 1]


def get_table_columns(db):
    '''테이블의 실제 구조를 읽어 [(이름, 타입, 자동증가여부), ...] 로 돌려준다.

    SHOW COLUMNS 결과의 각 행은 (Field, Type, Null, Key, Default, Extra)
    이다. Extra 에 'auto_increment' 가 있으면 그 컬럼은 DB 가 자동으로
    채우므로 INSERT 대상에서 제외할 수 있다.
    '''
    info = db.fetch_all('SHOW COLUMNS FROM {0}'.format(TABLE_NAME))
    columns = []
    for row in info:
        field, col_type, extra = row[0], row[1], row[5]
        is_auto = 'auto_increment' in str(extra).lower()
        columns.append((field, str(col_type), is_auto))
    return columns


def convert_value(col_type, raw):
    '''DB 컬럼 타입(col_type)에 맞춰 문자열 raw 를 변환한다.

    변환할 수 있으면 (값, None) 을, 없으면 (None, 사유문자열) 을 돌려준다.
    컬럼 타입은 SHOW COLUMNS 가 주는 'int', 'datetime', 'float',
    'varchar(20)' 같은 문자열이다. 이름이 아니라 '타입'을 보고 판단하므로
    테이블 구조가 바뀌어도 그대로 적용된다.
    '''
    lowered = col_type.lower()
    if 'int' in lowered:
        # 정수 컬럼: 소수('21.4')도 받도록 float 으로 읽은 뒤 반올림한다.
        try:
            return round(float(raw)), None
        except ValueError:
            return None, '정수로 바꿀 수 없음'
    if 'float' in lowered or 'double' in lowered or 'decimal' in lowered:
        try:
            return float(raw), None
        except ValueError:
            return None, '실수로 바꿀 수 없음'
    if 'date' in lowered or 'time' in lowered:
        # datetime / date / timestamp 류는 날짜 형식인지 확인한다.
        if is_valid_mars_date(raw):
            return raw, None
        return None, '날짜(YYYY-MM-DD) 형식이 아님'
    # 문자열 계열(varchar, text 등)은 그대로 사용한다.
    return raw, None


def print_csv_content(header, rows):
    '''읽어 들인 CSV 내용을 사람이 확인할 수 있게 전체 출력한다.

    특정 컬럼을 가정하지 않고 헤더와 값을 있는 그대로 보여준다(어떤 구조의
    CSV 든 표시 가능). 행이 많을 때 print 를 행마다 호출하면 느리므로 한
    번에 모아 출력한다.
    '''
    print('CSV 헤더:', ','.join(header))
    print('총 데이터 행 수:', len(rows))
    body = ['  ' + ', '.join(fields) for fields in rows]
    if body:
        print('\n'.join(body))


# ---------------------------------------------------------------------------
# 테이블 작업
# ---------------------------------------------------------------------------
def create_table(db):
    '''mars_weather 테이블을 생성한다(없을 때만).

    주의: 이 DDL 은 schema.sql 의 테이블 정의와 반드시 일치해야 한다.
    한쪽 컬럼/타입을 바꾸면 다른 쪽도 같이 고쳐야 한다(둘이 어긋나면
    Workbench 로 만든 테이블과 코드가 다르게 동작한다).
    '''
    query = (
        'CREATE TABLE IF NOT EXISTS {0} ('
        '    weather_id INT NOT NULL AUTO_INCREMENT,'
        '    mars_date  DATETIME NOT NULL,'
        '    temp       INT,'
        '    storm      INT,'
        '    PRIMARY KEY (weather_id)'
        ')'
    ).format(TABLE_NAME)
    db.execute(query)
    print('테이블 "{0}" 준비 완료.'.format(TABLE_NAME))


def insert_weathers(db, header, rows):
    '''CSV 가 실제 테이블 구조에 맞는지 판단한 뒤 적재한다.

    고정된 컬럼 목록을 쓰지 않고, SHOW COLUMNS 로 읽은 실제 구조에 CSV 를
    '위치 + 타입' 으로 맞춰 본다. 구조가 안 맞거나 한 행이라도 타입에 안
    맞으면 아무것도 넣지 않고 사유를 알린 뒤 돌아간다(전체 반영 방식).
    '''
    columns = get_table_columns(db)
    insert_names = [name for name, _type, is_auto in columns if not is_auto]

    # CSV 컬럼 수가 (1) 전체 컬럼 수와 같으면 자동증가 컬럼 자리는 건너뛰고,
    # (2) 자동증가 제외 컬럼 수와 같으면 그대로 매핑한다. 둘 다 아니면 거부.
    if len(header) == len(columns):
        plan = columns
    elif len(header) == len(insert_names):
        plan = [(name, col_type, is_auto) for name, col_type, is_auto in columns
                if not is_auto]
    else:
        print('CSV 구조가 테이블과 맞지 않아 반영할 수 없습니다.')
        print('  CSV 컬럼({0}개): {1}'.format(len(header), ','.join(header)))
        print('  테이블 컬럼({0}개): {1} (자동증가 제외 {2}개)'.format(
            len(columns), ','.join(name for name, _, _ in columns),
            len(insert_names)))
        return

    # 각 행을 테이블 타입에 맞춰 변환한다. 자동증가 컬럼은 건너뛴다.
    converted_rows = []
    problems = []
    for line_number, fields in enumerate(rows, start=2):
        if len(fields) != len(plan):
            problems.append((line_number, '컬럼 수가 맞지 않음'))
            continue
        values = []
        for (name, col_type, is_auto), raw in zip(plan, fields):
            if is_auto:
                continue
            value, reason = convert_value(col_type, raw)
            if reason is not None:
                problems.append((line_number, '{0}({1}): {2}'.format(
                    name, col_type, reason)))
                break
            values.append(value)
        else:
            converted_rows.append(tuple(values))

    if problems:
        print('테이블 속성에 맞지 않는 행이 {0}개 있어 이 파일은 '
              '반영하지 않습니다.'.format(len(problems)))
        for line_number, reason in problems:
            print('  - {0}번 줄: {1}'.format(line_number, reason))
        return

    before = db.fetch_all('SELECT COUNT(*) FROM {0}'.format(TABLE_NAME))[0][0]
    db.execute('TRUNCATE TABLE {0}'.format(TABLE_NAME))
    placeholders = ', '.join(['%s'] * len(insert_names))
    query = 'INSERT INTO {0} ({1}) VALUES ({2})'.format(
        TABLE_NAME, ', '.join(insert_names), placeholders)
    inserted = db.execute_many(query, converted_rows)
    after = db.fetch_all('SELECT COUNT(*) FROM {0}'.format(TABLE_NAME))[0][0]
    # TRUNCATE 로 기존 데이터를 모두 비우므로, 같은 CSV 를 다시 넣으면 행
    # 수가 똑같아 보일 수 있다. 비우고 새로 넣은 것임을 분명히 알린다.
    print('기존 {0}개 행을 비우고 {1}개 행을 새로 입력했습니다. '
          '(현재 "{2}" 행 수: {3})'.format(
              before, inserted, TABLE_NAME, after))


def format_table(names, rows):
    '''컬럼 이름과 행들을 받아 칸을 맞춘 표 문자열 리스트로 만든다.

    각 컬럼 폭은 헤더와 그 컬럼의 모든 값 중 가장 긴 것에 맞춘다. 컬럼명과
    값이 모두 ASCII(영문/숫자/날짜)라 글자 수 기준으로 정렬이 잘 맞는다.

        +------------+---------------------+------+-------+
        | weather_id | mars_date           | temp | storm |
        +------------+---------------------+------+-------+
        | 1          | 2050-01-01 00:00:00 | 21   | 56    |
        +------------+---------------------+------+-------+
    '''
    text_rows = [[str(value) for value in row] for row in rows]
    widths = [len(name) for name in names]
    for row in text_rows:
        for index, cell in enumerate(row):
            if len(cell) > widths[index]:
                widths[index] = len(cell)

    def make_row(cells):
        padded = [cell.ljust(widths[index]) for index, cell in enumerate(cells)]
        return '| ' + ' | '.join(padded) + ' |'

    border = '+' + '+'.join('-' * (width + 2) for width in widths) + '+'
    lines = [border, make_row(names), border]
    lines.extend(make_row(row) for row in text_rows)
    lines.append(border)
    return lines


def show_table(db):
    '''테이블에 적재된 내용을 전체 조회해서 표 형태로 보여준다.

    컬럼 구성을 가정하지 않고 실제 구조를 읽어 그대로 표로 출력한다. 행이
    많을 때 print 를 행마다 호출하면 느리므로 한 번에 모아 출력한다.
    '''
    names = [name for name, _type, _auto in get_table_columns(db)]
    total = db.fetch_all('SELECT COUNT(*) FROM {0}'.format(TABLE_NAME))
    print('테이블 행 수:', total[0][0] if total else 0)
    rows = db.fetch_all('SELECT {0} FROM {1} ORDER BY {2}'.format(
        ', '.join(names), TABLE_NAME, names[0]))
    print('\n'.join(format_table(names, rows)))


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
    missing = [key for key in ('host', 'user', 'password', 'database')
               if not DB_CONFIG[key]]
    if DB_CONFIG['port'] <= 0:
        missing.append('port')
    if missing:
        print('DB 접속 정보가 비어 있습니다:', ', '.join(missing))
        print('이 파일과 같은 폴더에 .env 를 만들고 값을 채우세요. '
              '(키 목록은 파일 상단 주석의 .env 예시 참고)')
        return
    try:
        with MySQLHelper(**DB_CONFIG) as db:
            action(db)
    except Exception as error:
        # 접속 실패, 권한 문제 등은 프로그램을 끝내지 않고 메시지로 안내한다.
        print('데이터베이스 작업 실패:', error)


def find_csv_files():
    '''같은 폴더에서 확장자가 .csv 인 파일 이름을 모두 찾아 정렬해 돌려준다.

    특정 파일명을 미리 정해두지 않고, 폴더에 있는 .csv 파일을 그때그때
    훑는다. 대소문자는 구분하지 않으므로 .CSV / .csv 를 모두 포함한다.
    '''
    names = [name for name in os.listdir(APP_DIR)
             if name.lower().endswith('.csv')]
    return sorted(names)


def choose_csv_file():
    '''사용할 CSV 파일의 실제 경로를 정해 돌려준다.

    폴더에 .csv 파일이 여러 개일 수 있으므로, 한 개든 여러 개든 항상
    목록을 보여주고 사용자가 직접 고르게 한다(0 은 취소 -> None).
    파일이 하나도 없으면 안내하고 None 을 돌려준다.
    '''
    files = find_csv_files()
    if not files:
        print('현재 폴더에 CSV 파일이 없습니다:', APP_DIR)
        return None

    print('현재 폴더에서 찾은 CSV 파일입니다. 어떤 파일을 읽을까요?')
    for index, name in enumerate(files, start=1):
        print('  {0}. {1}'.format(index, name))
    print('  0. 취소')
    answer = input('CSV 선택> ').strip()
    if not answer.isdigit():
        print('숫자를 입력하세요.')
        return None
    number = int(answer)
    if number == 0:
        return None
    if 1 <= number <= len(files):
        return os.path.join(APP_DIR, files[number - 1])
    print('범위를 벗어난 번호입니다.')
    return None


def read_csv_or_warn():
    '''사용할 CSV 파일을 정해 읽고 (헤더, 행목록) 을 돌려준다.

    파일이 없거나 선택을 취소하면 (None, None) 을 돌려준다. 파일 선택
    코드가 메뉴 곳곳에 중복되지 않도록 한 곳에 모았다.
    '''
    path = choose_csv_file()
    if path is None:
        return None, None
    return read_csv_file(path)


def main():
    while True:
        print_menu()
        try:
            choice = input('선택> ').strip()
        except (KeyboardInterrupt, EOFError):
            # Ctrl+C / Ctrl+D 를 눌러도 오류 추적(traceback) 없이 깔끔하게
            # 종료한다.
            print()
            print('종료합니다.')
            break

        if choice == '1':
            header, rows = read_csv_or_warn()
            if header is not None:
                print_csv_content(header, rows)
        elif choice == '2':
            run_with_db(create_table)
        elif choice == '3':
            header, rows = read_csv_or_warn()
            if rows:
                run_with_db(lambda db: insert_weathers(db, header, rows))
        elif choice == '4':
            run_with_db(show_table)
        elif choice == '0':
            print('종료합니다.')
            break
        else:
            print('잘못된 선택입니다. 0 ~ 4 중에서 고르세요.')


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        # 메뉴 입력이 아닌 동작(예: 긴 조회 출력) 도중 Ctrl+C 를 눌러도
        # 오류 추적 없이 종료한다.
        print()
        print('종료합니다.')
