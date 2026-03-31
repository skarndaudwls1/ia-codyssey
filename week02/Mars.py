# Mars.py
# 화성 기지 인화성 물질 분류 시스템

READ_FILE = 'Mars_Base_Inventory_List.csv'
WRITE_FILE = 'Mars_Base_Inventory_danger.csv'
BIN_FILE = 'Mars_Base_Inventory_List.bin'
DANGER_THRESHOLD = 0.7


def read_csv(file_path):
    # CSV 파일을 한 번만 읽어서 2차원 리스트로 반환한다.
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
    # 2차원 리스트를 TABLE처럼 정렬해서 출력한다.
    # 출력 줄을 리스트에 모은 뒤 print() 한 번으로 출력한다.
    # print() 호출 횟수를 줄여 시스템 콜 최소화.
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

    # 출력할 줄을 리스트에 먼저 모두 조립
    output_lines = [separator]
    for i, row in enumerate(rows):
        line_out = '| ' + ' | '.join(
            field.ljust(col_widths[j]) for j, field in enumerate(row)
        ) + ' |'
        output_lines.append(line_out)
        if i == 0:
            output_lines.append(separator)
    output_lines.append(separator)

    # print() 한 번으로 전체 출력
    print('\n'.join(output_lines))


def to_list(rows):
    # 메모리의 2차원 리스트를 딕셔너리 리스트로 변환한다.
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
    # 딕셔너리 리스트를 인화성 지수 기준 내림차순으로 정렬해서 반환한다.
    if not items:
        return []

    return sorted(items, key=lambda item: item['Flammability'], reverse=True)


def filter_dangerous(items, threshold):
    # 인화성 지수가 기준값 이상인 항목만 필터링해서 반환한다.
    if not items:
        return []

    return [item for item in items if item['Flammability'] >= threshold]


def items_to_rows(items):
    # 딕셔너리 리스트를 2차원 리스트(헤더 포함)로 변환한다.
    if not items:
        return []

    headers = list(items[0].keys())
    rows = [headers]
    for item in items:
        rows.append([str(v) for v in item.values()])

    return rows


def save_csv(items, file_path):
    # 딕셔너리 리스트를 CSV 파일로 저장한다.
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


def save_bin(items, file_path):
    # 정렬된 딕셔너리 리스트를 진짜 이진 파일로 저장하고 검증한다.
    # import 없이 int.to_bytes(), float.hex() 만 사용.
    #
    # 저장 형식 (항목 하나):
    #   [항목 수: 4바이트] 파일 맨 앞에 총 항목 수 기록
    #   [필드 수: 4바이트] 항목 하나의 필드 수
    #   [키 길이: 4바이트][키 바이트] 키 문자열
    #   [값 타입: 1바이트] 0=문자열, 1=float
    #   [값 길이: 4바이트][값 바이트] 또는 [float 8바이트]
    if not items:
        print('[안내] 저장할 데이터가 없습니다.')
        return False

    try:
        buffer = bytearray()

        # 총 항목 수를 파일 맨 앞 4바이트에 기록
        buffer += len(items).to_bytes(4, byteorder='big')

        for item in items:
            # 필드 수 기록 (4바이트)
            buffer += len(item).to_bytes(4, byteorder='big')

            for key, val in item.items():
                # 키: 길이(4바이트) + UTF-8 바이트
                key_bytes = key.encode('utf-8')
                buffer += len(key_bytes).to_bytes(4, byteorder='big')
                buffer += key_bytes

                # 값 타입 판별 후 저장
                if isinstance(val, float):
                    # float: 타입(1바이트=0x01) + hex 문자열 바이트(8바이트 고정)
                    buffer += (1).to_bytes(1, byteorder='big')
                    # float.hex()로 정밀도 손실 없이 변환 후 8바이트로 저장
                    val_bytes = val.hex().encode('utf-8')
                    buffer += len(val_bytes).to_bytes(4, byteorder='big')
                    buffer += val_bytes
                else:
                    # 문자열: 타입(1바이트=0x00) + 길이(4바이트) + UTF-8 바이트
                    buffer += (0).to_bytes(1, byteorder='big')
                    val_bytes = str(val).encode('utf-8')
                    buffer += len(val_bytes).to_bytes(4, byteorder='big')
                    buffer += val_bytes

        # 'wb': write binary
        with open(file_path, 'wb') as f:
            f.write(buffer)

        # 저장 검증: 메모리의 buffer 크기로 바로 확인
        file_size = len(buffer)

        if file_size > 0:
            print(f'[완료] 이진 파일 저장 성공: {file_path}')
            print(f'[검증] 파일 크기: {file_size} bytes → 정상')
            return True
        else:
            print(f'[오류] 파일이 비어 있습니다: {file_path}')
            return False

    except PermissionError:
        print(f'[오류] 파일 쓰기 권한이 없습니다: {file_path}')
        return False
    except OSError as e:
        print(f'[오류] 파일 저장 실패: {e}')
        return False


