import sys
import graphviz as gv
import functools
from collections import deque
import argparse
import re
import psycopg2
import time


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--i", help="input file name")
    parser.add_argument("-f", "--f", help="read from DB", action='store_true')
    args = parser.parse_args()

    # print(analysis_code())

    # if args.f:
    #     # read from DB
    #     filename = "sourcecode"
    #     cur = load_from_db()
    #     for i in cur:
    #         row_id = i[0]
    #         contract_addr = i[1]
    #         print('\n ---> Analyzing contract: {}'.format(contract_addr))
    #         assembly_code = i[2]
    #         w = open(filename, 'w')
    #         w.write(assembly_code)
    #         w.close()
    #         code_preproc(filename)
    start_time = time.time()
    #         result, end_node = analysis_code()
    #         if result:
    #             print('\n ---> Positive Cycle Found: [Yes] node {}'.format(end_node))
    #         else:
    #             print('\n ---> Positive Cycle Found: [No]')
    duration = time.time() - start_time
    print(duration)
    #         update_result_to_db(result, row_id)
    # elif args.i:
    #     filename = args.i
    #     code_preproc(filename)
    #     result, end_node = analysis_code()
    #     if result:
    #         print('\n ---> Positive Cycle Found: [Yes] node {}'.format(end_node))
    #     else:
    #         print('\n ---> Positive Cycle Found: [No]')
    # else:
    #     print('Must use an argument, -i for individual source code, -f use source code from DB')

    # sys.exit(0)


def code_preproc(filename):
    print(' --- Start checking contract \"{}\" ---'.format(filename))
    w = open('opcode', 'w')

    with open(filename, 'r') as f:
        is_data = 0
        for idx, line in enumerate(f):
            is_tag = 0
            new_line = line.split('			')
            check_tag = new_line[0].split('    tag')
            if is_data:
                if len(check_tag) == 2:
                    is_tag = 1
                if len(new_line) > 1 or is_tag:
                    if new_line[0].rstrip().strip() == 'REVERT':
                        continue
                    else:
                        w.write(new_line[0].rstrip().strip() + '\n')
            if new_line[0].rstrip() == '.data':
                is_data = 1
    w.close()


def connect_to_db():
    try:
        conn = psycopg2.connect(database="soslab", user="soslab", password="$0$1ab", host="140.119.19.77", port="65432")
        return conn
    except Exception as ex:
        print(" --- Unable to connect to the database. ---")
        print('Error: ', ex)
        sys.exit(0)


def load_from_db():
    conn = connect_to_db()
    cur = conn.cursor()

    try:
        print(' --- Querying contract assembly code from DB ---')
        cur.execute('''
        SELECT COUNT(*)
        FROM contract
        WHERE assembly <> '' AND status = 'GOT_ASSEMBLY';''')
        num = cur.fetchall()[0][0]
        print(' ---> {} contract(s) waiting for analysis ---'.format(num))
        cur.execute('''
        SELECT id, address, assembly
        FROM contract
        WHERE assembly <> '' AND status = 'GOT_ASSEMBLY'
        ORDER BY id;
        ''')
    except Exception as ex:
        print(' --- Failed to select source code from database. ---')
        print('Error: ', ex)
        sys.exit(0)

    return cur


def update_result_to_db(result, row_id):
    conn = connect_to_db()
    cur = conn.cursor()

    try:
        print(' --- Updating contract analysis result to DB, id: {} ---'.format(row_id))
        cur.execute('''
        UPDATE contract
        SET status = '{}'
        WHERE id='{}';
        '''.format('CFG_CONSTRUCTED', row_id))
        conn.commit()
        cur.execute('''
        UPDATE contract
        SET analysisresult = '{}'
        WHERE id='{}';
        '''.format(result, row_id))
        conn.commit()
    except Exception as ex:
        print(' --- Failed to update result to database. ---')
        print('Error: ', ex)
        sys.exit(0)


def analysis_code():
    nodes = []
    edges = []
    init_graph(nodes, edges)
    # print(nodes)
    # print(edges)
    return count_stack_size(nodes, edges)


