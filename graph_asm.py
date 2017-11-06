from collections import deque
from modules import db_connect as db
import sys
import graphviz as gv
import functools
import argparse
import re
import time


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--i", help="input file name")
    parser.add_argument("-f", "--f", help="read from DB", action='store_true')
    args = parser.parse_args()

    if args.f:
        db.ready_contract_count('assembly', 'GOT_ASSEMBLY')
        cur = db.load_assembly_from_db('assembly', 'GOT_ASSEMBLY')
        for i in cur:
            row_id = i[0]
            contract_addr = i[1]
            print('\n ---> Analyzing contract: {}'.format(contract_addr))
            assembly_code = i[2]

            filename = 'sourcecode'
            w = open(filename, 'w')
            w.write(assembly_code)
            w.close()

            start_time = time.time()
            result, end_node = analysis_code()
            print(result, end_node)

            duration = time.time() - start_time
            m, s = divmod(duration, 60)
            h, m = divmod(m, 60)
            print(' --- Time using: {:2.0f}h{:2.0f}m{:2.0f}s'.format(h, m, s))

            if result:
                print('\n ---> Positive Cycle Found: [Yes] node {}'.format(end_node))
            else:
                print('\n ---> Positive Cycle Found: [No]')

            db.update_analysis_result_to_db('CFG_CONSTRUCTED', result, row_id)
    elif args.i:
        filename = args.i
        code_preproc(filename)
        result, end_node = analysis_code()
        if result:
            print('\n ---> Positive Cycle Found: [Yes] node {}'.format(end_node))
        else:
            print('\n ---> Positive Cycle Found: [No]')
    else:
        print('Must use an argument, -i for individual source code, -f use source code from DB')
        sys.exit(0)


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


def analysis_code():
    filename = 'sourcecode'
    code_preproc(filename)
    nodes = []
    edges = []
    init_graph(nodes, edges)

    # print(nodes)
    # print(edges)

    # create_graph(nodes, edges)

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
    print('\n ---> Total {} graph(s) constructed'.format(len(graph_head)))

    ana_result, node = count_stack_size(nodes, edges, graph_head)

    return ana_result, node


def find_graph_head(node_list, edge_list):
    head_list = []

    for idx, n in enumerate(node_list):
        if n not in edge_list:
            head_list.append((n, idx))

    return head_list


def count_stack_size(nodes, edges, graph_head):
    count = 0
    check_result = 0
    end_node = ''
    queue = deque([])

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
    prev_instruction = '0'

    with open('opcode', 'r') as f:
        stack_header = '100000'
        nodes.append((stack_header,
                      {'label': 'JUMPDEST ' + stack_header,
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
            if 'LOG' not in s[0]:
                instruction = re.sub(r'\d+', '', str(s[0]))

            if instruction == 'tag':
                tag_number = str(int(s[1]) + 100000)
                nodes.append((tag_number,
                              {'label': 'JUMPDEST ' + tag_number,
                               'id': '0',
                               'fontname': 'Helvetica',
                               'shape': 'hexagon',
                               'fontcolor': 'gray',
                               'color': 'white',
                               'style': 'filled',
                               'fillcolor': '#006699',
                               }))

                if prev_instruction.rstrip() == 'JUMP [out]'\
                        or prev_instruction.rstrip().split(' ')[0] in ['RETURN', 'STOP']:
                    stack_header = str(tag_number)
                    continue
                else:
                    edge_color = 'black'
                    stack_size = '+0'
                    one_before_header = str(stack_header)
                    stack_header = str(tag_number)
                    edges.append(((one_before_header, stack_header),
                                  {'label': instruction + ' ' + stack_size,
                                   'color': edge_color,
                                   'id': str(stack_size)}))

                prev_instruction = line
                continue

            if instruction.rstrip() == 'JUMPDEST':
                continue

            if instruction in ['JUMP', 'JUMPI']:
                func_out = 0
                if instruction == 'JUMP':
                    if len(s) > 1 and s[1] == '[out]':
                        func_out = 1
                    stack_size = '-1'
                    stack_sum -= 1

                if instruction == 'JUMPI':
                    stack_size = '-2'
                    stack_sum -= 2

                one_before_header = str(stack_header)
                stack_header = str(idx)
                edge_color = 'blue'
                edges.append(((one_before_header, stack_header),
                              {'label': instruction + ' ' + stack_size,
                               'color': edge_color,
                               'id': str(stack_size)}))

                if prev_instruction.strip().split(' ')[0] == 'PUSH' and not func_out:
                    nodes.append((stack_header,
                                  {'label': line,
                                   'id': '-1'}))
                    tag_number = int(prev_instruction.split(' ')[2])
                    jump_from = str(stack_header)
                    jump_to = str(tag_number + 100000)
                    edges.append(((jump_from, jump_to),
                                  {'label': '',
                                   'color': edge_color,
                                   'id': '0'}))

                prev_instruction = line
                continue

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

            if 'LOG' in instruction:
                edge_color = 'red'
                log_number = instruction.split('LOG')[1]
                stack_size = '-' + str(int(log_number) + 2)
                stack_sum -= int(stack_size)

            one_before_header = str(stack_header)
            stack_header = str(idx)
            nodes.append((stack_header,
                          {'label': line + ' ' + str(stack_sum),
                           'id': '-1'}))
            edges.append(((one_before_header, stack_header),
                          {'label': instruction + ' ' + stack_size,
                           'color': edge_color,
                           'id': str(stack_size)}))
            prev_instruction = line
    print(' ---> Control Flow Graph Constructed')


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
