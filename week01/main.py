LOG_FILE = 'mission_computer_main.log'
ERROR_LOG_FILE = 'error_log.txt'

try:
    with open(LOG_FILE, 'r') as log_file:
        line = log_file.readlines()
        print(line)
        header = line[0]
        log_data = line[1:]
        print(log_data)
        log_data.reverse()
        

        print(header, end='')
        for line in log_data:
            print(line, end='')

    error_text = []
    for extract in log_data:
        if 'unstable' in extract or 'explosion' in extract:
            error_text.append(extract)

    with open(ERROR_LOG_FILE, 'w') as error_log_file:
        for apply in error_text:
            error_log_file.write(apply)

    print()
    print('Error Log extraction complete : ' + ERROR_LOG_FILE)

except FileNotFoundError:
    print('Error: 파일을 찾을 수 없습니다.')

except PermissionError:
    print('Error: 파일 읽기 권한이 없습니다.')

except UnicodeDecodeError:
    print('Error: 인코딩을 확인해주세요.')

except IsADirectoryError:
    print('Error: 파일이 아닌 디렉토리입니다.')

except Exception as error:
    print('Error: ' + str(error))