'''
caesar_cipher.py
emergency_storage_key.zip 에서 얻은 password.txt 의 문자열을
카이사르 암호로 가정하고 1~25 자리수만큼 시프트하여 복호화한다.

- password.txt 를 읽어 target_text 로 사용한다.
- caesar_cipher_decode(target_text) 가 1~25 자리수에 대해 결과를 출력한다.
  알파벳은 26 글자이지만 자리수 26 은 원문과 동일한 결과(=자리수 0) 라
  의미가 없어 제외한다. 따라서 실제로 의미 있는 자리수는 25개.
- 보너스: 내장 사전과 일치하는 단어가 보이면 그 자리수에서 일시 정지하고
  하나의 통합 프롬프트로 사용자의 다음 행동을 묻는다.
- 사용자가 선택한 자리수를 result.txt 로 저장한다.

실행은 본 파일이 있는 폴더에서 한다.
'''


# ---------------------------------------------------------------------------
# 상수
# ---------------------------------------------------------------------------
PASSWORD_FILENAME = 'password.txt'
RESULT_FILENAME = 'result.txt'
ALPHABET_SIZE = 26
# 시프트 0 과 26 은 모두 원문과 동일하므로 의미 있는 자리수는 1~25 (25개).
MAX_SHIFT = ALPHABET_SIZE - 1
# 자리수 사이 시각적 지연용 바쁜 대기 반복 횟수.
# 표준 라이브러리 사용이 금지되어 time.sleep 대신 빈 루프로 시간을 끈다.
SHIFT_DELAY_LOOPS = 3000000

LINE_WIDTH = 60
HEADING_BORDER = '=' * LINE_WIDTH
SECTION_BORDER = '-' * LINE_WIDTH

# 통합 프롬프트 반환 값 식별자.
ACTION_CANCEL = 'cancel'
ACTION_CONTINUE = 'continue'

# 보너스 과제용 단어 사전. 우주/기지 도메인을 우선으로 한다.
DICTIONARY = (
    'mars', 'earth', 'moon', 'venus', 'mercury', 'jupiter', 'saturn',
    'uranus', 'neptune', 'pluto', 'sun', 'star', 'planet', 'space',
    'rocket', 'orbit', 'base', 'station', 'door', 'gate', 'open', 'lock',
    'key', 'code', 'password', 'secret', 'emergency', 'storage', 'hello',
    'world', 'system', 'computer', 'mission', 'launch', 'control',
)


# ---------------------------------------------------------------------------
# 출력 헬퍼
# ---------------------------------------------------------------------------
def _print_heading(title):
    print(HEADING_BORDER)
    print('  ' + title)
    print(HEADING_BORDER)


def _print_section(title):
    print()
    print(SECTION_BORDER)
    print('  ' + title)
    print(SECTION_BORDER)


def _print_warn(message):
    print('  ! ' + message)


def _print_error(message):
    print('[오류] ' + message)


# ---------------------------------------------------------------------------
# 카이사르 시프트
# ---------------------------------------------------------------------------
def _shift_char(character, shift):
    '''알파벳 한 글자를 자리수만큼 뒤로(복호화 방향) 시프트한다.

    숫자/공백/특수문자는 그대로 둔다. 대/소문자는 모두 유지한다.
    '''
    if 'a' <= character <= 'z':
        base = ord('a')
        return chr((ord(character) - base - shift) % ALPHABET_SIZE + base)
    if 'A' <= character <= 'Z':
        base = ord('A')
        return chr((ord(character) - base - shift) % ALPHABET_SIZE + base)
    return character


def _shift_text(target_text, shift):
    result_chars = []
    for character in target_text:
        result_chars.append(_shift_char(character, shift))
    return ''.join(result_chars)


def _contains_dictionary_word(decoded_text):
    '''복호화 결과에 사전 단어가 포함되어 있으면 해당 단어를 반환, 없으면 None.'''
    lowered = decoded_text.lower()
    for word in DICTIONARY:
        if word in lowered:
            return word
    return None


def _visual_delay():
    '''표준 라이브러리 사용 없이 자리수 사이 시각적 지연을 만든다.'''
    counter = 0
    for _ in range(SHIFT_DELAY_LOOPS):
        counter += 1
    return counter


def _is_canonical_nonnegative_int(text):
    '''양의 정수 표현이 표준 형식(앞자리 0 없음) 인지 검사한다.

    예: '1' → True, '12' → True, '01' → False, '+5' → False.
    '''
    if not text.isdigit():
        return False
    if len(text) > 1 and text[0] == '0':
        return False
    return True


