# DummySensor.py
# 화성 기지 더미 센서 클래스

import random

LOG_FILE = 'sensor.log'
RTC_TIME_FILE = '/sys/class/rtc/rtc0/time'
RTC_DATE_FILE = '/sys/class/rtc/rtc0/date'
UTC_OFFSET = 9  # KST = UTC+9

# 센서 항목 추가/수정은 이 딕셔너리 한 곳만 변경하면 된다.
# 형식: 키: (최솟값, 최댓값, 소수점 자리수)
# 소수점 자리수가 0이면 정수로 생성한다.
ENV_RANGES = {
    'mars_base_internal_temperature': (18,   30,   0),
    'mars_base_external_temperature': (0,    21,   0),
    'mars_base_internal_humidity':    (50,   60,   0),
    'mars_base_external_illuminance': (500,  715,  0),
    'mars_base_internal_co2':         (0.02, 0.1,  4),
    'mars_base_internal_oxygen':      (4,    7,    0),
}

# 헤더 레이블도 ENV_RANGES 키 순서에 맞게 정의한다.
HEADER_LABELS = {
    'mars_base_internal_temperature': '내부온도(°C)',
    'mars_base_external_temperature': '외부온도(°C)',
    'mars_base_internal_humidity':    '내부습도(%)',
    'mars_base_external_illuminance': '외부광량(W/m²)',
    'mars_base_internal_co2':         'CO2(%)',
    'mars_base_internal_oxygen':      '산소농도(%)',
}

HEADER = ['날짜/시간'] + [HEADER_LABELS[k] for k in ENV_RANGES]


def _days_in_month(year, month):
    # 해당 월의 일 수를 반환한다. (윤년 처리 포함)
    days = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    if month == 2 and (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)):
        return 29
    return days[month]


def _utc_to_local(year, month, day, hour, minute, second):
    # UTC 시각을 로컬 시간(UTC+9)으로 변환한다.
    hour += UTC_OFFSET
    if hour >= 24:
        hour -= 24
        day += 1
        if day > _days_in_month(year, month):
            day = 1
            month += 1
            if month > 12:
                month = 1
                year += 1
    return year, month, day, hour, minute, second


def get_current_time():
    # 시스템 파일에서 UTC 시간을 읽어 로컬 시간 문자열로 반환한다.
    try:
        with open(RTC_TIME_FILE, 'r') as f:
            time_str = f.read().strip()
        with open(RTC_DATE_FILE, 'r') as f:
            date_str = f.read().strip()

        h = int(time_str[0:2])
        m = int(time_str[3:5])
        s = int(time_str[6:8])
        y = int(date_str[0:4])
        mo = int(date_str[5:7])
        d = int(date_str[8:10])

        y, mo, d, h, m, s = _utc_to_local(y, mo, d, h, m, s)
        return f'{y:04d}-{mo:02d}-{d:02d} {h:02d}:{m:02d}:{s:02d}'
    except (OSError, ValueError):
        return '날짜/시간 미확인'


def _display_width(text):
    # 한글 등 멀티바이트 문자는 폭 2, 나머지는 폭 1로 계산한다.
    return sum(2 if ord(ch) > 127 else 1 for ch in text)


def _pad_cell(text, width):
    # 표시 너비 기준으로 문자열을 공백으로 채운다.
    return text + ' ' * (width - _display_width(text))


def _read_data_rows():
    # 기존 로그 파일에서 데이터 행만 추출해 반환한다.
    data_rows = []
    try:
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line.startswith('|'):
                    continue
                try:
                    cells = [c.strip() for c in line.strip('|').split('|')]
                    if cells and cells[0] != HEADER[0]:
                        data_rows.append(cells)
                except (IndexError, ValueError):
                    # 손상된 행은 건너뛴다.
                    continue
    except FileNotFoundError:
        pass
    except (OSError, UnicodeDecodeError) as e:
        print(f'[오류] 로그 파일 읽기 실패: {e}')
    return data_rows


def _write_table(data_rows):
    # 헤더 + 데이터 행 전체를 표 형식으로 파일에 저장한다.
    all_rows = [HEADER] + data_rows
    col_widths = [
        max(_display_width(row[i]) for row in all_rows)
        for i in range(len(HEADER))
    ]
    sep = '+' + '+'.join('-' * (w + 2) for w in col_widths) + '+'

    lines = [sep]
    for idx, row in enumerate(all_rows):
        cells = ' | '.join(_pad_cell(cell, col_widths[i]) for i, cell in enumerate(row))
        lines.append(f'| {cells} |')
        if idx == 0:
            lines.append(sep)
    lines.append(sep)

    try:
        with open(LOG_FILE, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines) + '\n')
    except OSError as e:
        print(f'[오류] 로그 저장 실패: {e}')


class DummySensor:
    def __init__(self):
        self.env_values = {key: 0 for key in ENV_RANGES}

    def set_env(self):
        # ENV_RANGES 기준으로 각 항목에 랜덤 값을 생성해 채운다.
        # 소수점 자리수가 0이면 정수, 그 외에는 지정 자릿수의 실수로 생성한다.
        for key, (lo, hi, digits) in ENV_RANGES.items():
            if digits == 0:
                self.env_values[key] = random.randint(int(lo), int(hi))
            else:
                self.env_values[key] = round(random.uniform(lo, hi), digits)

    def get_env(self):
        # 보너스: 환경 값을 표 형식으로 로그 파일에 누적 기록한다.
        new_row = [get_current_time()] + [str(self.env_values[k]) for k in ENV_RANGES]
        data_rows = _read_data_rows()
        data_rows.append(new_row)
        _write_table(data_rows)
        return self.env_values


if __name__ == '__main__':
    ds = DummySensor()
    ds.set_env()
    print(ds.get_env())
