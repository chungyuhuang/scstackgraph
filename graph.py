import graphviz as gv
import functools
from collections import deque


def main():
    nodes = []
    edges = []
    init_graph(nodes, edges)
    print(nodes)
    print(edges)
    count_stack_size(nodes, edges)


def count_stack_size(nodes, edges):
    queue = deque([])
    start_idx = 0

    for idx, n in enumerate(nodes):
        find_jump_des = n[1].get('label').split(' ')
        if find_jump_des[0] != 'JUMPDEST':
            start_idx = idx
            break
    start_node = nodes[start_idx]
    start_node[1]['id'] = 0
    queue.append(start_node)
    while len(queue):
        father_node = queue.popleft()
        print('\nfather node = ', father_node)
        f_label = father_node[0]
        f_id = father_node[1].get('id')
        for e in edges:
            is_jumpdest = 0
            edge_relation = e[0]
            edge_from = edge_relation[0]
            edge_to = edge_relation[1]
            edge_weight = e[1].get('id')
            if edge_from == f_label:
                print('edge = ', e)
                for n in nodes:
                    if n[0] == edge_to:
                        n_label_name = n[1].get('label').split(' ')
                        print('child node = ', n)
                        c_id = n[1].get('id')
                        print(f_id, edge_weight, c_id)
                        if int(f_id) + int(edge_weight) > int(c_id):
                            child_node = n[1]
                            child_node['id'] = int(f_id) + int(edge_weight)
                            check_c_id = child_node.get('id')
                            print(check_c_id)
                            if int(check_c_id) > 1024:
                                break
                            else:
                                queue.append(n)
                        if n_label_name[0] == 'JUMPDEST':
                            is_jumpdest = 1
                            continue
                        else:
                            is_jumpdest = 0
                            break
                if is_jumpdest:
                    continue
                else:
                    break
        print('queue = ', queue)
    print(nodes)


def init_graph(nodes, edges):
    stack_push_one = ['PUSH', 'DUP', 'MLOAD', 'CALLER', 'CALLVALUE', 'GAS']
    stack_pop_one = ['POP', 'LT', 'GT', 'EQ', 'AND', 'OR', 'XOR', 'ADD', 'SUB', 'MUL', 'DIV', 'EXP']
    stack_pop_two = ['MSTORE', 'SSTORE']
    stack_unchange = ['SWAP', 'JUMPDEST', 'SLOAD', 'NOT', 'ISZERO', 'CALLDATALOAD', 'EXTCODESIZE', 'STOP']

    push_value_list = []

    stack_header = '0'
    stack_size = '0'
    stack_sum = 0
    edge_color = 'black'
    prev_instruction = '0'

    with open('test4', 'r') as f:
        for line in f:
            s = line.rstrip().split(' ')
            node_label = str(s[1])
            if node_label == 'JUMPDEST':
                nodes.append((str(s[0]),
                              {'label': 'JUMPDEST ' + s[0],
                               'id': '-1'}))
    with open('test4', 'r') as f:
        for idx, line in enumerate(f):
            s = line.rstrip().split(' ')
            node_header = str(s[0])
            instruction = s[1].strip()
            if len(s) == 3:
                if s[2] == 'Opcode)':
                    continue
                else:
                    num = int(s[2], 16)
                    push_value_list.append(num)
            if prev_instruction == 'JUMP' and instruction == 'JUMPDEST':
                stack_header = node_header
                continue
            if instruction in ['JUMP', 'JUMPI']:
                if instruction == 'JUMP':
                    stack_size = '-1'
                    stack_sum -= 1
                if instruction == 'JUMPI':
                    stack_size = '-2'
                    stack_sum -= 2
                one_before_header = stack_header
                stack_header = node_header
                nodes.append((stack_header,
                              {'label': str(stack_sum),
                               'id': '-1'}))
                jump_from = stack_header
                jump_to = '[' + str(push_value_list[-1]) + ']'
                edge_color = 'blue'
                edges.append(((one_before_header, stack_header),
                              {'label': s[0] + ' ' + instruction + ' ' + stack_size,
                               'color': edge_color,
                               'id': str(stack_size)}))
                edges.append(((jump_from, jump_to),
                              {'label': '0',
                               'color': edge_color,
                               'id': '0'}))
                prev_instruction = instruction
                continue
            for key_world in stack_push_one:
                if key_world in instruction:
                    edge_color = 'red'
                    stack_size = '+1'
                    stack_sum += 1
                    break
            for key_world in stack_pop_two:
                if key_world in instruction:
                    edge_color = 'orange'
                    stack_size = '-2'
                    stack_sum -= 2
                    break
            for key_world in stack_pop_one:
                if key_world in instruction:
                    if instruction.rstrip() != 'MSTORE':
                        if instruction.rstrip() != 'SSTORE':
                            if instruction.rstrip() != 'JUMPI':
                                if instruction.rstrip() != 'JUMPDEST':
                                    edge_color = 'green'
                                    stack_size = '-1'
                                    stack_sum -= 1
                                    break
            for key_world in stack_unchange:
                if key_world in instruction:
                    edge_color = 'brown'
                    stack_size = '+0'
                    break
            if instruction == 'CALL':
                edge_color = 'purple'
                stack_size = '-6'
                stack_sum -= 6
            one_before_header = stack_header
            stack_header = node_header
            nodes.append((stack_header,
                          {'label': str(stack_sum),
                           'id': '-1'}))
            edges.append(((one_before_header, stack_header),
                          {'label': s[0] + ' ' + instruction + ' ' + stack_size,
                           'color': edge_color,
                           'id': str(stack_size)}))
            prev_instruction = instruction
    # print(push_value_list)
    create_graph(nodes, edges)


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

    g1.render(filename='img/g1')


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
