'''
javis.py
시스템 마이크를 인식하고 음성을 녹음하는 도구.

- 한국어 번호 메뉴 CLI 로 동작한다.
- 녹음 부분에 한해 외부 라이브러리(sounddevice / pyaudio) 사용이 허용된다.
  두 라이브러리 중 사용 가능한 것을 자동으로 감지해서 쓰며, 둘 다 없으면
  녹음 기능만 비활성화하고 나머지 기능은 그대로 동작한다.
- 녹음 파일은 본 스크립트와 같은 위치의 records 폴더에 저장한다.
- 파일 이름은 녹음 시각을 참조해 '년월일-시간분초' 형식으로 만든다.
  예) 20260516-143012.wav
- 보너스: 특정 날짜 범위의 녹음 파일만 골라서 보여준다.

실행은 본 파일이 있는 폴더에서 한다.
'''

import os
import wave
import datetime
import threading

# ---------------------------------------------------------------------------
# 선택적 외부 라이브러리 (녹음 부분에 한해 허용)
# ---------------------------------------------------------------------------
# 라이브러리나 오디오 시스템이 없을 때 import 단계에서 예외가 날 수 있으므로
# 모두 감싸서 처리한다. 실패하면 해당 백엔드는 사용 불가로 둔다.
try:
    import sounddevice as _sd
except (ImportError, OSError):
    _sd = None

try:
    import pyaudio as _pyaudio
except (ImportError, OSError):
    _pyaudio = None

try:
    import numpy as _np
except ImportError:
    _np = None


# ---------------------------------------------------------------------------
# 상수
# ---------------------------------------------------------------------------
APP_DIR = os.path.dirname(os.path.abspath(__file__))
RECORDS_DIRNAME = 'records'
RECORDS_DIR = os.path.join(APP_DIR, RECORDS_DIRNAME)

SAMPLE_RATE = 44100
CHANNELS = 1
SAMPLE_WIDTH = 2          # 16비트(int16) → 2바이트
CHUNK_SIZE = 1024

FILENAME_TIME_FORMAT = '%Y%m%d-%H%M%S'
FILE_EXTENSION = '.wav'

# 보너스: 날짜 입력 시 허용할 형식들.
DATE_INPUT_FORMATS = ('%Y%m%d', '%Y-%m-%d', '%Y.%m.%d', '%Y/%m/%d')

LINE_WIDTH = 60
HEADING_BORDER = '=' * LINE_WIDTH
SECTION_BORDER = '-' * LINE_WIDTH


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


def _ask(prompt):
    '''입력을 받아 양옆 공백을 제거해 돌려준다.

    EOF / Ctrl+C 는 None 으로 변환해 호출 측이 취소로 처리하게 한다.
    '''
    try:
        return input(prompt).strip()
    except EOFError:
        print()
        return None
    except KeyboardInterrupt:
        print()
        print('  사용자가 중단(Ctrl+C)했습니다.')
        return None


# ---------------------------------------------------------------------------
# 네이티브 stderr 잠금 (녹음 백엔드 보조)
# ---------------------------------------------------------------------------
class NativeStderrSilencer:
    '''ALSA/JACK 같은 C 라이브러리가 표준 라이브러리를 거치지 않고
    파일 디스크립터 2(stderr) 로 직접 쏟아내는 진단 메시지를 잠시
    /dev/null 로 돌린다.

    파이썬 계층의 예외/경고는 건드리지 않으므로 오류 처리에는 영향이
    없다. 녹음 백엔드 초기화 시에만 with 문으로 사용하며, 제약상
    외부 라이브러리가 아닌 표준 os 모듈만 쓴다.
    '''

    def __enter__(self):
        self._saved_stderr_fd = os.dup(2)
        self._devnull_fd = os.open(os.devnull, os.O_WRONLY)
        os.dup2(self._devnull_fd, 2)
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        os.dup2(self._saved_stderr_fd, 2)
        os.close(self._devnull_fd)
        os.close(self._saved_stderr_fd)
        return False


