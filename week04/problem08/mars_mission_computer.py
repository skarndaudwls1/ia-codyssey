# mars_mission_computer.py
# 화성 기지 미션 컴퓨터 — 환경 센서 모니터링 + 시스템 상태 진단

import json  # setting.txt (JSON 형식) 파싱 전용
import os
import platform
import sys
import threading
import time

try:
    import psutil
    _PSUTIL_OK = True
except ImportError:
    _PSUTIL_OK = False

_SENSOR_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', '..', 'week03', 'problem06'
)
sys.path.insert(0, _SENSOR_PATH)
from mars_mission_computer import DummySensor  # noqa: E402


# ── 화면 출력 유틸리티 ────────────────────────────────────────────────

def _display_width(text):
    # 한글 등 2바이트 문자는 폭 2, 나머지는 폭 1로 계산한다.
    return sum(2 if ord(ch) > 127 else 1 for ch in text)


def _divider(width, char='-'):
    return '+' + char * (width - 2) + '+'


def _center(text, width):
    pad = width - 2 - _display_width(text)
    left = pad // 2
    return '|' + ' ' * left + text + ' ' * (pad - left) + '|'


def _item(text, width):
    prefix = '|  ' + text
    return prefix + ' ' * max(width - _display_width(prefix) - 1, 0) + '|'


def _sub(text, width):
    prefix = '|     ' + text
    return prefix + ' ' * max(width - _display_width(prefix) - 1, 0) + '|'


def _format_value(val):
    # Python 값을 JSON 표현 문자열로 변환한다. (json 모듈 미사용)
    if isinstance(val, bool):
        return 'true' if val else 'false'
    if val is None:
        return 'null'
    if isinstance(val, str):
        escaped = val.replace('\\', '\\\\').replace('"', '\\"')
        return f'"{escaped}"'
    return str(val)


def _to_json(data, indent=4):
    # 딕셔너리를 JSON 형식 문자열로 직접 변환한다. (json 모듈 미사용)
    lines = ['{']
    items = list(data.items())
    for i, (key, val) in enumerate(items):
        comma = ',' if i < len(items) - 1 else ''
        lines.append(f'{" " * indent}"{key}": {_format_value(val)}{comma}')
    lines.append('}')
    return '\n'.join(lines)


def _json_box_lines(data, width):
    # 데이터를 박스 안 JSON 형태 줄 목록으로 반환한다. (json 모듈 미사용)
    lines = ['|  {' + ' ' * (width - 5) + '|']
    items = list(data.items())
    for i, (key, val) in enumerate(items):
        comma = ',' if i < len(items) - 1 else ''
        content = f'    "{key}": {_format_value(val)}{comma}'
        pad = width - 2 - _display_width(content) - 2
        lines.append(f'|  {content}{" " * max(pad, 0)}|')
    lines.append('|  }' + ' ' * (width - 5) + '|')
    return lines


# ── psutil 없을 때 /proc 파일 기반 대체 함수 ─────────────────────────

def _proc_mem_total():
    try:
        with open('/proc/meminfo', 'r') as f:
            for line in f:
                if line.startswith('MemTotal:'):
                    kb = int(line.split()[1])
                    return f'{kb / (1024 ** 2):.2f} GB'
    except (OSError, ValueError, IndexError):
        pass
    return '알 수 없음'


def _proc_cpu_usage():
    def _stat():
        with open('/proc/stat', 'r') as f:
            parts = f.readline().split()
        total = sum(int(x) for x in parts[1:])
        return total, int(parts[4])

    try:
        t1, i1 = _stat()
        time.sleep(0.5)
        t2, i2 = _stat()
        return f'{100.0 * (1 - (i2 - i1) / (t2 - t1)):.1f} %'
    except (OSError, ZeroDivisionError):
        return '알 수 없음'


def _proc_mem_usage():
    try:
        data = {}
        with open('/proc/meminfo', 'r') as f:
            for line in f:
                k, _, v = line.partition(':')
                data[k.strip()] = int(v.split()[0])
        total = data['MemTotal']
        avail = data.get('MemAvailable', data.get('MemFree', 0))
        return f'{100.0 * (total - avail) / total:.1f} %'
    except (OSError, KeyError, ZeroDivisionError, ValueError):
        return '알 수 없음'


# ── SystemInfo 클래스 ─────────────────────────────────────────────────

