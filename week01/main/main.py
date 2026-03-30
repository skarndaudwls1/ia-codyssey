# main.py
# 화성 기지 미션 컴퓨터 로그 분석 시스템

LOG_FILE = 'mission_computer_main.log'
PROBLEM_FILE = 'mission_computer_error.log'
REPORT_FILE = 'log_analysis.md'

# 문제 로그 키워드
PROBLEM_KEYWORDS = ['unstable', 'explosion', 'error', 'fail', 'warning', 'critical']


def hello_mars():
    # 시스템 시작 메시지를 출력한다.
    print('Hello Mars')


def read_log(file_path):
    # 로그 파일을 한 번만 읽어서 라인 리스트로 반환한다.
    # 헤더(첫 줄)는 제외하고 데이터만 반환한다.
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
                lines.append(line)

    except FileNotFoundError:
        print(f'[오류] 파일을 찾을 수 없습니다: {file_path}')
    except PermissionError:
        print(f'[오류] 파일 읽기 권한이 없습니다: {file_path}')
    except UnicodeDecodeError:
        print(f'[오류] 파일 인코딩을 읽을 수 없습니다: {file_path}')
    except OSError as e:
        print(f'[오류] 파일 읽기 실패: {e}')

    return lines


def parse_line(line):
    # 로그 한 줄을 파싱해서 딕셔너리로 반환한다.
    # 형식: timestamp,event,message
    # message 안에 콤마가 있을 수 있으므로 maxsplit=2 사용
    parts = line.split(',', 2)
    if len(parts) == 3:
        return {
            'timestamp': parts[0].strip(),
            'event': parts[1].strip(),
            'message': parts[2].strip(),
        }
    return None


def print_log(lines):
    # 로그 전체 내용을 TABLE 형식으로 출력한다.
    print('\n=== 전체 로그 출력 ===')
    output_lines = []
    for line in lines:
        parsed = parse_line(line)
        if parsed:
            output_lines.append(
                f'[{parsed["timestamp"]}] [{parsed["event"]}] {parsed["message"]}'
            )
    print('\n'.join(output_lines))
    print(f'\n총 {len(lines)}개 로그')


def sort_by_time_desc(lines):
    # 로그를 시간 역순으로 정렬해서 반환한다. (보너스)
    # timestamp 앞 19글자 기준으로 정렬
    try:
        return sorted(lines, key=lambda x: x[:19], reverse=True)
    except Exception as e:
        print(f'[오류] 정렬 실패: {e}')
        return lines


def filter_problems(lines):
    # 문제가 되는 로그만 필터링해서 반환한다. (보너스)
    result = []
    for line in lines:
        parsed = parse_line(line)
        if parsed:
            msg_lower = parsed['message'].lower()
            event_lower = parsed['event'].lower()
            if any(kw in msg_lower or kw in event_lower for kw in PROBLEM_KEYWORDS):
                result.append(line)
    return result


def save_problems(lines, file_path):
    # 문제 로그를 별도 파일로 저장한다. (보너스)
    problems = filter_problems(lines)
    if not problems:
        print('[안내] 저장할 문제 로그가 없습니다.')
        return

    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('timestamp,event,message\n')
            for line in problems:
                f.write(line + '\n')
        print(f'[완료] 문제 로그 저장 성공: {file_path} ({len(problems)}개)')

    except PermissionError:
        print(f'[오류] 파일 쓰기 권한이 없습니다: {file_path}')
    except OSError as e:
        print(f'[오류] 파일 저장 실패: {e}')


