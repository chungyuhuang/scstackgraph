from selenium import webdriver
import pyperclip
import subprocess
import time


def main():
    chrome_path = "/Users/PeterHuang/Downloads/chromedriver"
    # chromedriver.exe執行檔所存在的路徑
    web = webdriver.Chrome(chrome_path)
    web.get('https://ethereum.github.io/browser-solidity/#version=soljson-v0.4.18+commit.9cf6e910.js')

    load_source_code_from_db()
    copy_assembly_code()
    time.sleep(30)
    update_assembly_to_db()
    # web.close()


def load_source_code_from_db():
    code = '''pragma solidity^0.4.16;
                   contract test{}'''
    pyperclip.copy(code)


def update_assembly_to_db():
    assembly_code = pyperclip.paste()
    open('sourcecode', 'w').close()
    w = open('sourcecode', 'w')
    w.write(assembly_code)
    w.close()


def copy_assembly_code():
    subprocess.Popen(['./runsikulix', '-r', 'GetAssemblyCode.sikuli'], cwd='./sikuli/sikuliX-nightly')


if __name__ == '__main__':
    main()