def count_stack_size(nodes, edges):
    count = 0
    check_result = 0
    end_node = ''
    queue = deque([])
    node_list = []
    edge_list = []

    for n in nodes:
        node_idx = n[0]
        node_list.append(node_idx)
    for e in edges:
        edge_idx = e[0][1]
        edge_list.append(edge_idx)

    # list with all the nodes without input edge
    graph_head = find_graph_head(node_list, edge_list)
    # print(graph_head, len(graph_head))
    print('\n ---> Total {} graph(s) constructed'.format(len(graph_head)))

    for start_node in graph_head:
        start_node_idx = start_node[1]
        queue.append(nodes[start_node_idx])

    # start_node = nodes[start_idx]
    # start_node[1]['id'] = 0
    # queue.append(start_node)
    # queue.append(nodes[87])

    # print(queue)
    print('      Checking CFG', end='')

    while len(queue):
        if count % 10000 == 0:
            print('.', end='')
            sys.stdout.flush()

        count += 1
        father_node = queue.popleft()
        # print('\nfather node = ', father_node)
        f_idx = father_node[0]
        f_id = father_node[1].get('id')

        for e in edges:
            is_jumpdest = 0
            edge_relation = e[0]
            edge_from = edge_relation[0]
            edge_to = edge_relation[1]
            edge_weight = e[1].get('id')

            if edge_from == f_idx:
                # print('edge = ', e)
                for n in nodes:
                    child_idx = n[0]
                    if edge_to == child_idx:
                        n_label_name = n[1].get('label').split(' ')
                        # print('child node = ', n)
                        c_id = n[1].get('id')
                        # print(f_id, edge_weight, c_id)
                        if int(f_id) + int(edge_weight) > int(c_id):
                            child_node_info = n[1]
                            child_node_info['id'] = str(int(f_id) + int(edge_weight))
                            check_c_id = child_node_info.get('id')
                            # print(check_c_id)
                            if int(check_c_id) > 1023:
                                check_result = 1
                                end_node = n
                                break
                                # sys.exit(0)
                            else:
                                queue.append(n)
                        if n_label_name[0] == 'JUMPDEST':
                            is_jumpdest = 1
                            continue
                        else:
                            break
                if is_jumpdest:
                    continue
                else:
                    break
        # print('queue = ', queue)
    return check_result, end_node


def find_graph_head(node_list, edge_list):
    head_list = []

    for idx, n in enumerate(node_list):
        if n not in edge_list:
            head_list.append((n, idx))

    return head_list


def init_graph(nodes, edges):
    print(' ---> Initiating Control Flow Graph')

    stack_push_one = ['PUSH', 'DUP', 'CALLER', 'CALLVALUE', 'GAS', 'CALLDATASIZE', 'PC', 'MSIZE',
                      'COINBASE', 'GASLIMIT', 'DIFFICULTY', 'TIMESTAMP', 'NUMBER', 'CODESIZE', 'GASPRICE', 'ADDRESS',
                      'ORIGIN']
    stack_pop_one = ['POP', 'LT', 'GT', 'EQ', 'AND', 'OR', 'XOR', 'ADD', 'SUB',
                     'MUL', 'DIV', 'EXP', 'KECCAK256', 'SHA3', 'BYTE', 'SIGNEXTEND', 'SUICIDE']
    stack_pop_two = ['MSTORE', 'SSTORE', 'RETURN', 'CREATE', 'ADDMOD', 'MULMOD']
    stack_pop_three = ['CODECOPY', 'CALLDATACOPY']
    stack_unchange = ['SWAP', 'MLOAD', 'SLOAD', 'NOT', 'ISZERO', 'CALLDATALOAD', 'EXTCODESIZE', 'STOP', 'INVALID',
                      'BALANCE', 'BLOCKHASH']

    stack_size = '0'
    stack_sum = 0
    edge_color = 'black'
    instruction = ''
    prev_instruction = '0'

    with open('opcode_new', 'r') as f:
        stack_header = '0'
        nodes.append((stack_header,
                      {'label': 'Start ' + stack_header,
                       'id': '0',
                       'fontname': 'Helvetica',
                       'shape': 'hexagon',
                       'fontcolor': 'gray',
                       'color': 'white',
                       'style': 'filled',
                       'fillcolor': '#006699',
                       }))
        for idx, line in enumerate(f):
            s = line.rstrip().split(' ')
            op_label = s[0].strip('[]')

            if 'LOG' not in s[1]:
                instruction = re.sub(r'\d+', '', str(s[1]))

            if 'Unknown' in instruction:
                continue

            if instruction == 'JUMPDEST':
                nodes.append((op_label,
                              {'label': 'JUMPDEST ' + op_label,
                               'id': '0',
                               # 'fontname': 'Helvetica',
                               # 'shape': 'hexagon',
                               # 'fontcolor': 'gray',
                               # 'color': 'white',
                               # 'style': 'filled',
                               # 'fillcolor': '#006699',
                               }))
                edge_color = 'black'
                stack_size = '+0'
                one_before_header = str(stack_header)
                stack_header = str(op_label)
                edges.append(((one_before_header, stack_header),
                              {'label': instruction + ' ' + stack_size,
                               'color': edge_color,
                               'id': str(stack_size)}))
                prev_instruction = line
                continue

            if instruction in ['JUMP', 'JUMPI'] and 'PUSH' in prev_instruction.strip().split(' ')[1]:
                if instruction == 'JUMP':
                    stack_size = '-1'
                    stack_sum -= 1

                if instruction == 'JUMPI':
                    stack_size = '-2'
                    stack_sum -= 2

                one_before_header = str(stack_header)
                stack_header = str(op_label)
                nodes.append((stack_header,
                              {'label': str(stack_sum),
                               'id': '-1'}))
                jump_label = int(prev_instruction.strip().split(' ')[2], 16)
                jump_from = str(stack_header)
                jump_to = str(jump_label)
                edge_color = 'blue'
                edges.append(((one_before_header, stack_header),
                              {'label': instruction + ' ' + stack_size,
                               'color': edge_color,
                               'id': str(stack_size)}))
                edges.append(((jump_from, jump_to),
                              {'label': '',
                               'color': edge_color,
                               'id': '0'}))
                prev_instruction = line
                continue

            # if instruction.rstrip() == 'JUMPDEST':
            #     tag_number = int(prev_instruction.split(' ')[1]) + 100000
            #     stack_header = str(tag_number)
            #     continue

            for key_world in stack_push_one:
                if key_world == instruction:
                    edge_color = 'red'
                    stack_size = '+1'
                    stack_sum += 1
                    break

            for key_world in stack_pop_three:
                if key_world == instruction:
                    edge_color = 'orange'
                    stack_size = '-3'
                    stack_sum -= 3
                    break

            for key_world in stack_pop_two:
                if key_world == instruction:
                    edge_color = 'orange'
                    stack_size = '-2'
                    stack_sum -= 2
                    break

            for key_world in stack_pop_one:
                if key_world == instruction:
                    edge_color = 'green'
                    stack_size = '-1'
                    stack_sum -= 1
                    break

            for key_world in stack_unchange:
                if key_world == instruction:
                    edge_color = 'brown'
                    stack_size = '+0'
                    break

            if instruction == 'CALL' or instruction == 'CALLCODE':
                edge_color = 'purple'
                stack_size = '-6'
                stack_sum -= 6

            if instruction == 'DELEGATECALL':
                edge_color = 'purple'
                stack_size = '-5'
                stack_sum -= 5

            if instruction == 'EXTCODECOPY':
                edge_color = 'purple'
                stack_size = '-4'
                stack_sum -= 4

            if 'LOG' in s[1]:
                edge_color = 'red'
                instruction = s[1]
                log_number = instruction.split('LOG')[1]
                stack_size = '-' + str(int(log_number) + 2)
                stack_sum += int(stack_size)

            one_before_header = str(stack_header)
            stack_header = str(op_label)
            nodes.append((stack_header,
                          {'label': str(stack_sum),
                           'id': '-1'}))
            edges.append(((one_before_header, stack_header),
                          {'label': instruction + ' ' + stack_size,
                           'color': edge_color,
                           'id': str(stack_size)}))
            prev_instruction = line
    print(' ---> Control Flow Graph Constructed')
    # create_graph(nodes, edges)