# ---------------------------------------------------------------------------
# 녹음 백엔드
# ---------------------------------------------------------------------------
class SoundDeviceRecorder:
    '''sounddevice + numpy 기반 녹음 백엔드.'''

    name = 'sounddevice'

    def __init__(self):
        self._frames = []

    def list_microphones(self):
        '''입력 채널이 있는 장치를 (번호, 이름) 목록으로 돌려준다.'''
        microphones = []
        with NativeStderrSilencer():
            for index, device in enumerate(_sd.query_devices()):
                if device.get('max_input_channels', 0) > 0:
                    microphones.append(
                        (index, device.get('name', '알 수 없음')))
        return microphones

    def record_until_event(self, stop_event):
        '''stop_event 가 set 될 때까지 녹음하고 raw 바이트로 돌려준다.'''
        self._frames = []

        def _callback(indata, frame_count, time_info, status):
            # status 는 언더런 등 상태 정보. 안정성을 위해 그대로 두고
            # 들어온 블록만 복사해 모은다.
            self._frames.append(indata.copy())

        with NativeStderrSilencer():
            with _sd.InputStream(samplerate=SAMPLE_RATE,
                                 channels=CHANNELS,
                                 dtype='int16',
                                 callback=_callback):
                stop_event.wait()

        if not self._frames:
            return b''
        return _np.concatenate(self._frames, axis=0).tobytes()


class PyAudioRecorder:
    '''pyaudio 기반 녹음 백엔드.'''

    name = 'pyaudio'

    def list_microphones(self):
        microphones = []
        with NativeStderrSilencer():
            audio = _pyaudio.PyAudio()
            try:
                for index in range(audio.get_device_count()):
                    info = audio.get_device_info_by_index(index)
                    if int(info.get('maxInputChannels', 0)) > 0:
                        microphones.append(
                            (index, info.get('name', '알 수 없음')))
            finally:
                audio.terminate()
        return microphones

    def record_until_event(self, stop_event):
        frames = []
        with NativeStderrSilencer():
            audio = _pyaudio.PyAudio()
            stream = None
            try:
                stream = audio.open(format=_pyaudio.paInt16,
                                    channels=CHANNELS,
                                    rate=SAMPLE_RATE,
                                    input=True,
                                    frames_per_buffer=CHUNK_SIZE)
                while not stop_event.is_set():
                    frames.append(
                        stream.read(CHUNK_SIZE,
                                    exception_on_overflow=False))
            finally:
                if stream is not None:
                    stream.stop_stream()
                    stream.close()
                audio.terminate()
        return b''.join(frames)


def _select_recorder():
    '''사용 가능한 녹음 백엔드를 골라 돌려준다. 없으면 None.'''
    if _sd is not None and _np is not None:
        return SoundDeviceRecorder()
    if _pyaudio is not None:
        return PyAudioRecorder()
    return None


# ---------------------------------------------------------------------------
# 파일 입출력
# ---------------------------------------------------------------------------
def _ensure_records_dir():
    '''records 폴더가 없으면 만든다.'''
    os.makedirs(RECORDS_DIR, exist_ok=True)


def _make_record_path():
    '''현재 시각으로 '년월일-시간분초.wav' 경로를 만든다.'''
    stamp = datetime.datetime.now().strftime(FILENAME_TIME_FORMAT)
    return os.path.join(RECORDS_DIR, stamp + FILE_EXTENSION)


def _save_wav(path, raw_bytes):
    '''raw PCM 바이트를 표준 wave 모듈로 WAV 파일에 쓴다.'''
    with wave.open(path, 'wb') as wav_file:
        wav_file.setnchannels(CHANNELS)
        wav_file.setsampwidth(SAMPLE_WIDTH)
        wav_file.setframerate(SAMPLE_RATE)
        wav_file.writeframes(raw_bytes)


