# design_dome.py
# 화성 기지 주요 부품 구조 강도 분석

import numpy as np

CSV_FILES = [
    'mars_base_main_parts-001.csv',
    'mars_base_main_parts-002.csv',
    'mars_base_main_parts-003.csv',
]
OUTPUT_FILE = 'parts_to_work_on.csv'

# 전역 배열 변수
arr1 = None
arr2 = None
arr3 = None
parts = None
parts_avg = None
parts_weak = None
부품_이름 = None


def load_csv_files():
    # 3개의 CSV 파일에서 강도 값(2열)을 numpy로 읽어 arr1, arr2, arr3에 저장한다.
    global arr1, arr2, arr3, 부품_이름
    try:
        arr1 = np.genfromtxt(CSV_FILES[0], delimiter=',', skip_header=1, usecols=(1,))
        arr2 = np.genfromtxt(CSV_FILES[1], delimiter=',', skip_header=1, usecols=(1,))
        arr3 = np.genfromtxt(CSV_FILES[2], delimiter=',', skip_header=1, usecols=(1,))
        부품_이름 = np.genfromtxt(
            CSV_FILES[0], delimiter=',', skip_header=1, usecols=(0,), dtype=str
        )
        print('\n[완료] CSV 파일 3개 읽기 완료.')
        print(f'  arr1: {arr1.shape}  arr2: {arr2.shape}  arr3: {arr3.shape}')
        print(f'\narr1:\n{arr1}')
        print(f'\narr2:\n{arr2}')
        print(f'\narr3:\n{arr3}')
    except FileNotFoundError as e:
        print(f'[오류] 파일을 찾을 수 없습니다: {e}')
    except OSError as e:
        print(f'[오류] 파일 읽기 실패: {e}')


def merge_arrays():
    # 3개 배열을 열 방향으로 합쳐 parts ndarray를 생성한다. (부품 수 × 3)
    global parts
    if arr1 is None or arr2 is None or arr3 is None:
        print('\n[안내] 먼저 1번으로 CSV 파일을 읽어주세요.')
        return
    parts = np.column_stack([arr1, arr2, arr3])
    print('\n[완료] 배열 합치기 완료.')
    print(f'  parts 크기: {parts.shape}  (부품 수 × 측정 횟수)')
    print(f'\nparts:\n{parts}')


def calc_average():
    # parts의 각 부품(행)별 강도 평균값을 계산한다.
    global parts_avg
    if parts is None:
        print('\n[안내] 먼저 2번으로 배열을 합쳐주세요.')
        return
    parts_avg = np.mean(parts, axis=1)
    print('\n[완료] 각 항목별 평균 강도:')
    for i, (이름, avg) in enumerate(zip(부품_이름, parts_avg)):
        print(f'  {i + 1:3d}. {이름:<35} 평균: {avg:.2f}')


def save_weak_parts():
    # 평균 강도가 50 미만인 부품을 추출하여 parts_to_work_on.csv에 저장한다.
    global parts_weak
    if parts_avg is None:
        print('\n[안내] 먼저 3번으로 평균값을 계산해주세요.')
        return
    mask = parts_avg < 50
    parts_weak = parts[mask]
    취약_이름 = 부품_이름[mask]
    print(f'\n[완료] 평균 강도 50 미만 취약 부품: {parts_weak.shape[0]}개')
    for 이름, avg in zip(취약_이름, parts_avg[mask]):
        print(f'  {이름:<35} 평균: {avg:.2f}')
    try:
        np.savetxt(OUTPUT_FILE, parts_weak, delimiter=',', fmt='%.1f')
        print(f'\n[완료] {OUTPUT_FILE} 저장 완료')
    except PermissionError:
        print(f'[오류] 파일 쓰기 권한이 없습니다: {OUTPUT_FILE}')
    except OSError as e:
        print(f'[오류] 파일 저장 실패: {e}')


def bonus_transpose():
    # parts_to_work_on.csv를 읽어 parts2에 저장하고 전치행렬을 parts3으로 출력한다.
    try:
        parts2 = np.genfromtxt(OUTPUT_FILE, delimiter=',')
        print(f'\n[보너스] parts2 (원본, 크기: {parts2.shape}):\n{parts2}')
        parts3 = parts2.T
        print(f'\n[보너스] parts3 (전치행렬, 크기: {parts3.shape}):\n{parts3}')
    except FileNotFoundError:
        print(f'\n[안내] {OUTPUT_FILE} 파일이 없습니다. 먼저 4번을 실행해주세요.')
    except OSError as e:
        print(f'[오류] 파일 읽기 실패: {e}')


def print_menu():
    print('\n============================')
    print(' 화성 기지 부품 구조 강도 분석')
    print('============================')
    print('1. CSV 파일 읽기 (arr1, arr2, arr3)')
    print('2. 배열 합치기 (parts 생성)')
    print('3. 항목별 평균 강도 계산')
    print('4. 취약 부품 추출 및 저장')
    print('5. [보너스] 전치행렬 계산 및 출력')
    print('0. 종료')
    print('----------------------------')


def main():
    while True:
        print_menu()
        선택 = input('번호를 선택하세요: ').strip()

        if 선택 == '1':
            load_csv_files()
        elif 선택 == '2':
            merge_arrays()
        elif 선택 == '3':
            calc_average()
        elif 선택 == '4':
            save_weak_parts()
        elif 선택 == '5':
            bonus_transpose()
        elif 선택 == '0':
            print('종료합니다.')
            break
        else:
            print('[안내] 올바른 번호를 입력하세요.')


if __name__ == '__main__':
    main()
