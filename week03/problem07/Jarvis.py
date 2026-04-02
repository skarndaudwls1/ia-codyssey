# Jarvis.py
# 화성 기지 음성 녹음 시스템

import os
import wave
import datetime

try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False

RECORDS_DIR = 'records'
CHUNK = 1024
FORMAT = pyaudio.paInt16 if PYAUDIO_AVAILABLE else None
CHANNELS = 1
RATE = 44100


def ensure_records_dir():
    # records 폴더가 없으면 생성한다.
    if not os.path.exists(RECORDS_DIR):
        os.makedirs(RECORDS_DIR)


def list_microphones():
    # 시스템에서 인식된 마이크 목록을 출력한다.
    if not PYAUDIO_AVAILABLE:
        print('[오류] pyaudio 라이브러리가 설치되지 않았습니다.')
        print('  설치 명령: pip install pyaudio')
        return

    audio = pyaudio.PyAudio()
    print('\n=== 인식된 마이크 목록 ===')
    found = False
    for i in range(audio.get_device_count()):
        info = audio.get_device_info_by_index(i)
        if info['maxInputChannels'] > 0:
            print(f'  [{i}] {info["name"]}')
            found = True
    if not found:
        print('  인식된 마이크가 없습니다.')
    audio.terminate()


def record_audio():
    # 마이크로 음성을 녹음하고 records 폴더에 저장한다.
    if not PYAUDIO_AVAILABLE:
        print('[오류] pyaudio 라이브러리가 설치되지 않았습니다.')
        print('  설치 명령: pip install pyaudio')
        return

    try:
        seconds_input = input('녹음 시간을 입력하세요 (초, 기본값 5): ').strip()
        record_seconds = int(seconds_input) if seconds_input.isdigit() else 5
    except ValueError:
        record_seconds = 5

    ensure_records_dir()
    now = datetime.datetime.now()
    filename = now.strftime('%Y%m%d-%H%M%S') + '.wav'
    filepath = os.path.join(RECORDS_DIR, filename)

    audio = pyaudio.PyAudio()
    try:
        stream = audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK,
        )
    except OSError as e:
        print(f'[오류] 마이크를 열 수 없습니다: {e}')
        audio.terminate()
        return

    print(f'\n녹음 시작... ({record_seconds}초)')
    frames = []
    for _ in range(0, int(RATE / CHUNK * record_seconds)):
        data = stream.read(CHUNK)
        frames.append(data)
    print('녹음 완료.')

    stream.stop_stream()
    stream.close()
    audio.terminate()

    try:
        with wave.open(filepath, 'wb') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(audio.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(frames))
        print(f'[저장] {filepath}')
    except OSError as e:
        print(f'[오류] 파일 저장 실패: {e}')


def list_records():
    # records 폴더의 녹음 파일 목록을 출력한다.
    ensure_records_dir()
    files = sorted([f for f in os.listdir(RECORDS_DIR) if f.endswith('.wav')])
    print('\n=== 녹음 파일 목록 ===')
    if not files:
        print('  저장된 녹음 파일이 없습니다.')
    else:
        for i, name in enumerate(files, 1):
            print(f'  {i}. {name}')
        print(f'\n총 {len(files)}개')


def list_records_by_date():
    # 특정 날짜 범위의 녹음 파일을 출력한다. (보너스)
    ensure_records_dir()

    start_input = input('시작 날짜 입력 (YYYYMMDD): ').strip()
    end_input = input('종료 날짜 입력 (YYYYMMDD): ').strip()

    try:
        start = datetime.datetime.strptime(start_input, '%Y%m%d')
        end = datetime.datetime.strptime(end_input, '%Y%m%d').replace(
            hour=23, minute=59, second=59
        )
    except ValueError:
        print('[오류] 날짜 형식이 올바르지 않습니다. 예) 20260331')
        return

    files = sorted([f for f in os.listdir(RECORDS_DIR) if f.endswith('.wav')])
    result = []
    for name in files:
        date_part = name.split('-')[0]
        try:
            file_date = datetime.datetime.strptime(date_part, '%Y%m%d')
            if start <= file_date <= end:
                result.append(name)
        except ValueError:
            continue

    print(f'\n=== {start_input} ~ {end_input} 녹음 파일 ===')
    if not result:
        print('  해당 범위의 파일이 없습니다.')
    else:
        for i, name in enumerate(result, 1):
            print(f'  {i}. {name}')
        print(f'\n총 {len(result)}개')


def print_menu():
    print('\n============================')
    print('   화성 기지 음성 녹음 시스템')
    print('============================')
    print('1. 마이크 목록 확인')
    print('2. 음성 녹음')
    print('3. 녹음 파일 목록')
    print('4. 날짜 범위로 파일 검색 (보너스)')
    print('0. 종료')
    print('----------------------------')


def main():
    if not PYAUDIO_AVAILABLE:
        print('[경고] pyaudio 미설치 — 녹음 기능을 사용하려면 아래 명령으로 설치하세요.')
        print('  pip install pyaudio')

    while True:
        print_menu()
        choice = input('번호를 선택하세요: ').strip()

        if choice == '1':
            list_microphones()

        elif choice == '2':
            record_audio()

        elif choice == '3':
            list_records()

        elif choice == '4':
            list_records_by_date()

        elif choice == '0':
            print('종료합니다.')
            break

        else:
            print('[안내] 올바른 번호를 입력하세요.')

        input('\n계속하려면 Enter 를 누르세요...')


if __name__ == '__main__':
    main()
