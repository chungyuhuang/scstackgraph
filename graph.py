import graphviz as gv
import functools
import sys


def main():
    init_graph()


def init_graph():
    stack_push_one = ['PUSH', 'DUP', 'JUMPDEST', 'MLOAD', 'CALLER', 'CALLVALUE', 'GAS']
    stack_pop_one = ['POP', 'LT', 'GT', 'EQ', 'AND', 'OR', 'XOR', 'ADD', 'SUB', 'MUL', 'DIV', 'EXP']
    stack_pop_two = ['MSTORE', 'SSTORE']
    stack_unchange =['SWAP', 'NOT', 'ISZERO', 'EXTCODESIZE']

    nodes = []
    edges = []
    push_value_list = []

    stack_header = '0'
    one_before_header = '[-1]'
    two_before_header = '[-2]'
    stack_size = 0

    with open('test', 'r') as f:
        for line in f:
            s = line.rstrip().split(' ')
            node_label = str(s[1])
            if node_label == 'JUMPDEST':
                nodes.append((str(s[0]), {'label': 'JUMPDEST' + s[0]}))
    with open('test', 'r') as f:
        for idx, line in enumerate(f):
            s = line.rstrip().split(' ')
            node_label = str(s[0])
            instruction = s[1]
            if len(s) == 3:
                if s[2] == 'Opcode)':
                    continue
                else:
                    num = int(s[2], 16)
                    push_value_list.append(num)
            for key_world in stack_push_one:
                if key_world in instruction:
                    if key_world == 'JUMPDEST':
                        edges.append(((stack_header, node_label),
                                      {'label': 'step' + str(idx + 1) + instruction}))
                    else:
                        two_before_header = one_before_header
                        one_before_header = stack_header
                        stack_header = node_label
                        stack_size += 1
                    # label_list.append(stack_header)
                        # print(nodes[-1])
                    # if nodes[-1] == stack_header | len(nodes) == 0:
                        nodes.append((stack_header, {'label': str(stack_size)}))
                        edges.append(((one_before_header, stack_header),
                                      {'label': 'step' + str(idx + 1) + instruction, 'color': 'red'}))
                    break
            for key_world in stack_pop_two:
                if key_world in instruction:
                    # index_of_header = label_list.index(one_before_header)
                    tmp = one_before_header
                    # if len(nodes) < 4:
                    #     one_before_header = '[-1]'
                    # else:
                    one_before_header = stack_header
                    stack_header = two_before_header
                    two_before_header = tmp
                    edges.append(((one_before_header, two_before_header),
                                  {'label': 'step' + str(idx + 1) + instruction}))
                    stack_size -= 2
                    break
            for key_world in stack_pop_one:
                if key_world in instruction:
                    if instruction.rstrip() != 'SSTORE':
                        if instruction.rstrip() != 'JUMPI':
                            if instruction.rstrip() != 'JUMPDEST':
                                two_before_header = one_before_header
                                one_before_header = stack_header
                                stack_header = two_before_header
                                edges.append(((one_before_header, stack_header),
                                              {'label': 'step' + str(idx + 1) + instruction,
                                               'color': 'green'}))
                                # stack_header = one_before_header
                                # if len(nodes) < 4:
                                #     one_before_header = '[-1]'
                                # else:
                                #     one_before_header = nodes[-3][0]
                                stack_size -= 1
                                break
            for key_world in stack_unchange:
                if key_world in instruction:
                    # print('no change ', instruction)
                    # two_before_header = one_before_header
                    # one_before_header = stack_header
                    edges.append(((stack_header, stack_header),
                                  {'label': 'step' + str(idx + 1) + instruction}))
                    break
            if s[1] in ['JUMP', 'JUMPI']:
                jump_from = stack_header
                jump_to = '[' + str(push_value_list[-1]) + ']'
                edges.append(((jump_from, jump_to), {'label': 'step' + str(idx + 1) + instruction}))
    print(push_value_list)
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
    print('nodes = ', nodes)
    for n in nodes:
        if isinstance(n, tuple):
            graph.node(n[0], **n[1])
        else:
            graph.node(n)
    return graph


def add_edges(graph, edges):
    print('edges = ', edges)
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
