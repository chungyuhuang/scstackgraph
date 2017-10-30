from selenium import webdriver
import pyperclip
import subprocess
from subprocess import check_output
import time
import psycopg2
import sys
import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-asm", "--asm", help="generate assembly code", action='store_true')
    parser.add_argument("-r", "--r", help="generate runtime binary", action='store_true')
    args = parser.parse_args()

    # chrome_path = "/Users/soslab/Downloads/chromedriver"
    chrome_path = "/Users/PeterHuang/Downloads/chromedriver"
    # chromedriver.exe執行檔所存在的路徑

    if args.asm:
        web = webdriver.Chrome(chrome_path)
        web.get('https://ethereum.github.io/browser-solidity/#version=soljson-v0.4.18+commit.9cf6e910.js')

    conn, cur = load_source_code_from_db()

    for i in cur:
        row_id = i[0]
        code = i[1]

        if args.r:
            w = open('contract.sol', 'w')
            w.write(code)
            w.close()
            result = gen_runtime_binary('contract.sol')
            if result is not None:
                result = str(result).split('Binary of the runtime part: \\n')[1].split('\\n')[0]
                update_to_db(args, conn, row_id, result)
        elif args.asm:
            pyperclip.copy(code)
            copy_assembly_code()
            time.sleep(30)
            update_to_db(args, conn, row_id, code)
        else:
            print('Must use an argument, -asm for assembly, -r for runtime binary.')
            sys.exit(0)

    conn.close()
    # web.close()


def connect_to_db():
    try:
        conn = psycopg2.connect(database="soslab", user="soslab", password="$0$1ab", host="140.119.19.77", port="65432")
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
        cur.execute('''SELECT id, sourcecode FROM contract
        WHERE status = 'PENDING' AND sourcecode <> '' ORDER BY id;''')
    except Exception as ex:
        print('--- Failed to select source code from database. ---')
        print('Error: ', ex)
        conn.close()
        sys.exit(0)

    return conn, cur


def update_to_db(args, conn, row_id, input_code):
    code_origin = pyperclip.paste()
    assembly_code = code_origin.replace("'", " ")

    # open('sourcecode', 'w').close()
    # w = open('sourcecode', 'w')
    # w.write(assembly_code)
    # w.close()

    cur = conn.cursor()

    if args.r:
        try:
            cur.execute('''
                UPDATE contract
                SET runtime_opcode='{}', status='{}'
                WHERE id='{}';
                '''.format(input_code,
                           'GOT_RUNTIME_BINARY',
                           row_id))
            conn.commit()
        except Exception as ex:
            print('--- Failed to update runtime binary to database. ---')
            print('Error: ', ex)
    else:
        if code_origin == input_code:
            try:
                cur.execute('''UPDATE contract SET status='{}' WHERE id='{}';'''.format('COMPILE_ERROR',
                                                                                        row_id))
                conn.commit()
            except Exception as ex:
                print('--- Failed to update to database. ---')
                print('Error: ', ex)
        else:
            try:
                cur.execute('''
                UPDATE contract
                SET assembly='{}', status='{}'
                WHERE id='{}';
                '''.format(assembly_code,
                           'GOT_ASSEMBLY',
                           row_id))
                conn.commit()
            except Exception as ex:
                print('--- Failed to update assembly code to database. ---')
                print('Error: ', ex)


def gen_runtime_binary(file):
    try:
        output = check_output(['solc', '--bin-runtime', file])
        return output
    except Exception as ex:
        print('--- Failed to execute solc. ---')
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
