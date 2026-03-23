# Mars.py
# 화성 기지 인화성 물질 분류 시스템

READ_FILE = 'Mars_Base_Inventory_List.csv'
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

    # 리스트 컴프리헨션: 조건에 맞는 항목만 골라서 새 리스트 만들기
    # [결과 for 항목 in 리스트 if 조건]
    return [item for item in items if item['Flammability'] >= threshold]


def main():
    rows = read_csv(READ_FILE)                  # 1번: 파일 읽기
    print_table(rows)                           # 1번: 출력
    items = to_list(rows)                       # 2번: 리스트 변환
    sorted_items = sort_by_flammability(items)  # 3번: 정렬

    print('\n=== 인화성 높은 순 정렬 결과 ===')
    for item in sorted_items:
        print(f'{item["Substance"]:<25} {item["Flammability"]}')

    danger_items = filter_dangerous(sorted_items, DANGER_THRESHOLD)  # 4번: 필터링

    print(f'\n=== 인화성 {DANGER_THRESHOLD} 이상 위험 물질 ===')
    for item in danger_items:
        print(f'{item["Substance"]:<25} {item["Flammability"]}')


if __name__ == '__main__':
    main()