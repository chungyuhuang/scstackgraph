from collections import deque
from modules import dbconnect as db
from gas_price import *
import sys
import graphviz as gv
import functools
import argparse
import re
import time
import os
import math


nodes = []
edges = []


def main():
    # n = [('jp1', {'label': 'HEAD', 'weight': '-1'}),
    #      ('PUSH60', {'label': 'PUSH60', 'weight': '-1'}),
    #      ('PUSH40', {'label': 'PUSH40', 'weight': '-1'}),
    #      ('MSTORE', {'label': 'MSTORE', 'weight': '-1'}),
    #      ('PUSH4', {'label': 'PUSH4', 'weight': '-1'}),
    #      ('calldatasize', {'label': 'CALLDATASIZE', 'weight': '-1'}),
    #      ('LT', {'label': 'LT', 'weight': '-1'}),
    #      ('PUSH1', {'label': 'PUSH tag1', 'weight': '-1'}),
    #      ('JUMPI', {'label': 'JUMPI', 'weight': '-1'}),
    #      ('PUSH0', {'label': 'PUSH0', 'weight': '-1'}),
    #      ('calldataload', {'label': 'CALLDATALOAD', 'weight': '-1'}),
    #      ('PUSH100', {'label': 'PUSH 100...', 'weight': '-1'}),
    #      ('SWAP1', {'label': 'SWAP1', 'weight': '-1'}),
    #      ('DIV', {'label': 'DIV', 'weight': '-1'}),
    #      ('PUSHF', {'label': 'PUSH FFF...', 'weight': '-1'}),
    #      ('AND', {'label': 'AND', 'weight': '-1'}),
    #      ('DUP1', {'label': 'DUP1', 'weight': '-1'}),
    #      ('PUSH72', {'label': 'PUSH 72EA4B8C', 'weight': '-1'}),
    #      ('EQ', {'label': 'EQ', 'weight': '-1'}),
    #      ('PUSH2', {'label': 'PUSH tag2', 'weight': '-1'}),
    #      ('JUMPI2', {'label': 'JUMPI', 'weight': '-1'}),
    #      ('JUMPDEST1', {'label': 'JUMPDEST', 'weight': '-1'}),
    #
    #      ]
    #
    # e = [(('jp1', 'PUSH60'), {'label': '+1'}),
    #      (('PUSH60', 'PUSH40'), {'label': '+1'}),
    #      (('PUSH40', 'MSTORE'), {'label': '-2'}),
    #      (('MSTORE', 'PUSH4'), {'label': '+1'}),
    #      (('PUSH4', 'calldatasize'), {'label': '+1'}),
    #      (('calldatasize', 'LT'), {'label': '-1'}),
    #      (('LT', 'PUSH1'), {'label': '+1'}),
    #      (('PUSH1', 'JUMPI'), {'label': '-2'}),
    #      (('JUMPI', 'PUSH0'), {'label': '+1'}),
    #     (('JUMPI', 'JUMPDEST1'), {'label': '0'}),
    #      (('PUSH0', 'calldataload'), {'label': '0'}),
    #      (('calldataload', 'PUSH100'), {'label': '+1'}),
    #      (('PUSH100', 'SWAP1'), {'label': '0'}),
    #      (('SWAP1', 'DIV'), {'label': '-1'}),
    #      (('DIV', 'PUSHF'), {'label': '0'}),
    #      (('PUSHF', 'AND'), {'label': '+1'}),
    #      (('AND', 'DUP1'), {'label': '+1'}),
    #      (('DUP1', 'PUSH72'), {'label': '+1'}),
    #      (('PUSH72', 'EQ'), {'label': '-1'}),
    #      (('EQ', 'PUSH2'), {'label': '+1'}),
    #      (('PUSH2', 'JUMPI2'), {'label': '-2'}),
    #      (('JUMPI2', 'JUMPDEST1'), {'label': '0'}),
    #      ]
    # create_graph(n,e,123)
    generate_s_e_t()