class SystemInfo:
    # 클래스 변수: 메서드명 → 출력 레이블 매핑
    SETTING_FILE = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 'setting.txt'
    )
    INFO_LABELS = {
        'get_os':           '운영체제',
        'get_os_version':   '운영체제 버전',
        'get_cpu_type':     'CPU 타입',
        'get_cpu_cores':    'CPU 코어 수',
        'get_memory_total': '메모리 크기',
    }
    LOAD_LABELS = {
        'get_cpu_usage':    'CPU 사용량',
        'get_memory_usage': '메모리 사용량',
    }

    # ── @staticmethod: 각 항목 데이터를 수집하는 메서드 ──────────────

    @staticmethod
    def get_os():
        try:
            return platform.system()
        except Exception as e:
            return f'오류: {e}'

    @staticmethod
    def get_os_version():
        try:
            return platform.version()
        except Exception as e:
            return f'오류: {e}'

    @staticmethod
    def get_cpu_type():
        try:
            return platform.processor() or platform.machine()
        except Exception as e:
            return f'오류: {e}'

    @staticmethod
    def get_cpu_cores():
        try:
            return os.cpu_count()
        except Exception as e:
            return f'오류: {e}'

    @staticmethod
    def get_memory_total():
        try:
            if _PSUTIL_OK:
                gb = psutil.virtual_memory().total / (1024 ** 3)
                return f'{gb:.2f} GB'
            return _proc_mem_total()
        except Exception as e:
            return f'오류: {e}'

    @staticmethod
    def get_cpu_usage():
        try:
            if _PSUTIL_OK:
                return f'{psutil.cpu_percent(interval=1):.1f} %'
            return _proc_cpu_usage()
        except Exception as e:
            return f'오류: {e}'

    @staticmethod
    def get_memory_usage():
        try:
            if _PSUTIL_OK:
                return f'{psutil.virtual_memory().percent:.1f} %'
            return _proc_mem_usage()
        except Exception as e:
            return f'오류: {e}'

    # ── @classmethod: 클래스 변수를 참조해 setting.txt 를 파싱한다 ────

    @classmethod
    def _load_settings(cls):
        # setting.txt (JSON 형식) 에서 항목별 출력 여부를 읽는다.
        # 파일이 없으면 INFO_LABELS + LOAD_LABELS 전체를 true 로 반환한다.
        all_methods = list(cls.INFO_LABELS) + list(cls.LOAD_LABELS)
        defaults = {m: True for m in all_methods}
        if not os.path.exists(cls.SETTING_FILE):
            return defaults
        try:
            with open(cls.SETTING_FILE, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            # 알 수 없는 키는 무시하고 기본값으로 채운다.
            return {m: bool(settings.get(m, True)) for m in all_methods}
        except (OSError, json.JSONDecodeError) as e:
            print(f'[경고] 설정 파일 읽기 실패: {e}')
            return defaults


# ── MissionComputer 클래스 ───────────────────────────────────────────

class MissionComputer:
    # 클래스 변수: 모든 인스턴스가 공유하는 설정값
    AVG_INTERVAL = 60
    SCREEN_WIDTH = 60
    SENSOR_META = {
        'mars_base_internal_temperature': ('화성 기지 내부 온도',      '°C'),
        'mars_base_external_temperature': ('화성 기지 외부 온도',      '°C'),
        'mars_base_internal_humidity':    ('화성 기지 내부 습도',      '%'),
        'mars_base_external_illuminance': ('화성 기지 외부 광량',      'W/m²'),
        'mars_base_internal_co2':         ('화성 기지 내부 CO2',       '%'),
        'mars_base_internal_oxygen':      ('화성 기지 내부 산소 농도', '%'),
    }

    def __init__(self):
        # 인스턴스 변수: 각 인스턴스가 독립적으로 유지하는 상태값
        self.env_values = {
            'mars_base_internal_temperature': 0,
            'mars_base_external_temperature': 0,
            'mars_base_internal_humidity':    0,
            'mars_base_external_illuminance': 0,
            'mars_base_internal_co2':         0,
            'mars_base_internal_oxygen':      0,
        }
        self.ds = DummySensor()   # DummySensor 를 ds 로 인스턴스화
        self._history = []        # private: 평균 계산용 이력
        self._avg = None          # private: 마지막으로 계산된 5분 평균값
        self._running = False     # private: 센서 스레드 제어 플래그

    # ── public: 환경 센서 모니터링 ───────────────────────────────────

    def get_sensor_data(self):
        # 보너스: 센서 출력(daemon thread)과 메인 스레드를 분리해 처리.
        # Ctrl+C 입력 시 센서 루프를 중단한다.
        self._running = True
        thread = threading.Thread(target=self._sensor_loop, daemon=True)
        thread.start()
        try:
            while self._running:
                time.sleep(1)
        except KeyboardInterrupt:
            self._running = False
        thread.join(timeout=1)
        print('\nSystem stopped....')

    # ── public: 시스템 정보 ──────────────────────────────────────────

    def get_mission_computer_info(self):
        print(_to_json(self._collect(SystemInfo.INFO_LABELS)))

    # ── public: 시스템 부하 ──────────────────────────────────────────

    def get_mission_computer_load(self):
        print(_to_json(self._collect(SystemInfo.LOAD_LABELS)))

    # ── private: 활성화된 항목만 수집하는 공통 헬퍼 ──────────────────

    def _collect(self, labels):
        # setting.txt 설정에 따라 활성화된 항목만 getattr() 로 호출해 반환한다.
        settings = SystemInfo._load_settings()
        return {
            label: getattr(SystemInfo, method_name)()
            for method_name, label in labels.items()
            if settings.get(method_name, True)
        }

    # ── private: 센서 루프 (daemon thread 에서 실행) ──────────────────

    def _sensor_loop(self):
        count = 0
        while self._running:
            self.ds.set_env()
            sensor = self.ds.get_env()
            for key in self.env_values:
                self.env_values[key] = sensor[key]
            self._history.append(dict(self.env_values))
            if len(self._history) > MissionComputer.AVG_INTERVAL:
                del self._history[:-MissionComputer.AVG_INTERVAL]
            count += 1
            if count % MissionComputer.AVG_INTERVAL == 0:
                self._avg = self._calc_avg()
            self._render_sensor_screen()
            # 0.1초 단위로 쪼개 sleep — Ctrl+C 후 빠르게 반응한다.
            for _ in range(50):
                if not self._running:
                    break
                time.sleep(0.1)

    def _calc_avg(self):
        # private: 최근 AVG_INTERVAL 개 데이터의 항목별 평균을 계산한다.
        recent = self._history[-MissionComputer.AVG_INTERVAL:]
        return {
            k: round(sum(r[k] for r in recent) / len(recent), 4)
            for k in self.env_values
        }

    def _render_sensor_screen(self):
        # private: 모니터링 화면을 top 방식으로 전체 갱신한다.
        w = MissionComputer.SCREEN_WIDTH
        print('\033[2J\033[H', end='')
        print(_divider(w, '='))
        print(_center('화성 기지 환경 모니터링', w))
        print(_center(time.strftime('%Y-%m-%d %H:%M:%S'), w))
        print(_divider(w, '='))
        display = {}
        for key, val in self.env_values.items():
            label, unit = MissionComputer.SENSOR_META.get(key, (key, ''))
            display[f'{label} ({unit})'] = val
        for line in _json_box_lines(display, w):
            print(line)
        print(_divider(w, '='))
        if self._avg is not None:
            print()
            print(_divider(w, '='))
            print(_center('5분 평균값', w))
            print(_divider(w, '-'))
            avg_display = {}
            for key, val in self._avg.items():
                label, unit = MissionComputer.SENSOR_META.get(key, (key, ''))
                avg_display[f'{label} ({unit})'] = val
            for line in _json_box_lines(avg_display, w):
                print(line)
            print(_divider(w, '='))
        print('\n  Ctrl+C 로 중지')

    # ── @staticmethod: 인스턴스/클래스 상태와 무관한 순수 유틸 ────────

    @staticmethod
    def _display_width(text):
        # 한글 등 2바이트 문자는 폭 2, 나머지는 폭 1로 계산한다.
        return sum(2 if ord(ch) > 127 else 1 for ch in text)


RunComputer = MissionComputer()


# ── 메뉴 및 진입점 ───────────────────────────────────────────────────

def _print_menu():
    w = MissionComputer.SCREEN_WIDTH
    print()
    print(_divider(w, '='))
    print(_center('화성 기지 미션 컴퓨터', w))
    print(_divider(w, '-'))
    print(_item('1. 환경 센서 모니터링 시작', w))
    print(_sub('(5초마다 갱신 | Ctrl+C 로 중지)', w))
    print(_item('2. 시스템 정보 보기', w))
    print(_item('3. 시스템 부하 보기', w))
    print(_item('0. 종료', w))
    print(_divider(w, '-'))


def main():
    try:
        while True:
            _print_menu()
            choice = input('  번호를 선택하세요: ').strip()
            if choice == '1':
                RunComputer.get_sensor_data()
            elif choice == '2':
                RunComputer.get_mission_computer_info()
            elif choice == '3':
                RunComputer.get_mission_computer_load()
            elif choice == '0':
                print('  미션 컴퓨터를 종료합니다.')
                break
            else:
                print('  [안내] 올바른 번호를 입력하세요.')
    except KeyboardInterrupt:
        print('\n  미션 컴퓨터를 종료합니다.')


if __name__ == '__main__':
    main()