def load_bin(file_path):
    # 이진 파일을 읽어서 딕셔너리 리스트로 반환한다.
    # import 없이 int.from_bytes(), float.fromhex() 만 사용.
    try:
        with open(file_path, 'rb') as f:
            buffer = f.read()

        pos = 0

        def read_bytes(n):
            # 현재 위치에서 n바이트 읽고 pos 이동
            nonlocal pos
            chunk = buffer[pos:pos + n]
            pos += n
            return chunk

        # 총 항목 수 읽기 (4바이트)
        item_count = int.from_bytes(read_bytes(4), byteorder='big')
        items = []

        for _ in range(item_count):
            # 필드 수 읽기 (4바이트)
            field_count = int.from_bytes(read_bytes(4), byteorder='big')
            item = {}

            for _ in range(field_count):
                # 키 읽기
                key_len = int.from_bytes(read_bytes(4), byteorder='big')
                key = read_bytes(key_len).decode('utf-8')

                # 값 타입 읽기 (1바이트)
                val_type = int.from_bytes(read_bytes(1), byteorder='big')
                val_len = int.from_bytes(read_bytes(4), byteorder='big')
                val_bytes = read_bytes(val_len)

                if val_type == 1:
                    # float 복원
                    item[key] = float.fromhex(val_bytes.decode('utf-8'))
                else:
                    # 문자열 복원
                    item[key] = val_bytes.decode('utf-8')

            items.append(item)

        print(f'[완료] 이진 파일 읽기 성공: {file_path} ({len(items)}개 항목)')
        return items

    except FileNotFoundError:
        print(f'[오류] 파일을 찾을 수 없습니다: {file_path}')
        print('[안내] 먼저 11번으로 이진 파일을 저장해주세요.')
    except PermissionError:
        print(f'[오류] 파일 읽기 권한이 없습니다: {file_path}')
    except OSError as e:
        print(f'[오류] 파일 읽기 실패: {e}')

    return []


def verify_data(rows, items):
    # 원본 CSV 데이터와 변환된 리스트가 일치하는지 검증한다.
    print('\n=== 데이터 검증 ===')

    csv_count = len(rows) - 1
    list_count = len(items)
    count_ok = csv_count == list_count
    print(f'행 수 일치:     CSV {csv_count}개 / 리스트 {list_count}개 → {"OK" if count_ok else "불일치!"}')

    csv_headers = rows[0]
    list_headers = list(items[0].keys()) if items else []
    header_ok = csv_headers == list_headers
    print(f'헤더 일치:      {csv_headers} → {"OK" if header_ok else "불일치!"}')

    mismatch = 0
    for i, (row, item) in enumerate(zip(rows[1:], items)):
        for j, key in enumerate(csv_headers):
            csv_val = row[j]
            list_val = item[key]
            try:
                if float(csv_val) != float(list_val):
                    mismatch += 1
                    print(f'  [불일치] {i+1}행 {key}: CSV="{csv_val}" / 리스트="{list_val}"')
            except ValueError:
                if csv_val != str(list_val):
                    mismatch += 1
                    print(f'  [불일치] {i+1}행 {key}: CSV="{csv_val}" / 리스트="{list_val}"')

    if mismatch == 0:
        print(f'값 일치:        전체 {csv_count}행 모두 일치 → OK')
    else:
        print(f'값 불일치:      {mismatch}개 항목 불일치!')


def print_menu():
    # 메뉴를 출력한다.
    title = '화성 기지 인화성 물질 분류'

    print('============================')
    print(f' {title}')
    print('============================')
    print('1.  파일 출력')
    print('2.  리스트 변환 후 출력')
    print('3.  인화성 높은 순으로 정렬')
    print('4.  인화성 0.7 이상 목록 출력')
    print('5.  인화성 0.7 이상 목록 CSV 저장')
    print('6.  데이터 검증')
    print()
    print('11. 정렬된 목록 이진 파일 저장')
    print('12. 이진 파일 읽어서 출력')
    print('0.  종료')
    print('----------------------------')


def main():
    # 시작 시 데이터를 한 번만 읽어서 메모리에 준비한다.
    rows = read_csv(READ_FILE)
    items = to_list(rows)
    sorted_items = sort_by_flammability(items)
    danger_items = filter_dangerous(sorted_items, DANGER_THRESHOLD)

    # 메뉴 선택마다 변환 반복을 막기 위해 한 번만 변환해서 메모리에 보관
    sorted_rows = items_to_rows(sorted_items)
    danger_rows = items_to_rows(danger_items)

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
            print_table(sorted_rows)

        elif choice == '4':
            print(f'\n=== 4. 인화성 {DANGER_THRESHOLD} 이상 위험 물질 ===')
            print_table(danger_rows)

        elif choice == '5':
            print('\n=== 5. 위험 물질 CSV 저장 ===')
            save_csv(danger_items, WRITE_FILE)

        elif choice == '6':
            verify_data(rows, items)

        elif choice == '11':
            print('\n=== 11. 정렬된 목록 이진 파일 저장 ===')
            save_bin(sorted_items, BIN_FILE)

        elif choice == '12':
            print('\n=== 12. 이진 파일 읽어서 출력 ===')
            bin_items = load_bin(BIN_FILE)
            if bin_items:
                print_table(items_to_rows(bin_items))

        elif choice == '0':
            print('종료합니다.')
            break

        else:
            print('[안내] 올바른 번호를 입력하세요.')

        input('\n계속하려면 Enter 를 누르세요...')


if __name__ == '__main__':
    main()