def _duration_seconds(raw_bytes):
    '''raw PCM 바이트 길이로 녹음 길이(초)를 계산한다.'''
    bytes_per_second = SAMPLE_RATE * CHANNELS * SAMPLE_WIDTH
    if bytes_per_second == 0:
        return 0.0
    return len(raw_bytes) / bytes_per_second


# ---------------------------------------------------------------------------
# 기능 1. 마이크 목록 보기
# ---------------------------------------------------------------------------
def _show_microphones(recorder):
    if recorder is None:
        _print_warn('녹음 라이브러리가 없어 마이크를 조회할 수 없습니다.')
        return

    try:
        microphones = recorder.list_microphones()
    # 백엔드/드라이버 예외를 사용자 메시지로 바꾼다 (트레이스백 방지).
    except Exception as error:
        _print_error('마이크 조회 중 오류가 발생했습니다: {0}'.format(error))
        return

    if not microphones:
        _print_warn('입력 가능한 마이크를 찾지 못했습니다.')
        return

    _print_section('인식된 마이크 목록 (백엔드: {0})'.format(recorder.name))
    for index, mic_name in microphones:
        print('  [{0:>2}] {1}'.format(index, mic_name))


# ---------------------------------------------------------------------------
# 기능 2. 녹음 시작 (Enter 로 시작/중지)
# ---------------------------------------------------------------------------
def _record_voice(recorder):
    if recorder is None:
        _print_warn('녹음 라이브러리가 없어 녹음을 시작할 수 없습니다.')
        return

    try:
        _ensure_records_dir()
    except OSError as error:
        _print_error('records 폴더를 만들 수 없습니다: {0}'.format(error))
        return

    _print_section('음성 녹음')
    if _ask('  준비되면 Enter 를 눌러 시작하세요 (취소: Ctrl+C) ') is None:
        print('  녹음을 취소했습니다.')
        return

    stop_event = threading.Event()
    result = {}

    def _worker():
        try:
            result['data'] = recorder.record_until_event(stop_event)
        # 녹음 스레드의 예외는 메인에서 메시지로 처리한다.
        except Exception as error:
            result['error'] = error

    thread = threading.Thread(target=_worker)
    print('  ● 녹음 중...  중지하려면 Enter 를 누르세요.')
    thread.start()

    try:
        input()
    except (EOFError, KeyboardInterrupt):
        print()
    stop_event.set()
    thread.join()

    if 'error' in result:
        _print_error('녹음 중 오류가 발생했습니다: {0}'.format(result['error']))
        return

    raw_bytes = result.get('data', b'')
    if not raw_bytes:
        _print_warn('녹음된 데이터가 없습니다. 마이크 연결을 확인해 주세요.')
        return

    path = _make_record_path()
    try:
        _save_wav(path, raw_bytes)
    except OSError as error:
        _print_error('녹음 파일 저장에 실패했습니다: {0}'.format(error))
        return

    print()
    print('  저장 완료 : {0}'.format(os.path.basename(path)))
    print('  녹음 길이 : {0:.1f}초'.format(_duration_seconds(raw_bytes)))
    print('  저장 경로 : {0}'.format(path))


# ---------------------------------------------------------------------------
# 기능 3. (보너스) 날짜 범위로 녹음 파일 보기
# ---------------------------------------------------------------------------
def _parse_date(text):
    '''여러 형식의 날짜 문자열을 date 로 바꾼다. 실패하면 None.'''
    for date_format in DATE_INPUT_FORMATS:
        try:
            return datetime.datetime.strptime(text, date_format).date()
        except ValueError:
            continue
    return None


def _recording_date(filename):
    '''녹음 파일 이름 앞부분(년월일)을 date 로 바꾼다. 형식이 아니면 None.'''
    base = os.path.basename(filename)
    if not base.lower().endswith(FILE_EXTENSION):
        return None

    stem = base[:-len(FILE_EXTENSION)]
    parts = stem.split('-')
    if len(parts) < 2:
        return None

    date_token = parts[0]
    if len(date_token) != 8 or not date_token.isdigit():
        return None

    try:
        return datetime.datetime.strptime(date_token, '%Y%m%d').date()
    except ValueError:
        return None