def create_graph(n, e):
    digraph = functools.partial(gv.Digraph, format='svg')
    # g1 = apply_styles(add_edges(add_nodes(digraph(), nodes), edges), styles)
    g1 = add_edges(add_nodes(digraph(), n), e)
    # g1.render(filename='img/g1')

    # g8 = apply_styles(
    #     add_edges(
    #         add_nodes(digraph(), [
    #             ('DD', {'label': 'Node D'}),
    #             ('EE', {'label': 'Node E'}),
    #             'FF'
    #         ]),
    #         [
    #             (('DD', 'EE'), {'label': 'Edge 3'}),
    #             (('DD', 'FF'), {'label': 'Edge 4'}),
    #             ('EE', 'FF')
    #         ]
    #     ),
    #     {
    #         'nodes': {
    #             'shape': 'square',
    #             'style': 'filled',
    #             'fillcolor': '#cccccc',
    #         }
    #     }
    # )
    #
    # g1.subgraph(g8)
    # g1.edge('B', 'EE', color='red', weight='2')
    print(' ---> Rendering graph')
    g1.render(filename='img/g1')
    print(' ---> Graph Constructed')


def add_nodes(graph, nodes):
    for n in nodes:
        if isinstance(n, tuple):
            graph.node(n[0], **n[1])
        else:
            graph.node(n)
    return graph


def add_edges(graph, edges):
    for e in edges:
        if isinstance(e[0], tuple):
            graph.edge(*e[0], **e[1])
        else:
            graph.edge(*e)
    return graph


def apply_styles(graph, styles):
    graph.graph_attr.update(
        ('graph' in styles and styles['graph']) or {}
    )
    graph.node_attr.update(
        ('nodes' in styles and styles['nodes']) or {}
    )
    graph.edge_attr.update(
        ('edges' in styles and styles['edges']) or {}
    )
    return graph


if __name__ == '__main__':
    main()
