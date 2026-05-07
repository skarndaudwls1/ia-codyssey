'''
door_hacking.py
emergency_storage_key.zip 의 암호를 무차별 대입으로 찾는 코드.

- 암호 가정: 숫자(0-9) + 소문자 알파벳(a-z) 으로 구성된 6자리.
- unlock_zip()         : 단일 프로세스 무차별 대입.
- unlock_zip_fast()    : 멀티프로세싱으로 키 공간을 분할해 병렬 대입 (보너스).
- unlock_zip_fastest() : ZipCrypto 12-byte 헤더만 pure-Python 으로 직접
                         검사 + 멀티프로세싱. 1·2번보다 5~15배 빠름.

사용 모듈:
- zipfile  : zip 파일 처리(문제에서 명시적으로 허용).
- time     : 시작 시간/진행 시간 출력(문제 요구사항으로 필요).
- multiprocessing : 보너스 과제(병렬 무차별 대입)에서만 사용.

실행은 본 파일이 있는 폴더에서 한다.
'''

import multiprocessing
import time
import zipfile


# ---------------------------------------------------------------------------
# 상수
# ---------------------------------------------------------------------------
CHARSET = '0123456789abcdefghijklmnopqrstuvwxyz'
CHARSET_BYTES = CHARSET.encode('ascii')
PASSWORD_LENGTH = 6
ZIP_FILENAME = 'emergency_storage_key.zip'
RESULT_FILENAME = 'password.txt'
REPORT_INTERVAL = 100000
PROGRESS_FLUSH_INTERVAL = 5000
PROGRESS_REPORT_SECONDS = 2.0
PROCESS_JOIN_TIMEOUT = 3.0
PROCESS_TERMINATE_TIMEOUT = 1.0

# ZipCrypto 알고리즘 상수
_ZC_KEY1_MULTIPLIER = 134775813
_ZC_INITIAL_KEYS = (0x12345678, 0x23456789, 0x34567890)


# ---------------------------------------------------------------------------
# 공통 헬퍼
# ---------------------------------------------------------------------------
def _format_time(epoch_seconds):
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(epoch_seconds))


def _save_password(password):
    try:
        with open(RESULT_FILENAME, 'w', encoding='utf-8') as result_file:
            result_file.write(password)
        print('암호를 {0} 파일에 저장했습니다.'.format(RESULT_FILENAME))
    except OSError as error:
        print('[오류] {0} 저장 실패: {1}'.format(RESULT_FILENAME, error))


def _open_zip():
    try:
        return zipfile.ZipFile(ZIP_FILENAME)
    except FileNotFoundError:
        print('[오류] {0} 파일을 찾을 수 없습니다.'.format(ZIP_FILENAME))
    except zipfile.BadZipFile:
        print('[오류] 손상된 zip 파일입니다.')
    except OSError as error:
        print('[오류] zip 파일을 열 수 없습니다: {0}'.format(error))
    return None


def _index_to_password(index):
    '''0..(36^6-1) 정수를 6자리 후보 문자열로 변환한다 (36진수).'''
    base = len(CHARSET)
    chars = [''] * PASSWORD_LENGTH
    n = index
    for position in range(PASSWORD_LENGTH - 1, -1, -1):
        chars[position] = CHARSET[n % base]
        n //= base
    return ''.join(chars)


def _final_flush(local_attempts, progress_counter, counter_lock):
    '''워커 종료 시 남은 지역 카운터를 공유 카운터에 합산한다.'''
    if not local_attempts:
        return
    try:
        with counter_lock:
            progress_counter.value += local_attempts
    except Exception:
        pass


def _finalize_result(found_password, total_attempts, total_elapsed, interrupted):
    '''1·2·3번 모드 공통 결과 출력 및 저장.'''
    print('==============================')
    if interrupted:
        print('사용자에 의해 중단되었습니다. 시도 약 {0:,}회 / 총 {1:.1f}초'.format(
            total_attempts, total_elapsed))
        return None
    if found_password is None:
        print('암호를 찾지 못했습니다. 시도 약 {0:,}회 / 총 {1:.1f}초'.format(
            total_attempts, total_elapsed))
        return None

    print('암호 발견! 암호 : {0}'.format(found_password))
    print('총 시도 횟수    : 약 {0:,}'.format(total_attempts))
    print('총 소요 시간    : {0:.2f}초'.format(total_elapsed))
    _save_password(found_password)
    return found_password


