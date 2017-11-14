from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from subprocess import check_output
from modules import dbconnect as db
import pyperclip
import subprocess
import time
import sys
import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-asm", "--asm", help="generate assembly code", action='store_true')
    parser.add_argument("-op", "--op", help="generate runtime opcode", action='store_true')
    args = parser.parse_args()

    chrome_path = "/Users/soslab/Downloads/chromedriver"
    # chrome_path = "/Users/PeterHuang/Downloads/chromedriver"

    if args.asm:
        web = webdriver.Chrome(chrome_path)
        web.get('https://ethereum.github.io/browser-solidity/#version=soljson-v0.4.18+commit.9cf6e910.js')

    db.total_contract_count()
    conn, cur = db.load_source_code_from_db()

    for i in cur:
        row_id = i[0]
        code = i[1]

        if args.op:
            w = open('contract.sol', 'w')
            w.write(code)
            w.close()
            result = str(gen_runtime_binary('contract.sol'))
            if result is not None:
                print('Result -> ', result)
                idx = result.index('Binary of the runtime part:')
                result = result[idx + 99: len(result) - 3]
                pyperclip.copy(result)
                web2 = webdriver.Firefox()
                web2.get('https://etherscan.io/opcode-tool')
                web2.find_element_by_id('ContentPlaceHolder1_txtByteCode').send_keys(Keys.COMMAND, 'v')
                time.sleep(10)
                web2.find_element_by_id('ContentPlaceHolder1_btnSubmit').click()
                time.sleep(10)
                runtime_op = web2.find_element_by_class_name('col-md-10').text
                position = runtime_op.index('Decoded Bytecode :')
                web2.close()
                db.update_crawling_to_db(conn, row_id, runtime_op[position + 20:len(runtime_op)])
        elif args.asm:
            pyperclip.copy(code)
            copy_assembly_code()
            time.sleep(55)
            db.update_crawling_to_db(conn, row_id, code)
        else:
            print('Must use an argument, -asm for assembly, -r for runtime binary.')
            sys.exit(0)

    conn.close()
    # web.close()


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
