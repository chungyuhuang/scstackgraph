from collections import deque
from modules import dbconnect as db
import sys
import graphviz as gv
import functools
import argparse
import re
import time
import os


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
            print('\n ---> Analyzing contract id {}'.format(row_id))
            assembly_code = i[2]

            filename = 'sourcecode'
            w = open(filename, 'w')
            w.write(assembly_code)
            w.close()

            start_time = time.time()
            print('\t---> Start checking contract {}'.format(contract_addr))
            result = asm_analysis(row_id)

            duration = time.time() - start_time
            m, s = divmod(duration, 60)
            h, m = divmod(m, 60)
            print('\t--- Time using: {:2.0f}h{:2.0f}m{:2.0f}s'.format(h, m, s))

            if result:
                print('\t---> Positive Cycle Found: [Yes] {}'.format(result))
            else:
                print('\t---> Positive Cycle Found: [No] {}'.format(result))

            # db.update_analysis_result_to_db('CFG_CONSTRUCTED', result, row_id)
    elif args.i:
        filename = args.i
        code_preproc(filename)
        result = asm_analysis()
        if result:
            print('\t---> Positive Cycle Found: [Yes]')
        else:
            print('\t---> Positive Cycle Found: [No]')
    else:
        print('Must use an argument, -i for individual source code, -f use source code from DB')
        sys.exit(0)


def asm_analysis(row_id=0):
    filename = 'sourcecode'
    code_preproc(filename)

    nodes = []
    edges = []

    node_list, edge_list = init_graph(nodes, edges)

    # list with all the nodes without input edge
    graph_head = find_graph_head(node_list, edge_list)

    ana_result, cycle_nodes, cycle_count = count_stack_size(nodes, edges, graph_head)

    if cycle_count > 0:
        cycle_nodes_list, cycle_edges = cycle_graph(cycle_nodes, nodes, edges, row_id)
        create_graph(cycle_nodes_list, cycle_edges, row_id)
        mapping_to_sourcecode(cycle_nodes_list, row_id)

    return ana_result


def code_preproc(filename):
    f_op = os.path.join(os.path.dirname(__file__), 'opcode')
    f_op_tmp = os.path.join(os.path.dirname(__file__), 'opcode_tmp')
    f_src = os.path.join(os.path.dirname(__file__), filename)

    w = open(f_op, 'w')
    w2 = open(f_op_tmp, 'w')

    with open(f_src, 'r') as f:
        is_data = 0
        for idx, line in enumerate(f):
            is_tag = 0
            new_line = line.replace('\t', ' ').split(' ')
            if new_line[0].rstrip() == '.data':
                is_data = 1
                continue
            if is_data:
                if len(new_line) > 8:
                    if new_line[4].rstrip() == 'tag':
                        is_tag = 1
                    if new_line[6].rstrip().strip() == 'REVERT':
                        continue
                    else:
                        if is_tag:
                            w.write(new_line[4].rstrip().strip() + ' '
                                    + new_line[5].rstrip().strip() + '\n')
                            for l in range(4, len(new_line)):
                                w2.write(new_line[l].rstrip().strip() + ' ')
                            w2.write('\n')
                        elif new_line[6] != '':
                            w.write(new_line[6].rstrip().strip() + ' '
                                    + new_line[7].rstrip().strip() + ' '
                                    + new_line[8].rstrip().strip() + '\n')
                            for l in range(6, len(new_line)):
                                w2.write(new_line[l].rstrip().strip() + ' ')
                            w2.write('\n')
    w.close()
    w2.close()