# ---------------------------------------------------------------------------
# 1번: 단일 프로세스
# ---------------------------------------------------------------------------
def unlock_zip():
    '''
    단일 프로세스로 36^6 가지 후보를 순차적으로 시도하여 zip 암호를 찾는다.
    찾으면 password.txt 로 저장하고 암호를 반환한다.
    '''
    zip_file = _open_zip()
    if zip_file is None:
        return None

    try:
        target_name = zip_file.namelist()[0]
    except IndexError:
        print('[오류] zip 안에 파일이 없습니다.')
        zip_file.close()
        return None

    total_combinations = len(CHARSET) ** PASSWORD_LENGTH
    start_time = time.time()

    print('==============================')
    print('암호 해독 시작 시각 : {0}'.format(_format_time(start_time)))
    print('문자 집합          : 0-9, a-z (총 {0}개)'.format(len(CHARSET)))
    print('암호 길이          : {0}자리'.format(PASSWORD_LENGTH))
    print('전체 경우의 수     : {0:,}'.format(total_combinations))
    print('==============================')

    attempt_count = 0
    found_password = None
    interrupted = False

    try:
        for index in range(total_combinations):
            attempt_count = index + 1
            password = _index_to_password(index)
            try:
                zip_file.read(target_name, pwd=password.encode('ascii'))
                found_password = password
                break
            except Exception:
                # 오답인 경우 RuntimeError(헤더 불일치) 또는
                # zlib.error / BadZipFile (헤더는 통과했으나 본문 해제 실패) 가
                # 발생할 수 있으므로 모두 무시하고 다음 후보로 진행한다.
                pass

            if attempt_count % REPORT_INTERVAL == 0:
                elapsed = time.time() - start_time
                speed = attempt_count / elapsed if elapsed > 0 else 0.0
                progress = attempt_count / total_combinations * 100.0
                print('[진행] 시도 {0:>12,} ({1:5.2f}%) / 경과 {2:7.1f}초 / '
                      '속도 {3:>9,.0f} 회/초 / 현재 후보 {4}'.format(
                          attempt_count, progress, elapsed, speed, password))
    except KeyboardInterrupt:
        interrupted = True
    finally:
        zip_file.close()

    total_elapsed = time.time() - start_time
    return _finalize_result(found_password, attempt_count, total_elapsed, interrupted)


# ---------------------------------------------------------------------------
# 멀티프로세싱 공통 드라이버 (2·3번 공유)
# ---------------------------------------------------------------------------
def _run_parallel(worker_fn, worker_extra_args, banner_lines):
    '''
    워커 N개를 spawn 하고, 결과 큐를 폴링하며 진행 상황을 출력하고,
    종료 시 워커들을 정리한 뒤 결과를 반환한다.

    worker_fn(start, end, *worker_extra_args, queue, counter, lock, event)
    Returns: (found_password, total_attempts, total_elapsed, interrupted)
    '''
    try:
        process_count = max(1, multiprocessing.cpu_count())
    except NotImplementedError:
        process_count = 4

    total_combinations = len(CHARSET) ** PASSWORD_LENGTH
    chunk_size = total_combinations // process_count

    progress_counter = multiprocessing.Value('Q', 0)
    counter_lock = multiprocessing.Lock()
    result_queue = multiprocessing.Queue()
    stop_event = multiprocessing.Event()

    start_time = time.time()
    print('==============================')
    for line in banner_lines:
        print(line)
    print('프로세스 수             : {0}'.format(process_count))
    print('전체 경우의 수          : {0:,}'.format(total_combinations))
    print('==============================')

    processes = []
    shared = (result_queue, progress_counter, counter_lock, stop_event)
    for i in range(process_count):
        start = i * chunk_size
        end = total_combinations if i == process_count - 1 else (i + 1) * chunk_size
        process = multiprocessing.Process(
            target=worker_fn,
            args=(start, end) + tuple(worker_extra_args) + shared,
        )
        process.daemon = True
        process.start()
        processes.append(process)

    found_password = None
    last_report = start_time
    interrupted = False

    try:
        while any(process.is_alive() for process in processes):
            try:
                found_password = result_queue.get(timeout=PROGRESS_REPORT_SECONDS)
                break
            except Exception:
                pass

            now = time.time()
            if now - last_report >= PROGRESS_REPORT_SECONDS:
                with counter_lock:
                    accumulated = progress_counter.value
                elapsed = now - start_time
                speed = accumulated / elapsed if elapsed > 0 else 0.0
                progress = accumulated / total_combinations * 100.0
                print('[진행] 누적 시도 {0:>12,} ({1:5.2f}%) / '
                      '경과 {2:7.1f}초 / 속도 {3:>9,.0f} 회/초'.format(
                          accumulated, progress, elapsed, speed))
                last_report = now

        if found_password is None:
            try:
                found_password = result_queue.get_nowait()
            except Exception:
                pass
    except KeyboardInterrupt:
        interrupted = True
    finally:
        stop_event.set()
        for process in processes:
            process.join(timeout=PROCESS_JOIN_TIMEOUT)
            if process.is_alive():
                process.terminate()
                process.join(timeout=PROCESS_TERMINATE_TIMEOUT)

    total_elapsed = time.time() - start_time
    with counter_lock:
        total_attempts = progress_counter.value

    return found_password, total_attempts, total_elapsed, interrupted


