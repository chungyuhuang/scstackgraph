from selenium import webdriver
import pyperclip
import subprocess
import time
import psycopg2
import sys


def main():
    chrome_path = "/Users/soslab/Downloads/chromedriver"
    # chrome_path = "/Users/PeterHuang/Downloads/chromedriver"
    # chromedriver.exe執行檔所存在的路徑

    web = webdriver.Chrome(chrome_path)
    web.get('https://ethereum.github.io/browser-solidity/#version=soljson-v0.4.18+commit.9cf6e910.js')

    conn, cur = load_source_code_from_db()

    for i in cur:
        row_id = i[0]
        code = i[1]
        pyperclip.copy(code)
        copy_assembly_code()
        time.sleep(30)
        update_assembly_to_db(conn, row_id)

    conn.close()
    web.close()


def connect_to_db():
    try:
        conn = psycopg2.connect(database="soslab", user="soslab", password="$0$1ab", host="localhost", port="65432")
        return conn
    except Exception as ex:
        print("--- Unable to connect to the database. ---")
        print('Error: ', ex)
        sys.exit(0)


def load_source_code_from_db():
    conn = connect_to_db()
    cur = conn.cursor()

    try:
        cur.execute('SELECT COUNT(*) FROM contract;')
        num = cur.fetchall()[0][0]
        print('--- Number(s) of downloaded contract from Etherscan: {} ---'.format(num))
    except Exception as ex:
        print('--- Failed to select contract from database. ---')
        print('Error: ', ex)

    try:
        cur.execute('''SELECT id, sourcecode FROM contract WHERE id < 3 AND status <> 'GOT_ASSEMBLY';''')
    except Exception as ex:
        print('--- Failed to select source code from database. ---')
        print('Error: ', ex)
        sys.exit(0)

    return conn, cur


def update_assembly_to_db(conn, row_id):
    assembly_code = pyperclip.paste()

    # open('sourcecode', 'w').close()
    # w = open('sourcecode', 'w')
    # w.write(assembly_code)
    # w.close()

    cur = conn.cursor()
    try:
        cur.execute('''UPDATE contract SET assembly='{}', status='{}'
        WHERE id='{}';'''.format(assembly_code, 'GOT_ASSEMBLY', row_id))
        conn.commit()
    except Exception as ex:
        cur.execute('''UPDATE contract SET status='{}' WHERE id='{}';'''.format('GET_ASSEMBLY_FAILED', row_id))
        conn.commit()
        print('--- Failed to update assembly code to database. ---')
        print('Error: ', ex)


def copy_assembly_code():
    try:
        subprocess.Popen(['./runsikulix', '-r', 'GetAssemblyCode.sikuli'], cwd='./sikuli/sikuliX-nightly')
    except Exception as ex:
        print('--- Failed to execute Sikuli script. ---')
        print('Error: ', ex)
        sys.exit(0)


if __name__ == '__main__':
    main()