def save_report(lines, file_path):
    # 로그 분석 보고서를 Markdown 형식으로 저장한다.
    problems = filter_problems(lines)

    # 사고 관련 로그 추출
    oxygen_logs = [l for l in lines if 'oxygen' in l.lower()]

    report = '# 화성 기지 사고 로그 분석 보고서\n\n'

    report += '## 1. 개요\n\n'
    report += f'- 분석 파일: `mission_computer_main.log`\n'
    report += f'- 전체 로그 수: {len(lines)}개\n'
    report += f'- 문제 로그 수: {len(problems)}개\n\n'

    report += '## 2. 전체 로그 요약\n\n'
    report += '| 시각 | 이벤트 | 내용 |\n'
    report += '|------|--------|------|\n'
    for line in lines:
        parsed = parse_line(line)
        if parsed:
            report += f'| {parsed["timestamp"]} | {parsed["event"]} | {parsed["message"]} |\n'

    report += '\n## 3. 사고 원인 분석\n\n'
    report += '로그 분석 결과, 사고는 다음과 같은 순서로 발생한 것으로 추정됩니다.\n\n'

    report += '### 사고 진행 순서\n\n'
    for line in oxygen_logs:
        parsed = parse_line(line)
        if parsed:
            report += f'- `{parsed["timestamp"]}` — {parsed["message"]}\n'

    report += '\n### 문제 로그 전체\n\n'
    for line in problems:
        parsed = parse_line(line)
        if parsed:
            report += f'- `{parsed["timestamp"]}` [{parsed["event"]}] {parsed["message"]}\n'

    report += '\n## 4. 결론\n\n'
    report += '11:35에 산소 탱크 불안정 신호가 감지되었으나 별도 대응 없이 '
    report += '11:40에 산소 탱크 폭발로 이어졌습니다.\n'
    report += '임무 완료(11:30) 이후 발생한 산소 탱크 이상이 '
    report += '사고의 직접적인 원인으로 판단됩니다.\n\n'
    report += '## 5. 권고 사항\n\n'
    report += '- 산소 탱크 압력 모니터링 주기 단축\n'
    report += '- 이상 감지 시 자동 경보 및 대피 프로토콜 수립\n'
    report += '- 임무 완료 후에도 시스템 안전 점검 절차 유지\n'

    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f'[완료] 보고서 저장 성공: {file_path}')

    except PermissionError:
        print(f'[오류] 파일 쓰기 권한이 없습니다: {file_path}')
    except OSError as e:
        print(f'[오류] 파일 저장 실패: {e}')


def print_menu():
    # 메뉴를 출력한다.
    print('\n============================')
    print(' 미션 컴퓨터 로그 분석 시스템')
    print('============================')
    print('1. 전체 로그 출력')
    print('2. 시간 역순 로그 출력 (보너스)')
    print('3. 문제 로그만 출력 (보너스)')
    print('4. 문제 로그 파일 저장 (보너스)')
    print('5. 분석 보고서 저장')
    print('0. 종료')
    print('----------------------------')


def main():
    hello_mars()

    # 시작 시 한 번만 읽기
    lines = read_log(LOG_FILE)
    if not lines:
        print('[오류] 로그 파일을 불러오지 못했습니다. 종료합니다.')
        return

    # 역순 정렬본도 미리 준비 (메모리에서 처리)
    sorted_lines = sort_by_time_desc(lines)

    while True:
        print_menu()
        choice = input('번호를 선택하세요: ').strip()

        if choice == '1':
            print_log(lines)

        elif choice == '2':
            print('\n=== 시간 역순 로그 출력 ===')
            print_log(sorted_lines)

        elif choice == '3':
            print('\n=== 문제 로그 출력 ===')
            problems = filter_problems(lines)
            if problems:
                print_log(problems)
            else:
                print('[안내] 문제 로그가 없습니다.')

        elif choice == '4':
            save_problems(lines, PROBLEM_FILE)

        elif choice == '5':
            save_report(lines, REPORT_FILE)

        elif choice == '0':
            print('종료합니다.')
            break

        else:
            print('[안내] 올바른 번호를 입력하세요.')

        input('\n계속하려면 Enter 를 누르세요...')


if __name__ == '__main__':
    main()