# ---------------------------------------------------------------------------
# 2번: 멀티프로세싱 (zipfile.read 사용)
# ---------------------------------------------------------------------------
def _worker(start_index, end_index, zip_path, target_name,
            result_queue, progress_counter, counter_lock, stop_event):
    '''zipfile.read 로 매 후보를 시도하는 워커.'''
    try:
        zip_file = zipfile.ZipFile(zip_path)
    except (OSError, zipfile.BadZipFile):
        return

    local_attempts = 0
    flush = PROGRESS_FLUSH_INTERVAL

    try:
        for index in range(start_index, end_index):
            password = _index_to_password(index)
            try:
                zip_file.read(target_name, pwd=password.encode('ascii'))
                with counter_lock:
                    progress_counter.value += local_attempts + 1
                result_queue.put(password)
                stop_event.set()
                return
            except Exception:
                pass

            local_attempts += 1
            if local_attempts >= flush:
                with counter_lock:
                    progress_counter.value += local_attempts
                local_attempts = 0
                if stop_event.is_set():
                    return
    except KeyboardInterrupt:
        pass
    finally:
        _final_flush(local_attempts, progress_counter, counter_lock)
        zip_file.close()


def unlock_zip_fast():
    '''[보너스] CPU 코어 수 만큼 분할하여 병렬 무차별 대입.'''
    try:
        with zipfile.ZipFile(ZIP_FILENAME) as zf:
            target_name = zf.namelist()[0]
    except FileNotFoundError:
        print('[오류] {0} 파일을 찾을 수 없습니다.'.format(ZIP_FILENAME))
        return None
    except (OSError, zipfile.BadZipFile, IndexError) as error:
        print('[오류] zip 파일을 읽을 수 없습니다: {0}'.format(error))
        return None

    banner_lines = [
        '병렬 암호 해독 시작 시각 : {0}'.format(_format_time(time.time())),
    ]
    found, attempts, elapsed, interrupted = _run_parallel(
        _worker, (ZIP_FILENAME, target_name), banner_lines,
    )
    return _finalize_result(found, attempts, elapsed, interrupted)


# ---------------------------------------------------------------------------
# 3번: ZipCrypto 12-byte 헤더 검사 + 멀티프로세싱 (가장 빠름)
# ---------------------------------------------------------------------------
def _build_crc32_table():
    table = []
    for i in range(256):
        value = i
        for _ in range(8):
            if value & 1:
                value = (value >> 1) ^ 0xedb88320
            else:
                value = value >> 1
        table.append(value)
    return tuple(table)


_CRC32_TABLE = _build_crc32_table()