def _ask_bound(label):
    '''날짜 경계를 입력받는다. 빈 입력은 '제한 없음'(None) 으로 본다.

    반환값:
      - (True, date)  : 정상 입력
      - (True, None)  : 빈 입력 → 해당 방향 제한 없음
      - (False, None) : 사용자가 취소(EOF / Ctrl+C)
    '''
    while True:
        answer = _ask('  {0} (예: 20260516, 비우면 제한 없음) > '.format(label))
        if answer is None:
            return (False, None)
        if answer == '':
            return (True, None)
        parsed = _parse_date(answer)
        if parsed is None:
            _print_warn('날짜 형식이 올바르지 않습니다. 예: 20260516')
            continue
        return (True, parsed)


def _list_recordings_in_range():
    _print_section('날짜 범위로 녹음 파일 보기')

    if not os.path.isdir(RECORDS_DIR):
        _print_warn('아직 records 폴더가 없습니다. 먼저 녹음을 해주세요.')
        return

    ok, start_date = _ask_bound('시작 날짜')
    if not ok:
        print('  조회를 취소했습니다.')
        return
    ok, end_date = _ask_bound('종료 날짜')
    if not ok:
        print('  조회를 취소했습니다.')
        return

    if start_date is not None and end_date is not None \
            and start_date > end_date:
        start_date, end_date = end_date, start_date
        _print_warn('시작/종료 날짜가 뒤바뀐 것 같아 자동으로 맞바꿨습니다.')

    matched = []
    for name in sorted(os.listdir(RECORDS_DIR)):
        file_date = _recording_date(name)
        if file_date is None:
            continue
        if start_date is not None and file_date < start_date:
            continue
        if end_date is not None and file_date > end_date:
            continue
        full_path = os.path.join(RECORDS_DIR, name)
        matched.append((name, os.path.getsize(full_path)))

    if not matched:
        _print_warn('해당 범위에 맞는 녹음 파일이 없습니다.')
        return

    print()
    print('  찾은 파일 : {0}개'.format(len(matched)))
    for name, size in matched:
        print('  - {0}  ({1:,} bytes)'.format(name, size))


# ---------------------------------------------------------------------------
# 진입점
# ---------------------------------------------------------------------------
def _print_menu():
    print()
    print('  1. 마이크 목록 보기')
    print('  2. 녹음 시작 (Enter 로 중지)')
    print('  3. 녹음 파일 보기 (날짜 범위)')
    print('  0. 종료')


def _main():
    _print_heading('javis 음성 기록기')

    recorder = _select_recorder()
    if recorder is None:
        _print_warn('녹음 가능한 라이브러리(sounddevice / pyaudio)를 '
                    '찾지 못했습니다.')
        _print_warn('녹음 기능은 비활성화되며, 나머지 기능은 사용할 수 있습니다.')
        print('      설치 예) pip install sounddevice  또는  '
              'pip install pyaudio')
    else:
        print('  녹음 백엔드 : {0}'.format(recorder.name))
    print('  저장 폴더   : {0}'.format(RECORDS_DIR))

    while True:
        _print_menu()
        choice = _ask('  > ')
        if choice is None or choice == '0':
            break
        if choice == '1':
            _show_microphones(recorder)
        elif choice == '2':
            _record_voice(recorder)
        elif choice == '3':
            _list_recordings_in_range()
        else:
            _print_warn('1, 2, 3, 0 중에서 선택해 주세요.')

    print()
    print('  javis 를 종료합니다.')


if __name__ == '__main__':
    try:
        _main()
    except KeyboardInterrupt:
        print()
        print('  사용자가 중단(Ctrl+C)했습니다.')
