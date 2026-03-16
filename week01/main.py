def read_log():
    try:
        with open('mission_computer_main.log', 'r') as f:
            print(f.read())

    except FileNotFoundError:
        print('Error: 파일을 찾을 수 없습니다.')

    except PermissionError:
        print('Error: 파일 읽기 권한이 없습니다.')

    except UnicodeDecodeError:
        print('Error: 인코딩을 확인해주세요.')

    except IsADirectoryError:
        print('Error: 파일이 아닌 디렉토리입니다.')

    except Exception as e:
        print(f'Error: {e}')


read_log()