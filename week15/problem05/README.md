# 문제5 화성의 날씨 데이터를 데이터베이스에 담아라

# 수행 과제
# MySQL Workbench + 데이터를 담을 수 있는 테이블을 생성
<img width="297" height="178" alt="image" src="https://github.com/user-attachments/assets/8fb63c41-96f4-45ff-80f1-2b3c7152c605" />
<img width="516" height="808" alt="image" src="https://github.com/user-attachments/assets/260b07ce-bbf1-46bc-b509-d5ea08e2f5fd" />

# 제공되는 mars_weathers_data.csv 파일을 읽어서 내용을 확인하는 코드를 작성
<img width="471" height="527" alt="image" src="https://github.com/user-attachments/assets/a2169fd8-ee6f-4534-963c-60c151291413" />

# mars_weathers_data.csv의 내용을 방금 작성한 mars_weathers 테이블에 입력한다. 이 때 mars_weathers_data.csv의 내용을 INSERT 쿼리로 변환해서 반복적으로 실행한다.
<img width="721" height="248" alt="image" src="https://github.com/user-attachments/assets/9c0d4655-6a26-40e1-97f6-faefa36e6d17" />

# 결과
<img width="475" height="833" alt="image" src="https://github.com/user-attachments/assets/9c68d1df-2051-488c-ae5b-8fc2f673d9d1" />

# 보너스 과제
MySQLHelper 클래스를 만들어서 데이터베이스 연결 및 쿼리 등을 쉽게 할 수 있게 구성한다.
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
