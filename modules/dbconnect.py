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
        cur.execute('SELECT COUNT(*) FROM contract WHERE checksame = 0;')
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
        WHERE {} <> '' AND status = '{}' AND checksame = 0;'''.format(db_column, db_status))
        num = cur.fetchall()[0][0]
        print('---> {} contract(s) waiting for analysis ---'.format(num))
    except Exception as ex:
        print('--- Failed to count ready contract numbers from database. ---')
        print('Error: ', ex)
        sys.exit(0)

    conn.close()


def load_source_code_from_db():
    conn = connect_to_db()
    cur = conn.cursor()

    try:
        cur.execute('''SELECT id, sourcecode FROM contract
        WHERE sourcecode <> '' AND status = 'PENDING' AND checksame = 0 ORDER BY id;''')
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
        print('--- Querying contract assembly code from DB ---')
        cur.execute('''
        SELECT id, address, {}
        FROM contract
        WHERE {} <> '' AND status = '{}' AND checksame = 0
        ORDER BY id;
        '''.format(db_column, db_column, db_status))
    except Exception as ex:
        print('--- Failed to select source code from database. ---')
        print('Error: ', ex)
        sys.exit(0)

    return cur


def update_analysis_result_to_db(db_status, result, row_id):
    conn = connect_to_db()
    cur = conn.cursor()

    try:
        print('\t--- Updating contract analysis result to DB, id: {} ---'.format(row_id))
        cur.execute('''
        UPDATE contract
        SET status = '{}', analysis_result = '{}'
        WHERE id='{}';
        '''.format(db_status, result, row_id))
        conn.commit()
        if result:
            print('\t--- Updating cycle information to DB, id: {} ---'.format(row_id))
            cur.execute('''
                    INSERT INTO cycle_contract (contract_id)
                    VALUES ('{}');
                    '''.format(row_id))
            conn.commit()
    except Exception as ex:
        print('\t--- Failed to update result to database. ---')
        print('Error: ', ex)
        sys.exit(0)


def update_crawling_to_db(conn, row_id, input_code):
    code_origin = pyperclip.paste()
    assembly_code = code_origin.replace("'", "''")

    cur = conn.cursor()

    if code_origin == input_code:
        try:
            cur.execute('''UPDATE contract SET status='{}' WHERE id='{}';'''.format('COMPILE_ERROR',
                                                                                    row_id))
            conn.commit()
            print('''\t--- Update id {} status '{}' to database. ---'''.format(row_id, 'COMPILE_ERROR'))
        except Exception as ex:
            print('\t--- Failed to update to database. ---')
            print('Error: ', ex)
            sys.exit(0)
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
            print('\t--- Update id {} assembly to database. ---'.format(row_id))
        except Exception as ex:
            print('\t--- Failed to update assembly code to database. ---')
            print('Error: ', ex)
            sys.exit(0)


def update_opcode_to_db(input_code, row_id):
    conn = connect_to_db()
    cur = conn.cursor()

    try:
        cur.execute('''UPDATE contract SET runtime_opcode='{}' WHERE id='{}';'''.format(input_code, row_id))
        conn.commit()
        print('\t--- Update runtime opcode to database. ---')
    except Exception as ex:
        print('\t--- Failed to update runtime opcode to database. ---')
        print('Error: ', ex)
        sys.exit(0)


def update_cycle_info_to_db(row_id, cfg, code, opcode, graph, node, edge, count):
    conn = connect_to_db()
    cur = conn.cursor()

    try:
        print('\t--- Updating cycle info to DB, id: {} ---'.format(row_id))
        cur.execute('''
        UPDATE cycle_contract
        SET cycle_cfg = '{}', cycle_code = '{}', cycle_opcode = '{}',
         cycle_graph_count = {}, cycle_node_count = {}, cycle_edge_count = {}, cycle_count = {}
        WHERE contract_id = '{}';
        '''.format(cfg, code, opcode, graph, node, edge, count, row_id))
        conn.commit()
    except Exception as ex:
        print('\t--- Failed to update result to database. ---')
        print('Error: ', ex)
        sys.exit(0)