def generate_s_e_t():
    opcode_with_formula = ['EXP', 'SHA3', 'CALLDATACOPY', 'CODECOPY', 'EXTCODECOPY', 'SSTORE', 'CALLCODE',
                           'DELEGATECALL', 'SELFDESTRUCT', 'LOG0', 'LOG1', 'LOG2', 'LOG3', 'LOG4', 'KECCAK']
    head = '0'
    gas_total = 0
    f_tmp = os.path.join(os.path.dirname(__file__), 'opcode')
    with open(f_tmp, 'r') as f:
        for idx, line in enumerate(f):
            instruction = line.rstrip().split('  ')[0].strip()
            s = instruction.rstrip().split(' ')
            t = re.sub(r'\d+', '', str(s[0]))
            if t == 'tag':
                continue
            elif t in opcode_with_formula:
                print(t)
                nodes.append((head,
                              {'label': 'gas: ' + str(gas_total),
                               'id': '0',
                               'shape': 'box'
                               }))
                head = opcode_formula(t, idx, head)
                gas_total = 0
            else:
                for g in gas_table:
                    if t == g:
                        gas_total += gas_table[g]
                        # head = str(idx)
    nodes.append((head,
                  {'label': 'gas: ' + str(gas_total),
                   'id': '0',
                   'shape': 'box'
                   }))
    create_graph(nodes, edges, 'test000')


def opcode_formula(op, idx, head):
    if op == 'EXP':
        nodes.append((str(idx),
                      {'label': 'exp == 0',
                       'id': '0',
                       'shape': 'diamond',
                       'color': 'yellow',
                       'style': 'filled'
                       }))
        nodes.append((str(idx) + 'exp1',
                      {'label': '10',
                       'id': '0',
                       'shape': 'box',
                       'color': 'yellow',
                       'style': 'filled'
                       }))
        nodes.append((str(idx) + 'exp2',
                      {'label': '10+(10*(1+log256(xy)))',
                       'id': '0',
                       'shape': 'box',
                       'color': 'yellow',
                       'style': 'filled'
                       }))
        edges.append(((head, str(idx)),
                      {'label': 'EXP',
                       'color': 'blue',
                       'id': '0'}))
        edges.append(((str(idx), str(idx) + 'exp1'),
                      {'label': 'exp = 0',
                       'color': 'blue',
                       'id': '0'}))
        edges.append(((str(idx) + 'exp1', str(int(head)+2)),
                      {'label': '',
                       'color': 'blue',
                       'id': '0'}))
        edges.append(((str(idx), str(idx) + 'exp2'),
                      {'label': 'exp != 0',
                       'color': 'blue',
                       'id': '0'}))
        edges.append(((str(idx) + 'exp2', str(int(head)+2)),
                      {'label': '',
                       'color': 'blue',
                       'id': '0'}))
        return str(int(head)+2)
    if op == 'SSTORE':
        nodes.append((str(idx),
                      {'label': 'x{} == 0 && y{}!= 0'.format(str(idx), str(idx)),
                       'id': '0',
                       'shape': 'diamond',
                       'color': 'yellow',
                       'style': 'filled'
                       }))
        nodes.append((str(idx) + 'sstore1',
                      {'label': '20000',
                       'id': '0',
                       'shape': 'box',
                       'color': 'yellow',
                       'style': 'filled'
                       }))
        nodes.append((str(idx) + 'sstore2',
                      {'label': '5000',
                       'id': '0',
                       'shape': 'box',
                       'color': 'yellow',
                       'style': 'filled'
                       }))
        edges.append(((head, str(idx)),
                      {'label': 'SSTORE',
                       'color': 'blue',
                       'id': '0'}))
        edges.append(((str(idx), str(idx) + 'sstore1'),
                      {'label': 'x{} == 0 && y{}!= 0'.format(str(idx), str(idx)),
                       'color': 'blue',
                       'id': '0'}))
        edges.append(((str(idx) + 'sstore1', str(int(head)+2)),
                      {'label': '',
                       'color': 'blue',
                       'id': '0'}))
        edges.append(((str(idx), str(idx) + 'sstore2'),
                      {'label': 'x{} != 0 || y{} == 0'.format(str(idx), str(idx)),
                       'color': 'blue',
                       'id': '0'}))
        edges.append(((str(idx) + 'sstore2', str(int(head)+2)),
                      {'label': '',
                       'color': 'blue',
                       'id': '0'}))
        return str(int(head)+2)
    if op == 'KECCAK':
        nodes.append((str(idx),
                      {'label': op + ': 30 + 6y',
                       'id': '0',
                       'shape': 'box',
                       'color': 'green',
                       'style': 'filled'
                       }))
        edges.append(((head, str(idx)),
                      {'label': '',
                       'id': '0'}))
        edges.append(((str(idx), str(int(head)+1)),
                      {'label': '',
                       'id': '0'}))
        return str(int(head)+1)


def create_graph(n, e, row_id):
    print('==> Visualizing graph')
    digraph = functools.partial(gv.Digraph, format='svg')
    g = add_edges(add_nodes(digraph(), n), e)
    filename = 'img/{}/g{}'.format(row_id, row_id)
    g.render(filename=filename)
    print('\t[Visualize graph constructed]')

    return g


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


if __name__ == '__main__':
    main()
