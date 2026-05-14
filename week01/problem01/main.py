# main.py
# 화성 기지 미션 컴퓨터 로그 분석 시스템

LOG_FILE = 'mission_computer_main.log'
JSON_FILE = 'mission_computer_main.json'


def read_log(file_path):
    # 로그 파일을 읽어서 2차원 리스트로 반환한다.
    # 형식: [[timestamp, event, message], ...]
    lines = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                line = line.strip()
                if not line:
                    continue
                # 첫 줄(헤더) 제외
                if i == 0:
                    continue
                # 콤마 기준으로 분리 (message 안 콤마 보호)
                parts = line.split(',', 2)
                if len(parts) == 3:
                    lines.append([
                        parts[0].strip(),
                        parts[1].strip(),
                        parts[2].strip(),
                    ])

    except FileNotFoundError:
        print(f'[오류] 파일을 찾을 수 없습니다: {file_path}')
    except PermissionError:
        print(f'[오류] 파일 읽기 권한이 없습니다: {file_path}')
    except UnicodeDecodeError:
        print(f'[오류] 파일 인코딩을 읽을 수 없습니다: {file_path}')
    except OSError as e:
        print(f'[오류] 파일 읽기 실패: {e}')

    return lines


def print_list(log_list):
    # 리스트 객체를 화면에 출력한다.
    print('\n=== 리스트 출력 ===')
    output_lines = []
    for item in log_list:
        output_lines.append(f'[{item[0]}] [{item[1]}] {item[2]}')
    print('\n'.join(output_lines))
    print(f'\n총 {len(log_list)}개 로그')


def sort_by_time_desc(log_list):
    # 리스트를 시간 역순으로 정렬해서 반환한다.
    # 원본 유지를 위해 sorted() 사용
    return sorted(log_list, key=lambda x: x[0], reverse=True)


def list_to_dict(log_list):
    # 리스트 객체를 딕셔너리 리스트로 변환한다.
    # [timestamp, event, message] → {'timestamp': ..., 'event': ..., 'message': ...}
    return [
        {
            'timestamp': item[0],
            'event': item[1],
            'message': item[2],
        }
        for item in log_list
    ]


def dict_to_json_str(dict_list):
    # 딕셔너리 리스트를 JSON 형식 문자열로 변환한다.
    # import json 없이 직접 구현.
    lines = []
    for item in dict_list:
        # 문자열 안 큰따옴표 이스케이프 처리
        timestamp = item['timestamp'].replace('"', '\\"')
        event = item['event'].replace('"', '\\"')
        message = item['message'].replace('"', '\\"')

        lines.append(
            '  {\n'
            f'    "timestamp": "{timestamp}",\n'
            f'    "event": "{event}",\n'
            f'    "message": "{message}"\n'
            '  }'
        )

    return '[\n' + ',\n'.join(lines) + '\n]'


def save_json(dict_list, file_path):
    # 딕셔너리 리스트를 JSON 파일로 저장한다.
    if not dict_list:
        print('[안내] 저장할 데이터가 없습니다.')
        return

    try:
        json_str = dict_to_json_str(dict_list)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(json_str)
        print(f'[완료] JSON 저장 성공: {file_path}')

    except PermissionError:
        print(f'[오류] 파일 쓰기 권한이 없습니다: {file_path}')
    except OSError as e:
        print(f'[오류] 파일 저장 실패: {e}')


def search_dict(dict_list, keyword):
    # 딕셔너리 리스트에서 특정 문자열이 포함된 항목을 출력한다. (보너스)
    result = [
        item for item in dict_list
        if keyword.lower() in item['message'].lower()
        or keyword.lower() in item['event'].lower()
    ]

    print(f'\n=== 검색 결과: "{keyword}" ({len(result)}개) ===')
    if result:
        output_lines = []
        for item in result:
            output_lines.append(
                f'[{item["timestamp"]}] [{item["event"]}] {item["message"]}'
            )
        print('\n'.join(output_lines))
    else:
        print('[안내] 검색 결과가 없습니다.')


def print_menu():
    # 메뉴를 출력한다.
    print('\n============================')
    print(' 미션 컴퓨터 로그 분석 시스템')
    print('============================')
    print('1. 전체 로그 리스트 출력')
    print('2. 시간 역순 정렬 출력')
    print('3. 딕셔너리 변환 후 출력')
    print('4. JSON 파일 저장')
    print('5. 키워드 검색 (보너스)')
    print('0. 종료')
    print('----------------------------')


def main():
    # 시작 시 한 번만 읽어서 메모리에 준비
    log_list = read_log(LOG_FILE)
    if not log_list:
        print('[오류] 로그 파일을 불러오지 못했습니다. 종료합니다.')
        return

    # 메모리에서 미리 가공 (파일 재접근 없음)
    sorted_list = sort_by_time_desc(log_list)
    dict_list = list_to_dict(sorted_list)

    while True:
        print_menu()
        choice = input('번호를 선택하세요: ').strip()

        if choice == '1':
            print_list(log_list)

        elif choice == '2':
            print('\n=== 시간 역순 정렬 ===')
            print_list(sorted_list)

        elif choice == '3':
            print('\n=== 딕셔너리 변환 결과 (상위 3개) ===')
            for item in dict_list[:3]:
                print(item)
            print(f'... 총 {len(dict_list)}개')

        elif choice == '4':
            save_json(dict_list, JSON_FILE)

        elif choice == '5':
            keyword = input('검색할 키워드를 입력하세요: ').strip()
            if keyword:
                search_dict(dict_list, keyword)
            else:
                print('[안내] 키워드를 입력해주세요.')

        elif choice == '0':
            print('종료합니다.')
            break

        else:
            print('[안내] 올바른 번호를 입력하세요.')

        input('\n계속하려면 Enter 를 누르세요...')


if __name__ == '__main__':
    main()