def init_graph(nodes, edges):
    print('\t>>> Initiating Control Flow Graph')

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

    f_op = os.path.join(os.path.dirname(__file__), 'opcode')

    with open(f_op, 'r') as f:
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
                              {'label': str(idx) + ' JUMPDEST ' + tag_number,
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
                    stack_size = '0'
                    one_before_header = str(stack_header)
                    stack_header = str(tag_number)
                    edges.append(((one_before_header, stack_header),
                                  {'label': str(idx) + ' ' + instruction + ' ' + stack_size,
                                   'color': edge_color,
                                   'id': stack_size}))

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
                              {'label': str(idx) + ' ' + instruction + ' ' + stack_size,
                               'color': edge_color,
                               'id': stack_size}))

                if prev_instruction.strip().split(' ')[0] == 'PUSH' and not func_out:
                    nodes.append((stack_header,
                                  {'label': str(idx) + ' ' + line,
                                   'id': '-1'}))
                    tag_number = int(prev_instruction.split(' ')[2])
                    jump_from = str(stack_header)
                    jump_to = str(tag_number + 100000)
                    edges.append(((jump_from, jump_to),
                                  {'label': str(idx) + ' ',
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
                          {'label': str(idx) + ' ' + line,
                           'id': '-1'}))
            edges.append(((one_before_header, stack_header),
                          {'label': str(idx) + ' ' + instruction + ' ' + stack_size,
                           'color': edge_color,
                           'id': str(stack_size)}))
            prev_instruction = line
    print('\t\t<<< Control Flow Graph Constructed')

    node_list = []
    edge_list = []

    for n in nodes:
        node_idx = n[0]
        node_list.append(node_idx)
    for e in edges:
        edge_idx = e[0][1]
        edge_list.append(edge_idx)

    print('\t--- {} nodes, {} edges'.format(len(node_list), len(edge_list)))

    return node_list, edge_list


def find_graph_head(node_list, edge_list):
    head_list = []

    for idx, n in enumerate(node_list):
        if n not in edge_list:
            head_list.append((n, idx))

    print('\t--- Total {} graph(s) constructed'.format(len(head_list)))

    return head_list


def count_stack_size(nodes, edges, graph_head):
    count = 0
    check_result = 0
    cycle_count = 0
    cycle_nodes = []
    queue = deque([])

    for start_node in graph_head:
        start_node_idx = start_node[1]
        queue.append(nodes[start_node_idx])

    print('\t>>> Checking CFG ', end='')

    while len(queue):
        if count % 1000 == 0:
            print('.', end='')
            sys.stdout.flush()

        count += 1
        father_node = queue.popleft()
        # print('\nfather node = ', father_node)
        f_idx = father_node[0]
        f_id = father_node[1].get('id')

        for e in edges:
            edge_relation = e[0]
            edge_from = edge_relation[0]
            edge_to = edge_relation[1]
            edge_weight = e[1].get('id')

            if edge_from == f_idx:
                # print('edge = ', e)
                for n in nodes:
                    child_idx = n[0]
                    if edge_to == child_idx:
                        n_label_idx = n[1].get('label').split(' ')
                        # print('child node = ', n)
                        c_id = n[1].get('id')
                        # print(f_id, edge_weight, c_id)
                        if int(f_id) + int(edge_weight) > int(c_id):
                            child_node_info = n[1]
                            if int(c_id) > 0 \
                                    and int(child_idx) > 100000 \
                                    and 'JUMP' in father_node[1].get('label')\
                                    and father_node[1].get('label').rstrip().split()[1] != 'JUMPDEST':
                                if int(f_idx) > int(n_label_idx[0]):
                                    cycle_nodes.append((father_node, n))
                                    cycle_count += 1
                                    check_result = 1
                                    child_node_info['id'] = str(int(f_id) + int(edge_weight))
                                    break
                            else:
                                child_node_info['id'] = str(int(f_id) + int(edge_weight))
                                queue.appendleft(n)
                                break
        # print('queue = ', queue)
    print('\n\t\t<<< Done, Found {} cycle(s) from assembly code'.format(cycle_count))

    return check_result, cycle_nodes, cycle_count


def cycle_graph(cycle_nodes, nodes, edges, row_id):
    cycle_nodes_list = []
    cycle_edges = []

    for cn in cycle_nodes:
        start_node_label = cn[1][0]
        end_node_label = cn[0][0]
        real_start = start_node_label
        for n in nodes:
            n_label = n[0]
            if n_label == start_node_label:
                cycle_nodes_list.append(n)
                start_node_idx = n[1].get('label').rstrip().split(' ')[0]
                for e in edges:
                    e_from = e[0][0]
                    e_to = e[0][1]
                    if e_from == end_node_label and e_to == real_start:
                            cycle_edges.append(e)
                            break
                    if start_node_label == e_from:
                        tag_idx = e[1].get('label').rstrip().split(' ')
                        if len(tag_idx) > 1:
                            if tag_idx[1] == 'tag':
                                e_to_idx = tag_idx[0]
                            else:
                                e_to_idx = e[0][1]
                        else:
                            e_to_idx = e[0][1]
                        if int(e_to_idx) - int(start_node_idx) < 3:
                            cycle_edges.append(e)
                            start_node_label = e_to
                            break
                        else:
                            continue

    return cycle_nodes_list, cycle_edges


def mapping_to_sourcecode(cycle_nodes, row_id):
    print('\t>>> Mapping cycle node to source code')
    f_op_tmp = os.path.join(os.path.dirname(__file__), 'opcode_tmp')
    f_src_tmp = os.path.join(os.path.dirname(__file__), 'img/{}/cycle_src_{}.txt'.format(row_id, row_id))

    w = open(f_src_tmp, 'w')

    with open(f_op_tmp, 'r') as f:
        for idx, line in enumerate(f):
            for n in cycle_nodes:
                n_label = n[1].get('label').rstrip().split(' ')
                if int(n_label[0]) == idx:
                    src = line.rstrip().split('  ')
                    w.write(src[-1].strip() + '\n')
                    break
    w.close()
    print('\t\t<<< Finishing mapping')


def create_graph(n, e, row_id):
    print('\t>>> Visualizing graph')
    digraph = functools.partial(gv.Digraph, format='svg')
    g1 = add_edges(add_nodes(digraph(), n), e)
    filename = 'img/{}/g{}'.format(row_id, row_id)
    g1.render(filename=filename)
    print('\t\t<<< Visualize graph constructed')


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