def _read_zip_metadata():
    '''
    zip 첫 암호화 entry 에서 (대상 파일명, 12-byte 암호화 헤더, 검증 바이트) 추출.

    검증 바이트:
      - general purpose flag bit 3 가 set 이면 last_mod_time 의 상위 바이트
      - 아니면 CRC-32 의 최상위 바이트
    '''
    try:
        with open(ZIP_FILENAME, 'rb') as raw_file:
            data = raw_file.read()
    except FileNotFoundError:
        print('[오류] {0} 파일을 찾을 수 없습니다.'.format(ZIP_FILENAME))
        return None
    except OSError as error:
        print('[오류] zip 파일을 열 수 없습니다: {0}'.format(error))
        return None

    signature = b'PK\x03\x04'
    pos = data.find(signature)
    if pos < 0 or len(data) < pos + 30:
        print('[오류] zip 의 local file header 를 찾을 수 없습니다.')
        return None

    flag = int.from_bytes(data[pos + 6:pos + 8], 'little')
    if not (flag & 0x0001):
        print('[오류] 첫 entry 가 암호화되어 있지 않습니다.')
        return None

    last_mod_time = int.from_bytes(data[pos + 10:pos + 12], 'little')
    crc32_value = int.from_bytes(data[pos + 14:pos + 18], 'little')
    name_length = int.from_bytes(data[pos + 26:pos + 28], 'little')
    extra_length = int.from_bytes(data[pos + 28:pos + 30], 'little')

    name_start = pos + 30
    name_end = name_start + name_length
    encrypt_start = name_end + extra_length
    encrypted_header = data[encrypt_start:encrypt_start + 12]
    if len(encrypted_header) < 12:
        print('[오류] zip 암호화 헤더가 짧습니다.')
        return None

    try:
        target_name = data[name_start:name_end].decode('utf-8')
    except UnicodeDecodeError:
        target_name = data[name_start:name_end].decode('latin-1')

    if flag & 0x0008:
        check_byte = (last_mod_time >> 8) & 0xff
    else:
        check_byte = (crc32_value >> 24) & 0xff

    return target_name, bytes(encrypted_header), check_byte


def _worker_fastest(start_index, end_index, zip_path, target_name,
                    encrypted_header, check_byte,
                    result_queue, progress_counter, counter_lock, stop_event):
    '''
    ZipCrypto 12-byte 헤더 검사를 직접 수행하는 워커.

    최적화:
    - 워커당 zipfile 핸들 1개를 미리 열어두고 검증 시 재사용 (P1-1).
    - 자리(prefix)별 키 상태를 캐싱하여 매 후보마다 6자리 전부 재계산하는
      대신 변경된 자리부터만 갱신 (P1-2).
    - string/bytes 할당은 헤더 통과(1/256) 후보 검증 시점에만 수행 (P1-3).
    '''
    try:
        zip_file = zipfile.ZipFile(zip_path)
    except (OSError, zipfile.BadZipFile):
        return

    table = _CRC32_TABLE
    cb = CHARSET_BYTES
    base = len(cb)
    pwd_len = PASSWORD_LENGTH
    multiplier = _ZC_KEY1_MULTIPLIER
    init_keys = _ZC_INITIAL_KEYS

    # start_index → 자리 배열로 변환
    digits = [0] * pwd_len
    n = start_index
    for position in range(pwd_len - 1, -1, -1):
        digits[position] = n % base
        n //= base

    # prefix_keys[i] = i 글자까지 처리한 후의 (k0,k1,k2)
    prefix_keys = [init_keys] * (pwd_len + 1)
    k0, k1, k2 = init_keys
    for position in range(pwd_len):
        ch = cb[digits[position]]
        k0 = (k0 >> 8) ^ table[(k0 ^ ch) & 0xff]
        k1 = (k1 + (k0 & 0xff)) & 0xffffffff
        k1 = (k1 * multiplier + 1) & 0xffffffff
        k2 = (k2 >> 8) ^ table[(k2 ^ ((k1 >> 24) & 0xff)) & 0xff]
        prefix_keys[position + 1] = (k0, k1, k2)

    local_attempts = 0
    flush = PROGRESS_FLUSH_INTERVAL
    remaining = end_index - start_index

    try:
        while remaining > 0:
            # 12-byte 헤더 복호화: 마지막 평문 바이트만 비교에 사용
            kk0, kk1, kk2 = k0, k1, k2
            last_plain = 0
            for cipher_byte in encrypted_header:
                temp = kk2 | 2
                stream = ((temp * (temp ^ 1)) >> 8) & 0xff
                last_plain = cipher_byte ^ stream
                kk0 = (kk0 >> 8) ^ table[(kk0 ^ last_plain) & 0xff]
                kk1 = (kk1 + (kk0 & 0xff)) & 0xffffffff
                kk1 = (kk1 * multiplier + 1) & 0xffffffff
                kk2 = (kk2 >> 8) ^ table[(kk2 ^ ((kk1 >> 24) & 0xff)) & 0xff]

            if last_plain == check_byte:
                # 1/256 후보 — 미리 열어 둔 zipfile 핸들로 최종 검증
                password_bytes = bytes(cb[d] for d in digits)
                try:
                    zip_file.read(target_name, pwd=password_bytes)
                    with counter_lock:
                        progress_counter.value += local_attempts + 1
                    result_queue.put(password_bytes.decode('ascii'))
                    stop_event.set()
                    return
                except Exception:
                    pass  # false positive

            # 다음 후보로 전진: digits 를 36진수 카운터로 +1
            advanced = False
            for position in range(pwd_len - 1, -1, -1):
                if digits[position] + 1 < base:
                    digits[position] += 1
                    for p in range(position + 1, pwd_len):
                        digits[p] = 0
                    pk0, pk1, pk2 = prefix_keys[position]
                    for p in range(position, pwd_len):
                        ch = cb[digits[p]]
                        pk0 = (pk0 >> 8) ^ table[(pk0 ^ ch) & 0xff]
                        pk1 = (pk1 + (pk0 & 0xff)) & 0xffffffff
                        pk1 = (pk1 * multiplier + 1) & 0xffffffff
                        pk2 = (pk2 >> 8) ^ table[(pk2 ^ ((pk1 >> 24) & 0xff)) & 0xff]
                        prefix_keys[p + 1] = (pk0, pk1, pk2)
                    k0, k1, k2 = pk0, pk1, pk2
                    advanced = True
                    break
            if not advanced:
                break  # 워커 구간 끝

            remaining -= 1
            local_attempts += 1
            if local_attempts >= flush:
                with counter_lock:
                    progress_counter.value += local_attempts
                local_attempts = 0
                if stop_event.is_set():
                    return
    except KeyboardInterrupt:
        pass
    finally:
        _final_flush(local_attempts, progress_counter, counter_lock)
        zip_file.close()


