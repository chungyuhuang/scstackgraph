import psycopg2
import sys
import pyperclip


def connect_to_db():
    try:
        conn = psycopg2.connect(database="soslab", user="soslab", password="$0$1ab", host="140.119.19.77", port="65432")
        return conn
    except Exception as ex:
        print(" --- Unable to connect to the database. ---")
        print('Error: ', ex)
        sys.exit(0)


def total_contract_count():
    conn = connect_to_db()
    cur = conn.cursor()

    try:
        cur.execute('SELECT COUNT(*) FROM contract;')
        num = cur.fetchall()[0][0]
        print('--- Number(s) of downloaded contract from Etherscan: {} ---'.format(num))
    except Exception as ex:
        print('--- Failed to count total contract numbers from database. ---')
        print('Error: ', ex)
        conn.close()
        sys.exit(0)

    conn.close()


def ready_contract_count(db_column, db_status):
    conn = connect_to_db()
    cur = conn.cursor()

    try:
        cur.execute('''
        SELECT COUNT(*)
        FROM contract
        WHERE {} <> '' AND status = '{}';'''.format(db_column, db_status))
        num = cur.fetchall()[0][0]
        print(' ---> {} contract(s) waiting for analysis ---'.format(num))
    except Exception as ex:
        print(' --- Failed to count ready contract numbers from database. ---')
        print('Error: ', ex)
        sys.exit(0)

    conn.close()


def load_source_code_from_db():
    conn = connect_to_db()
    cur = conn.cursor()

    try:
        cur.execute('''SELECT id, sourcecode FROM contract
        WHERE sourcecode <> '' AND status = 'PENDING' ORDER BY id;''')
    except Exception as ex:
        print('--- Failed to select source code from database. ---')
        print('Error: ', ex)
        conn.close()
        sys.exit(0)

    return conn, cur


def load_assembly_from_db(db_column, db_status):
    conn = connect_to_db()
    cur = conn.cursor()

    try:
        print(' --- Querying contract assembly code from DB ---')
        cur.execute('''
        SELECT id, address, {}
        FROM contract
        WHERE {} <> '' AND status = '{}'
        ORDER BY id;
        '''.format(db_column, db_column, db_status))
    except Exception as ex:
        print(' --- Failed to select source code from database. ---')
        print('Error: ', ex)
        sys.exit(0)

    return cur


def update_analysis_result_to_db(db_status, result, row_id):
    conn = connect_to_db()
    cur = conn.cursor()

    try:
        print(' --- Updating contract analysis result to DB, id: {} ---'.format(row_id))
        cur.execute('''
        UPDATE contract
        SET status = '{}'
        WHERE id='{}';
        '''.format(db_status, row_id))
        conn.commit()
        cur.execute('''
        UPDATE contract
        SET analysis_result = '{}'
        WHERE id='{}';
        '''.format(result, row_id))
        conn.commit()
    except Exception as ex:
        print(' --- Failed to update result to database. ---')
        print('Error: ', ex)
        sys.exit(0)


def update_crawling_to_db(args, conn, row_id, input_code):
    code_origin = pyperclip.paste()
    assembly_code = code_origin.replace("'", " ")

    cur = conn.cursor()

    if args.op:
        try:
            input_code = input_code.replace("'", "")
            cur.execute('''
                UPDATE contract
                SET runtime_opcode='{}'
                WHERE id='{}';
                '''.format(input_code,
                           row_id))
            conn.commit()
            print('--- Update runtime binary to database. ---')
        except Exception as ex:
            print('--- Failed to update runtime binary to database. ---')
            print('Error: ', ex)
    else:
        if code_origin == input_code:
            try:
                cur.execute('''UPDATE contract SET status='{}' WHERE id='{}';'''.format('COMPILE_ERROR',
                                                                                        row_id))
                conn.commit()
                print('''--- Update id {} status '{}' to database. ---'''.format(row_id, 'COMPILE_ERROR'))
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
                print('--- Update id {} assembly to database. ---'.format(row_id))
            except Exception as ex:
                print('--- Failed to update assembly code to database. ---')
                print('Error: ', ex)
