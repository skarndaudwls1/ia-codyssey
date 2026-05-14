# dom.py
# 화성 기지 돔 설계 계산기 — 메인 실행 파일

PI = 3.14159265358979
MARS_GRAVITY_RATIO = 0.376
MATERIAL_DENSITY = {
    '유리': 2.4,
    '알루미늄': 2.7,
    '탄소강': 7.85,
}
SAVE_FILE = 'design_dome.py'

# 전역변수 — 마지막 계산 결과 저장
material = '유리'
diameter = 0.0
thickness = 1.0
area = 0.0
weight = 0.0


def sphere_area(diameter, material='유리', thickness=1.0):
    # 반구 면적과 화성 기준 무게를 계산해서 반환한다.
    # 반구 면적 = 2 * PI * r²
    # 무게(화성) = 면적(cm²) * 두께 * 밀도 / 1000 * 화성중력비율
    radius = diameter / 2
    calc_area = 2 * PI * radius ** 2
    density = MATERIAL_DENSITY.get(material, MATERIAL_DENSITY['유리'])
    area_cm2 = calc_area * 10000
    volume_cm3 = area_cm2 * thickness
    weight_gram = volume_cm3 * density
    mars_weight_kg = (weight_gram / 1000) * MARS_GRAVITY_RATIO
    return calc_area, mars_weight_kg


def save_design(mat, dia, thick, calc_area, calc_weight, file_path):
    # 계산 결과를 텍스트 형태로 design_dome.py 에 저장한다.
    result = (
        f'재질 ==> {mat}, '
        f'지름 ==> {round(dia, 3)}, '
        f'두께 ==> {round(thick, 3)}, '
        f'면적 ==> {round(calc_area, 3)}, '
        f'무게 ==> {round(calc_weight, 3)} kg'
    )
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(result + '\n')
        print(f'[완료] {file_path} 저장 성공')
        print(f'[내용] {result}')

    except PermissionError:
        print(f'[오류] 파일 쓰기 권한이 없습니다: {file_path}')
    except OSError as e:
        print(f'[오류] 파일 저장 실패: {e}')


def get_material():
    # 사용자로부터 재질을 입력받아 반환한다.
    # 유효하지 않은 입력은 재입력 요청한다.
    material_map = {
        '1': '유리',
        '2': '알루미늄',
        '3': '탄소강',
        '유리': '유리',
        '알루미늄': '알루미늄',
        '탄소강': '탄소강',
    }
    while True:
        print('\n재질을 선택하세요:')
        print('  1. 유리')
        print('  2. 알루미늄')
        print('  3. 탄소강')
        choice = input('선택: ').strip()
        if choice in material_map:
            return material_map[choice]
        print('  [오류] 올바른 재질을 선택해주세요. (1/2/3 또는 유리/알루미늄/탄소강)')


def get_float(prompt, default=None, min_val=None):
    # 숫자를 입력받는다. 문자 입력 시 오류 없이 재입력 요청 (보너스 과제).
    while True:
        raw = input(prompt).strip()
        if raw == '' and default is not None:
            return default
        try:
            val = float(raw)
        except ValueError:
            print('  [오류] 숫자를 입력해주세요.')
            continue
        if min_val is not None and val <= min_val:
            print(f'  [오류] {min_val}보다 큰 값을 입력해주세요.')
            continue
        return val


def print_result(mat, dia, thick, calc_area, calc_weight):
    # 계산 결과를 지정된 형식으로 출력한다.
    print('\n=== 계산 결과 ===')
    print(
        f'재질 ==> {mat}, '
        f'지름 ==> {round(dia, 3)}, '
        f'두께 ==> {round(thick, 3)}, '
        f'면적 ==> {round(calc_area, 3)}, '
        f'무게 ==> {round(calc_weight, 3)} kg'
    )


def print_globals():
    # 전역변수에 저장된 마지막 계산값을 출력한다.
    print('\n=== 전역변수 저장값 ===')
    print(f'  재질:  {material}')
    print(f'  지름:  {round(diameter, 3)} m')
    print(f'  두께:  {round(thickness, 3)} cm')
    print(f'  면적:  {round(area, 3)} m²')
    print(f'  무게:  {round(weight, 3)} kg (화성 기준)')


def print_menu():
    # 메뉴를 출력한다.
    print('\n============================')
    print(' 화성 기지 돔 설계 계산기')
    print('============================')
    print('1. 돔 면적 및 무게 계산')
    print('2. 마지막 계산 결과 보기')
    print('3. 결과를 design_dome.py 로 저장')
    print('0. 종료')
    print('----------------------------')


def main():
    global material, diameter, thickness, area, weight

    while True:
        print_menu()
        choice = input('번호를 선택하세요: ').strip()

        if choice == '1':
            print('\n=== 돔 설계 계산 ===')
            mat = get_material()
            dia = get_float('지름을 입력하세요 (m, 0 초과): ', min_val=0)
            thick = get_float('두께를 입력하세요 (cm, 기본값 1): ', default=1.0, min_val=0)

            calc_area, calc_weight = sphere_area(dia, mat, thick)

            # 전역변수 저장
            material = mat
            diameter = dia
            thickness = thick
            area = calc_area
            weight = calc_weight

            print_result(mat, dia, thick, calc_area, calc_weight)

        elif choice == '2':
            if diameter == 0.0:
                print('\n[안내] 아직 계산한 결과가 없습니다.')
            else:
                print_globals()

        elif choice == '3':
            if diameter == 0.0:
                print('\n[안내] 먼저 1번으로 계산을 진행해주세요.')
            else:
                save_design(material, diameter, thickness, area, weight, SAVE_FILE)

        elif choice == '0':
            print('종료합니다.')
            break

        else:
            print('[안내] 올바른 번호를 입력하세요.')


if __name__ == '__main__':
    main()