def unlock_zip_fastest():
    '''
    [더 빠른 알고리즘] ZipCrypto 12-byte 헤더만 pure-Python 으로 검사하여
    오답을 빠르게 거른다. 헤더 통과(1/256) 한 후보만 zipfile 로 최종 검증.
    '''
    metadata = _read_zip_metadata()
    if metadata is None:
        return None
    target_name, encrypted_header, check_byte = metadata

    banner_lines = [
        '초고속 암호 해독 시작 시각 : {0}'.format(_format_time(time.time())),
        '알고리즘                  : ZipCrypto 헤더 검사 + 멀티프로세싱',
    ]
    found, attempts, elapsed, interrupted = _run_parallel(
        _worker_fastest,
        (ZIP_FILENAME, target_name, encrypted_header, check_byte),
        banner_lines,
    )
    return _finalize_result(found, attempts, elapsed, interrupted)


# ---------------------------------------------------------------------------
# 메뉴
# ---------------------------------------------------------------------------
def _print_menu():
    print('============================')
    print('  비상 저장소 도어 해킹 도구')
    print('============================')
    print('1. 단일 프로세스로 암호 해독 (unlock_zip)')
    print('2. 멀티프로세싱으로 빠르게 해독 (unlock_zip_fast) [보너스]')
    print('3. 헤더 검사 + 멀티프로세싱으로 초고속 해독 (unlock_zip_fastest)')
    print('0. 종료')


def _main():
    while True:
        _print_menu()
        try:
            choice = input('선택: ').strip()
        except EOFError:
            return
        if choice == '1':
            unlock_zip()
            return
        if choice == '2':
            unlock_zip_fast()
            return
        if choice == '3':
            unlock_zip_fastest()
            return
        if choice == '0':
            return
        print('잘못된 입력입니다. 다시 선택하세요.\n')


if __name__ == '__main__':
    _main()