# ---------------------------------------------------------------------------
# 통합 행동 프롬프트
# ---------------------------------------------------------------------------
def _ask_action(suggested_shift, max_shift, can_continue):
    '''사용자의 다음 행동을 하나의 프롬프트로 묻는다.

    옵션:
      y           : 더 보기 (can_continue=True 일 때만 노출/허용)
      엔터        : 추천 자리수(suggested_shift) 의 결과를 저장
                    (suggested_shift 가 None 이면 빈 입력 → 재질문)
      숫자(1..N)  : 그 자리수의 결과를 저장
      q           : 저장하지 않고 종료

    반환값:
      - ACTION_CANCEL    : 저장 없이 종료 (q / EOF / Ctrl+C)
      - ACTION_CONTINUE  : 더 보기
      - 양의 정수 (자리수): 그 자리수의 결과를 저장
    '''
    range_text = '1 ~ {0}'.format(max_shift)

    print()
    if can_continue:
        print('  ? 어떻게 하시겠어요?')
        print('      y            : {0}번 자리수까지 더 보기'.format(MAX_SHIFT))
    else:
        print('  ? 어떻게 저장하시겠어요?')

    if suggested_shift is not None:
        print('      엔터         : 추천 자리수({0}) 의 결과를 저장'.format(
            suggested_shift))
    print('      숫자({0}) : 그 자리수의 결과를 저장'.format(range_text))
    print('      q            : 저장하지 않고 종료')

    while True:
        try:
            choice = input('  > ').strip().lower()
        except EOFError:
            return ACTION_CANCEL
        except KeyboardInterrupt:
            print()
            print('  사용자가 중단(Ctrl+C)했습니다.')
            return ACTION_CANCEL

        if choice == 'q':
            return ACTION_CANCEL
        if choice == '':
            if suggested_shift is not None:
                return suggested_shift
            _print_warn('자리수 숫자를 입력하거나, 저장하지 않으려면 q 를 입력하세요.')
            continue
        if choice in ('y', 'yes'):
            if can_continue:
                return ACTION_CONTINUE
            _print_warn('이미 모든 자리수를 보여드렸습니다. '
                        '저장할 숫자를 입력하거나 q 로 종료해 주세요.')
            continue
        if not _is_canonical_nonnegative_int(choice):
            _print_warn('숫자로 입력해 주세요. (예: 5, 19)  '
                        '앞자리 0 (예: 01) 은 사용할 수 없습니다.')
            continue

        shift = int(choice)
        if shift < 1 or shift > max_shift:
            _print_warn('{0} 안에서 골라 주세요. '
                        '아직 화면에 표시되지 않은 자리수는 선택할 수 없습니다.'.format(
                            range_text))
            continue
        return shift


# ---------------------------------------------------------------------------
# 핵심 함수
# ---------------------------------------------------------------------------
def caesar_cipher_decode(target_text):
    '''1~25 자리수만큼 한 단계씩 자동으로 시프트하며 결과를 출력한다.

    사전 단어가 발견된 자리수에서 일시 정지하고, 하나의 통합 프롬프트로
    다음 행동을 묻는다 (y / 엔터 / 숫자 / q).

    반환값:
      - 저장할 자리수(int): 사용자가 선택한 자리수
      - None              : 사용자가 저장 없이 종료
    '''
    _print_section('자리수별 복호화 결과 (사전 매칭 시 일시 정지)')

    suggested_shift = None
    last_shown_shift = 0
    shift = 1

    try:
        while shift <= MAX_SHIFT:
            decoded = _shift_text(target_text, shift)
            matched_word = None
            if suggested_shift is None:
                matched_word = _contains_dictionary_word(decoded)

            if matched_word is not None:
                print('  [{0:>2}]  {1}'.format(shift, decoded))
                print("         << 사전 단어 '{0}' 발견".format(matched_word))
                last_shown_shift = shift
                suggested_shift = shift

                action = _ask_action(suggested_shift, last_shown_shift,
                                     can_continue=True)
                if action == ACTION_CANCEL:
                    return None
                if action == ACTION_CONTINUE:
                    shift += 1
                    continue
                return action

            print('  [{0:>2}]  {1}'.format(shift, decoded))
            last_shown_shift = shift
            if shift < MAX_SHIFT:
                _visual_delay()
            shift += 1
    except KeyboardInterrupt:
        print()
        print('  사용자가 중단(Ctrl+C)했습니다.')
        return None

    # 모든 자리수 출력 완료. 저장 행동만 묻는다 (더 보기 옵션 없음).
    if suggested_shift is None:
        print()
        print('  사전 단어를 찾지 못했습니다. 직접 자리수를 골라 주세요.')

    action = _ask_action(suggested_shift, last_shown_shift, can_continue=False)
    if action == ACTION_CANCEL:
        return None
    return action


# ---------------------------------------------------------------------------
# 파일 입출력
# ---------------------------------------------------------------------------
def _read_password():
    try:
        with open(PASSWORD_FILENAME, 'r', encoding='utf-8') as password_file:
            return password_file.read().strip()
    except FileNotFoundError:
        _print_error('{0} 파일을 찾을 수 없습니다.'.format(PASSWORD_FILENAME))
    except OSError as error:
        _print_error('{0} 파일을 열 수 없습니다: {1}'.format(
            PASSWORD_FILENAME, error))
    except UnicodeDecodeError as error:
        _print_error('{0} 인코딩 오류: {1}'.format(PASSWORD_FILENAME, error))
    return None


def _save_result(decoded_text):
    try:
        with open(RESULT_FILENAME, 'w', encoding='utf-8') as result_file:
            result_file.write(decoded_text)
        return True
    except OSError as error:
        _print_error('{0} 저장 실패: {1}'.format(RESULT_FILENAME, error))
        return False


# ---------------------------------------------------------------------------
# 진입점
# ---------------------------------------------------------------------------
def _main():
    _print_heading('카이사르 암호 해독기')

    target_text = _read_password()
    if target_text is None:
        return
    if target_text == '':
        _print_error('{0} 파일이 비어 있습니다.'.format(PASSWORD_FILENAME))
        return

    print('  입력 파일   : {0}'.format(PASSWORD_FILENAME))
    print('  대상 문자열 : {0}'.format(target_text))

    shift = caesar_cipher_decode(target_text)
    if shift is None:
        print()
        print('  저장하지 않고 종료합니다.')
        return

    decoded = _shift_text(target_text, shift)
    saved = _save_result(decoded)

    print()
    _print_heading('해독 완료')
    print('  선택한 자리수 : {0}'.format(shift))
    print('  해독 결과     : {0}'.format(decoded))
    if saved:
        print('  저장 파일     : {0}'.format(RESULT_FILENAME))
    print(HEADING_BORDER)


if __name__ == '__main__':
    try:
        _main()
    except KeyboardInterrupt:
        print()
        print('  사용자가 중단(Ctrl+C)했습니다.')
