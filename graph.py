import graphviz as gv
import functools


def main():
    init_graph()


def init_graph():
    stack_push_one = ['PUSH', 'DUP', 'MLOAD', 'CALLER', 'CALLVALUE', 'GAS']
    stack_pop_one = ['POP', 'LT', 'GT', 'EQ', 'AND', 'OR', 'XOR', 'ADD', 'SUB', 'MUL', 'DIV', 'EXP']
    stack_pop_two = ['MSTORE', 'SSTORE', 'SLOAD']
    stack_unchange =['SWAP', 'JUMPDEST', 'NOT', 'ISZERO', 'EXTCODESIZE']

    nodes = []
    edges = []
    push_value_list = []

    stack_header = '0'
    stack_size = '0'
    edge_color = 'black'

    with open('test', 'r') as f:
        for line in f:
            s = line.rstrip().split(' ')
            node_label = str(s[1])
            if node_label == 'JUMPDEST':
                nodes.append((str(s[0]), {'label': 'JUMPDEST' + s[0]}))
    with open('test', 'r') as f:
        for idx, line in enumerate(f):
            s = line.rstrip().split(' ')
            node_header = str(s[0])
            instruction = s[1].strip()
            # print(instruction)
            if len(s) == 3:
                if s[2] == 'Opcode)':
                    continue
                else:
                    num = int(s[2], 16)
                    push_value_list.append(num)
            if s[1] in ['JUMP', 'JUMPI']:
                print(s[1])
                jump_from = stack_header
                jump_to = '[' + str(push_value_list[-1]) + ']'
                edge_color = 'blue'
                if s[1] == 'JUMP':
                    stack_size = '-1'
                else:
                    stack_size = '-2'
                edges.append(((jump_from, jump_to),
                              {'label': 'step ' + str(idx + 1) + ' ' + instruction + '\nstack size ' + stack_size,
                               'color': edge_color}))
                continue
            for key_world in stack_push_one:
                if key_world in instruction:
                    edge_color = 'red'
                    stack_size = '+1'
                    break
            for key_world in stack_pop_two:
                if key_world in instruction:
                    edge_color = 'orange'
                    stack_size = '-2'
                    break
            for key_world in stack_pop_one:
                if key_world in instruction:
                    if instruction.rstrip() != 'SSTORE':
                        if instruction.rstrip() != 'JUMPI':
                            if instruction.rstrip() != 'JUMPDEST':
                                edge_color = 'green'
                                stack_size = '-1'
                                break
            for key_world in stack_unchange:
                if key_world in instruction:
                    edge_color = 'brown'
                    stack_size = '+0'
                    break
            one_before_header = stack_header
            stack_header = node_header
            nodes.append(stack_header)
            edges.append(((one_before_header, stack_header),
                          {'label': 'step ' + str(idx + 1) + ' ' + instruction + '\nstack size ' + stack_size,
                           'color': edge_color}))
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
