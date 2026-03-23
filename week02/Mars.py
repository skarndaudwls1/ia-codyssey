# Mars.py
# 화성 기지 인화성 물질 분류 시스템

READ_FILE = 'Mars_Base_Inventory_List.csv'
WRITE_FILE = 'Mars_Base_Inventory_danger.csv'
DANGER_THRESHOLD = 0.7


def read_csv(file_path):
    """CSV 파일을 한 번만 읽어서 2차원 리스트로 반환한다."""
    rows = []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rows.append(line.split(','))

    except FileNotFoundError:
        print(f'[오류] 파일을 찾을 수 없습니다: {file_path}')
    except PermissionError:
        print(f'[오류] 파일 읽기 권한이 없습니다: {file_path}')
    except UnicodeDecodeError:
        print(f'[오류] 파일 인코딩을 읽을 수 없습니다: {file_path}')
    except OSError as e:
        print(f'[오류] 파일 읽기 실패: {e}')

    return rows


def print_table(rows):
    """2차원 리스트를 TABLE처럼 정렬해서 출력한다."""
    if not rows:
        print('[안내] 출력할 데이터가 없습니다.')
        return

    col_widths = []
    for row in rows:
        for i, field in enumerate(row):
            if i >= len(col_widths):
                col_widths.append(0)
            if len(field) > col_widths[i]:
                col_widths[i] = len(field)

    separator = '+' + '+'.join('-' * (w + 2) for w in col_widths) + '+'
    print(separator)

    for i, row in enumerate(rows):
        line_out = '| ' + ' | '.join(
            field.ljust(col_widths[j]) for j, field in enumerate(row)
        ) + ' |'
        print(line_out)

        if i == 0:
            print(separator)

    print(separator)


def to_list(rows):
    """메모리의 2차원 리스트를 딕셔너리 리스트로 변환한다."""
    if not rows:
        return []

    headers = rows[0]
    items = []

    for row in rows[1:]:
        item = dict(zip(headers, row))
        try:
            item['Flammability'] = float(item['Flammability'])
        except ValueError:
            item['Flammability'] = 0.0
        items.append(item)

    return items


def sort_by_flammability(items):
    """딕셔너리 리스트를 인화성 지수 기준 내림차순으로 정렬해서 반환한다."""
    if not items:
        return []

    return sorted(items, key=lambda item: item['Flammability'], reverse=True)


def filter_dangerous(items, threshold):
    """인화성 지수가 기준값 이상인 항목만 필터링해서 반환한다."""
    if not items:
        return []

    return [item for item in items if item['Flammability'] >= threshold]


def items_to_rows(items):
    """딕셔너리 리스트를 2차원 리스트(헤더 포함)로 변환한다."""
    if not items:
        return []

    headers = list(items[0].keys())
    rows = [headers]
    for item in items:
        rows.append([str(v) for v in item.values()])

    return rows


def save_csv(items, file_path):
    """딕셔너리 리스트를 CSV 파일로 저장한다."""
    if not items:
        print('[안내] 저장할 데이터가 없습니다.')
        return

    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            headers = list(items[0].keys())
            f.write(','.join(headers) + '\n')

            for item in items:
                values = [str(v) for v in item.values()]
                f.write(','.join(values) + '\n')

        print(f'[완료] 저장 성공: {file_path}')

    except PermissionError:
        print(f'[오류] 파일 쓰기 권한이 없습니다: {file_path}')
    except OSError as e:
        print(f'[오류] 파일 저장 실패: {e}')


def verify_data(rows, items):
    """원본 CSV 데이터와 변환된 리스트가 일치하는지 검증한다."""
    print('\n=== 데이터 검증 ===')

    # 1. 행 수 비교 (헤더 제외)
    csv_count = len(rows) - 1
    list_count = len(items)
    count_ok = csv_count == list_count
    print(f'행 수 일치:     CSV {csv_count}개 / 리스트 {list_count}개 → {"OK" if count_ok else "불일치!"}')

    # 2. 헤더 비교
    csv_headers = rows[0]
    list_headers = list(items[0].keys()) if items else []
    header_ok = csv_headers == list_headers
    print(f'헤더 일치:      {csv_headers} → {"OK" if header_ok else "불일치!"}')

    # 3. 각 행 데이터 비교
    mismatch = 0
    for i, (row, item) in enumerate(zip(rows[1:], items)):
        for j, key in enumerate(csv_headers):
            csv_val = row[j]
            list_val = str(item[key])
            if csv_val != list_val:
                mismatch += 1
                print(f'  [불일치] {i+1}행 {key}: CSV="{csv_val}" / 리스트="{list_val}"')

    if mismatch == 0:
        print(f'값 일치:        전체 {csv_count}행 모두 일치 → OK')
    else:
        print(f'값 불일치:      {mismatch}개 항목 불일치!')


def print_menu():
    """메뉴를 출력한다."""
    title = '화성 기지 인화성 물질 분류 시스템'
    inner = f'| {title} |'
    border = '+' + '-' * (len(inner) - 2) + '+'

    print(border)
    print(inner)
    print(border)
    print('1. 파일 출력')
    print('2. 리스트 변환 후 출력')
    print('3. 인화성 높은 순으로 정렬')
    print('4. 인화성 0.7 이상 목록 출력')
    print('5. 인화성 0.7 이상 목록 CSV 저장')
    print('6. 데이터 검증')
    print('0. 종료')
    print('-' * len(inner))


def main():
    rows = read_csv(READ_FILE)
    items = to_list(rows)
    sorted_items = sort_by_flammability(items)
    danger_items = filter_dangerous(sorted_items, DANGER_THRESHOLD)

    while True:
        print_menu()
        choice = input('번호를 선택하세요: ').strip()

        if choice == '1':
            print('\n=== 1. 파일 원본 출력 ===')
            print_table(rows)

        elif choice == '2':
            print('\n=== 2. 리스트 변환 전후 비교 ===')
            print('\n[ 변환 전 — 2차원 리스트 (상위 3개) ]')
            print_table(rows[:4])
            print('\n[ 변환 후 — 딕셔너리 리스트 (상위 3개) ]')
            for item in items[:3]:
                print(item)

        elif choice == '3':
            print('\n=== 3. 인화성 높은 순 정렬 ===')
            print_table(items_to_rows(sorted_items))

        elif choice == '4':
            print(f'\n=== 4. 인화성 {DANGER_THRESHOLD} 이상 위험 물질 ===')
            print_table(items_to_rows(danger_items))

        elif choice == '5':
            print('\n=== 5. 위험 물질 CSV 저장 ===')
            save_csv(danger_items, WRITE_FILE)

        elif choice == '6':
            verify_data(rows, items)

        elif choice == '0':
            print('종료합니다.')
            break

        else:
            print('[안내] 0~6 사이 번호를 입력하세요.')

        input('\n계속하려면 Enter 를 누르세요...')


if __name__ == '__main__':
    main()