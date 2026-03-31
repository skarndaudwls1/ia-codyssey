# mars_mission_computer.py
# 화성 기지 더미 센서 클래스

import random
import datetime

LOG_FILE = 'sensor.log'


class DummySensor:
    def __init__(self):
        self.env_values = {
            'mars_base_internal_temperature': 0,
            'mars_base_external_temperature': 0,
            'mars_base_internal_humidity': 0,
            'mars_base_external_illuminance': 0,
            'mars_base_internal_co2': 0,
            'mars_base_internal_oxygen': 0,
        }

    def set_env(self):
        # 각 항목에 지정된 범위 안의 랜덤 값을 생성해 채운다.
        self.env_values['mars_base_internal_temperature'] = round(random.uniform(18, 30), 2)
        self.env_values['mars_base_external_temperature'] = round(random.uniform(0, 21), 2)
        self.env_values['mars_base_internal_humidity'] = round(random.uniform(50, 60), 2)
        self.env_values['mars_base_external_illuminance'] = round(random.uniform(500, 715), 2)
        self.env_values['mars_base_internal_co2'] = round(random.uniform(0.02, 0.1), 4)
        self.env_values['mars_base_internal_oxygen'] = round(random.uniform(4, 7), 2)

    def get_env(self):
        # 보너스: 날짜/시간과 환경 값을 로그 파일에 기록한다.
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_line = (
            f'{now},'
            f'{self.env_values["mars_base_internal_temperature"]},'
            f'{self.env_values["mars_base_external_temperature"]},'
            f'{self.env_values["mars_base_internal_humidity"]},'
            f'{self.env_values["mars_base_external_illuminance"]},'
            f'{self.env_values["mars_base_internal_co2"]},'
            f'{self.env_values["mars_base_internal_oxygen"]}'
        )
        try:
            with open(LOG_FILE, 'a', encoding='utf-8') as f:
                f.write(log_line + '\n')
        except OSError as e:
            print(f'[오류] 로그 저장 실패: {e}')

        return self.env_values


if __name__ == '__main__':
    ds = DummySensor()
    ds.set_env()
    print(ds.get_env())
