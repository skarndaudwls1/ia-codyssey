# mars_mission_computer.py
# 화성 기지 미션 컴퓨터 — 환경 센서 실시간 모니터링

import os
import sys
import time

# DummySensor 클래스를 problem06에서 가져온다.
_SENSOR_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            '..', '..', 'week03', 'problem06')
sys.path.insert(0, _SENSOR_PATH)
from mars_mission_computer import DummySensor  # noqa: E402

# 5분 평균 출력 주기 (5초 × 60회 = 300초)
평균_출력_주기 = 60
화면_너비 = 60

# 영문 키 → (한국어 레이블, 단위) 매핑
센서_정보 = {
    'mars_base_internal_temperature': ('화성 기지 내부 온도',      '°C'),
    'mars_base_external_temperature': ('화성 기지 외부 온도',      '°C'),
    'mars_base_internal_humidity':    ('화성 기지 내부 습도',      '%'),
    'mars_base_external_illuminance': ('화성 기지 외부 광량',      'W/m²'),
    'mars_base_internal_co2':         ('화성 기지 내부 CO2',       '%'),
    'mars_base_internal_oxygen':      ('화성 기지 내부 산소 농도', '%'),
}


def _display_width(text):
    # 한글 등 2바이트 문자는 폭 2로 계산한다.
    return sum(2 if ord(ch) > 127 else 1 for ch in text)


def _현재_시간():
    # 현재 로컬 시간을 문자열로 반환한다.
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())


def _구분선(char='-'):
    return '+' + char * (화면_너비 - 2) + '+'


def _가운데_줄(text):
    # 텍스트를 화면 너비에 맞춰 가운데 정렬한 행을 반환한다.
    표시폭 = _display_width(text)
    여백 = 화면_너비 - 2 - 표시폭
    좌 = 여백 // 2
    우 = 여백 - 좌
    return '|' + ' ' * 좌 + text + ' ' * 우 + '|'


def _json_블록(env):
    # env 딕셔너리를 JSON 형태의 박스 안 줄 목록으로 반환한다.
    lines = ['|  {' + ' ' * (화면_너비 - 5) + '|']
    항목들 = list(env.items())
    for i, (키, 값) in enumerate(항목들):
        레이블, 단위 = 센서_정보.get(키, (키, ''))
        쉼표 = ',' if i < len(항목들) - 1 else ''
        내용 = f'    "{레이블}" : {값} {단위}{쉼표}'
        패딩 = 화면_너비 - 2 - _display_width(내용) - 2
        lines.append(f'|  {내용}{" " * max(패딩, 0)}|')
    lines.append('|  }' + ' ' * (화면_너비 - 5) + '|')
    return lines


def _모니터링_화면(env, 최근_평균=None):
    # 터미널 전체를 갱신하며 모니터링 데이터를 출력한다. (top 방식)
    # 5분 평균이 계산된 경우 현재값 아래에 함께 표시한다.
    print('\033[2J\033[H', end='')

    # 현재 센서값 출력
    print(_구분선('='))
    print(_가운데_줄('화성 기지 환경 모니터링'))
    print(_가운데_줄(_현재_시간()))
    print(_구분선('='))
    for 줄 in _json_블록(env):
        print(줄)
    print(_구분선('='))

    # 5분 평균값 출력 (최초 5분 경과 후부터 표시)
    if 최근_평균 is not None:
        print()
        print(_구분선('='))
        print(_가운데_줄('5분 평균값'))
        print(_구분선('-'))
        for 줄 in _json_블록(최근_평균):
            print(줄)
        print(_구분선('='))

    print('\n  Ctrl+C 로 중지')


class MissionComputer:
    def __init__(self):
        self.env_values = {
            'mars_base_internal_temperature': 0,
            'mars_base_external_temperature': 0,
            'mars_base_internal_humidity':    0,
            'mars_base_external_illuminance': 0,
            'mars_base_internal_co2':         0,
            'mars_base_internal_oxygen':      0,
        }
        self.ds = DummySensor()
        self._이력 = []
        self._최근_평균 = None  # 마지막으로 계산된 5분 평균값

    def get_sensor_data(self):
        # 5초마다 센서 값을 읽어 모니터링 화면으로 출력한다.
        # 보너스: Ctrl+C 입력 시 'System stopped....' 출력 후 중지.
        # 보너스: 5분(60회)마다 평균값을 화면 하단에 함께 표시한다.
        읽기_횟수 = 0
        try:
            while True:
                self.ds.set_env()
                센서값 = self.ds.get_env()
                for 키 in self.env_values:
                    self.env_values[키] = 센서값[키]

                self._이력.append(dict(self.env_values))
                읽기_횟수 += 1

                if 읽기_횟수 % 평균_출력_주기 == 0:
                    self._최근_평균 = self._평균_계산()

                _모니터링_화면(self.env_values, self._최근_평균)

                time.sleep(5)

        except KeyboardInterrupt:
            print('\nSystem stopped....')

    def _평균_계산(self):
        # 최근 60개(5분) 데이터의 항목별 평균값을 계산해 반환한다.
        최근 = self._이력[-평균_출력_주기:]
        return {
            키: round(sum(행[키] for 행 in 최근) / len(최근), 4)
            for 키 in self.env_values
        }


RunComputer = MissionComputer()


def print_menu():
    print()
    print(_구분선('='))
    print(_가운데_줄('화성 기지 미션 컴퓨터'))
    print(_구분선('-'))
    print('|  1. 환경 센서 모니터링 시작' + ' ' * (화면_너비 - 30) + '|')
    print('|     (5초마다 갱신 | Ctrl+C 로 중지)' + ' ' * (화면_너비 - 38) + '|')
    print('|  0. 종료' + ' ' * (화면_너비 - 11) + '|')
    print(_구분선('-'))


def main():
    try:
        while True:
            print_menu()
            선택 = input('  번호를 선택하세요: ').strip()

            if 선택 == '1':
                RunComputer.get_sensor_data()
            elif 선택 == '0':
                print('  미션 컴퓨터를 종료합니다.')
                break
            else:
                print('  [안내] 올바른 번호를 입력하세요.')
    except KeyboardInterrupt:
        print('\n  미션 컴퓨터를 종료합니다.')


if __name__ == '__main__':
    main()
