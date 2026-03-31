# Mission.py
# 화성 기지 미션 컴퓨터 - 환경 센서 메뉴

from mars_mission_computer import DummySensor

ds = DummySensor()


def print_env(env):
    # 환경 값을 보기 좋게 출력한다.
    print('\n=== 화성 기지 환경 값 ===')
    print(f'  기지 내부 온도       : {env["mars_base_internal_temperature"]} °C')
    print(f'  기지 외부 온도       : {env["mars_base_external_temperature"]} °C')
    print(f'  기지 내부 습도       : {env["mars_base_internal_humidity"]} %')
    print(f'  기지 외부 광량       : {env["mars_base_external_illuminance"]} W/m²')
    print(f'  기지 내부 CO₂ 농도   : {env["mars_base_internal_co2"]} %')
    print(f'  기지 내부 산소 농도  : {env["mars_base_internal_oxygen"]} %')


def print_menu():
    print('\n============================')
    print('   화성 기지 미션 컴퓨터')
    print('============================')
    print('1. 환경 센서 값 읽기')
    print('2. 마지막으로 읽은 환경 값 출력')
    print('0. 종료')
    print('----------------------------')


def main():
    last_env = None

    while True:
        print_menu()
        choice = input('번호를 선택하세요: ').strip()

        if choice == '1':
            ds.set_env()
            last_env = ds.get_env()
            print_env(last_env)
            print('[완료] sensor.log에 기록되었습니다.')

        elif choice == '2':
            if last_env is None:
                print('[안내] 아직 센서를 읽지 않았습니다. 먼저 1번을 선택하세요.')
            else:
                print_env(last_env)

        elif choice == '0':
            print('미션 컴퓨터를 종료합니다.')
            break

        else:
            print('[안내] 올바른 번호를 입력하세요.')

        input('\n계속하려면 Enter 를 누르세요...')


if __name__ == '__main__':
    main()
