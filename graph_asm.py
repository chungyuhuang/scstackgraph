from collections import deque
from modules import dbconnect as db
from gas_price import *
from opcode_table import *
import se_ins as se
import sys
import graphviz as gv
import functools
import argparse
import re
import time
import os
import math
from subprocess import check_output, call
import json

f_SE = os.path.join(os.path.dirname(__file__), 'SE')
wSE = open(f_SE, 'w')
# c2c = False
loop_graph_count = 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--i", help="input file name", action='store_true')
    parser.add_argument("-f", "--f", help="read from DB", action='store_true')
    parser.add_argument("-t", "--t", help="testing", action='store_true')
    parser.add_argument("-code", "--code", help="source code")

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
            print('\t [Time using: {:2.0f}h{:2.0f}m{:2.0f}s]'.format(h, m, s))

            if result:
                print(' ---> Positive Cycle Found: [Yes] {}'.format(result))
            else:
                print(' ---> Positive Cycle Found: [No] {}'.format(result))
    elif args.i:
        # filename = args.i
        # code_preproc(filename)
        # db.ready_contract_count('assembly', 'CFG_CONSTRUCTED')
        cur = db.load_assembly_from_db('assembly', 'CFG_CONSTRUCTED')
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
            print('\t [Time using: {:2.0f}h{:2.0f}m{:2.0f}s]'.format(h, m, s))

        if result:
            print(' ---> Positive Cycle Found: [Yes]')
        else:
            print(' ---> Positive Cycle Found: [No]')
    elif args.t:
        asm_analysis(args.code, 0, test_mode=1)
    else:
        print('Must use an argument, -i for individual source code, -f use source code from DB')
    #     sys.exit(0)


def asm_analysis(code, row_id=0, test_mode=0):
    filename = 'sourcecode'
    # fh = stack_status(code)

    preproc(code)

    # code_preproc(filename)

    # db.update_opcode_to_db(op, row_id, test_mode)

    nodes = []
    edges = []
    f_op = os.path.join(os.path.dirname(__file__), 'opcode')

    nodes, edges, is_end = cfg_construction(f_op, nodes, edges, 0)
    create_graph(nodes, edges, 'cfg_full_contract')

    cycle_detection(nodes, edges)

    # f_inputs = stack_status(inputs, binrun, funchash, funcname)
    #
    # if f_inputs != 0:
    #     stack = []
    #     storage = []
    #     memory = []
    #     f_con = []
    #     t_con = []
    #     stack_status_constraint(stack, storage, memory, c_nodes, c_edges, '0', f_inputs, f_con, t_con, 0, 0, 0)

    # src_text, op_text = mapping_to_sourcecode(c_nodes, row_id)
    # print(src_text, op_text)

    # nodes, edges, node_list, edge_list, gas_total = init_graph([], [])
    # # # print(gas_total)
    # # # # g = create_graph(nodes, edges, row_id)
    # # # # # list with all the nodes without input edge
    # graph_head = find_graph_head(node_list, edge_list)
    # # #
    # ana_result, cycle_nodes, cycle_count = count_stack_size(nodes, edges, graph_head)

    # # # db.update_analysis_result_to_db('CFG_CONSTRUCTED', ana_result, row_id, test_mode)
    # # #
    # if cycle_count > 0:
    #     # condition_node = trace_condition(cycle_nodes)
    #     cycle_nodes_list, cycle_edges = cycle_graph(cycle_nodes, nodes, edges)
    #     g = create_graph(cycle_nodes_list, cycle_edges, row_id)

    #     # gas_total = cal_loop_gas()
    #     # for n in condition_node:
    #     #     db.update_condition_info_to_db(row_id, test_mode, gas_total, *n)
    #     # # op_with_src = op_with_src.replace("'", "''")
    #     # # cycle_info = [g, src_text, op_text, len(graph_head), len(node_list), len(edge_list), cycle_count, op_with_src]
    # #     # # db.update_cycle_info_to_db(row_id, test_mode, *cycle_info)

    return 0  #ana_result


def preproc(src):

    f_asm_json = ''
    f_src = os.path.join(os.path.dirname(__file__), src)

    f_op = os.path.join(os.path.dirname(__file__), 'opcode')
    f_op_pre = os.path.join(os.path.dirname(__file__), 'opcode_pre')

    try:
        # w = open(f_asm_json, 'w')
        print('\n[INFO] Empty the directory.')
        call(['rm', '-f', './output/*'])
    except Exception as ex:
        print('Error: ', ex)

    try:
        # w = open(f_asm_json, 'w')
        print('\n[INFO] Source code to assembly.')
        call(['solc', '--asm-json', '-o', './output', '--overwrite', f_src])
    except Exception as ex:
        print('Error: ', ex)

    for file in os.listdir("./output"):
        if file.endswith(".json"):
            f_asm_json = os.path.join("./output", file)
            print(f_asm_json)

            try:
                with open(f_asm_json, 'r') as fh:
                    opcode_file = json.load(fh)
                    for key, val in opcode_file.items():
                        if key == '.code':
                            w_pre = open(f_op_pre, 'w')
                            for ins_content in val:
                                instruction = ''
                                value = ''
                                for key1, val1 in ins_content.items():
                                    if key1 == 'value':
                                        value = val1
                                    if key1 == 'name':
                                        instruction = val1
                                instruction = instruction + ' ' + value + '\n'
                                w_pre.write(instruction)
                        elif key == '.data':
                            for key1, val1 in val.items():
                                if key1 == '0':
                                    for key2, val2 in val1.items():
                                        if key2 == '.code':
                                            w_op = open(f_op, 'w')
                                            for ins_content in val2:
                                                instruction = ''
                                                value = ''
                                                for key3, val3 in ins_content.items():
                                                    if key3 == 'value':
                                                        value = val3
                                                    if key3 == 'name':
                                                        instruction = val3
                                                instruction = instruction + ' ' + value + '\n'
                                                w_op.write(instruction)
            except Exception as ex:
                print('[Error]: ', ex)


def cfg_construction(read_file, nodes, edges, init_tag_num):

    segment_ins = ['tag', 'JUMP', 'JUMPI', 'STOP', 'REVERT', 'INVALID', 'RETURN'] # , 'CREATE', 'CALL']

    tag_num = 0 + init_tag_num
    jump_tag = 0
    stack_sum = 0
    gas_total = 0
    prev_tag = 0
    node_content = ''
    prev_ins = ''
    gas_constraint = ''
    tag_value = ''
    jump_out_next_tag = ''
    edge_color = 'blue'
    is_end = []
    push_tag_list = []
    from_jumpi = False
    not_out = False
    from_outer = False
    from_jump_out = False

    # f_status = os.path.join(os.path.dirname(__file__), 'ana_status')
    # w = open(f_status, 'w')
    # print(c2c)

    with open(read_file, 'r') as f:
        for idx, line in enumerate(f):
            s = line.rstrip().split(' ')
            for key, value in gas_constraint_table.items():
                if s[0] == key:
                    gas_constraint += gas_constraint_table[key]
            for key, value in gas_table.items():
                if s[0] == key:
                    gas_total += gas_table[key]
            if s[0] in segment_ins:
                if s[0] == 'tag':
                    if node_content == '':
                        tag_num = int(s[1]) + init_tag_num
                        node_content += str(idx) + ': ' + line.rstrip() + '\n'
                    else:
                        node_content += 'Stack Sum: ' + str(stack_sum) + '\n' + 'Gas: ' + str(gas_total) # + ' + [' + gas_constraint + ']'
                        nodes.append((str(tag_num), {'label': node_content, 'shape': 'box'}))
                        node_content = ''
                        if from_jumpi:
                            edges.append(((str(prev_tag), str(tag_num)),
                                          {'label': '',
                                           'color': edge_color}))
                            from_jumpi = False
                            # not_out = True
                        node_content += str(idx) + ': ' + line.rstrip() + '\n'
                        prev_tag = tag_num
                        tag_num = int(s[1]) + init_tag_num
                        edges.append(((str(prev_tag), str(tag_num)),
                                      {'label': '',
                                       'color': 'blue'}))
                        stack_sum = 0
                else:
                    if from_jumpi:
                        edges.append(((str(prev_tag), str(tag_num)),
                                      {'label': '',
                                       'color': edge_color}))
                        from_jumpi = False
                        # not_out = True
                    if s[0] == 'JUMP' and len(s) == 1 and len(prev_ins) > 1:
                        stack_sum -= 1
                        node_content += str(idx) + ': ' + line.rstrip() + '\n' + 'Stack Sum: ' + str(
                            stack_sum) + '\n' + 'Gas: ' + str(gas_total) # + ' + [' + gas_constraint + ']'
                        nodes.append((str(tag_num), {'label': node_content, 'shape': 'box'}))
                        # if from_jump_out:
                        #     jump_tag = int(jump_out_next_tag) + init_tag_num
                        #     from_jump_out = False
                        # else:
                        jump_tag = int(prev_ins[2]) + init_tag_num
                        edges.append(((str(tag_num), str(jump_tag)),
                                      {'label': '',
                                       'color': 'blue'}))
                        node_content = ''
                        not_out = False
                    elif s[0] == 'JUMPI':
                        stack_sum -= 2
                        node_content += str(idx) + ': ' + line.rstrip() + '\n' + 'Stack Sum: ' + str(stack_sum) + '\n' + 'Gas: ' + str(gas_total) # + ' + [' + gas_constraint + ']'
                        nodes.append((str(tag_num), {'label': node_content, 'shape': 'box'}))
                        jump_tag = int(prev_ins[2]) + init_tag_num
                        edges.append(((str(tag_num), str(jump_tag)),
                                      {'label': '',
                                       'color': edge_color}))
                        if from_outer:
                            for i in is_end:
                                edges.append(((str(i), str(tag_num)),
                                              {'label': '',
                                               'color': edge_color}))
                            from_outer = False
                        node_content = ''
                        prev_tag = tag_num
                        from_jumpi = True
                    elif len(s) > 1 and s[0] == 'JUMP' and s[1] == '[in]':
                        stack_sum -= 1
                        node_content += str(idx) + ': ' + line.rstrip() + '\n' + 'Stack Sum: ' + str(stack_sum) + '\n' + 'Gas: ' + str(gas_total)#  + ' + [' + gas_constraint + ']'
                        nodes.append((str(tag_num), {'label': node_content, 'shape': 'box'}))
                        jump_tag = int(push_tag_list[-1]) + init_tag_num
                        edges.append(((str(tag_num), str(jump_tag)),
                                      {'label': str(tag_value),
                                       'color': edge_color}))
                        node_content = ''
                        prev_tag = tag_num
                    elif len(s) > 1 and s[0] == 'JUMP' and s[1] == '[out]':
                        stack_sum -= 1
                        node_content += str(idx) + ': ' + line.rstrip() + '\n' + 'Stack Sum: ' + str(
                            stack_sum) + '\n' + 'Gas: ' + str(gas_total) # + ' + [' + gas_constraint + ']'
                        nodes.append((str(tag_num), {'label': node_content, 'shape': 'box'}))
                        # if not not_out:
                        #     edges.append(((str(tag_num), str(int(tag_num) - 1)),
                        #                   {'label': '',
                        #                    'color': edge_color}))
                        not_out = False
                        from_jump_out = True
                        node_content = ''
                        prev_tag = tag_num
                    # elif s[0] == 'CREATE' or s[0] == 'CALL':
                    #     # # if c2c:
                    #     # from_outer = True
                    #     # node_content += str(idx) + ': ' + line.rstrip() + '\n' + 'Stack Sum: ' + str(
                    #     #     stack_sum) + '\n' + 'Gas: ' + str(gas_total) + ' + [' + gas_constraint + ']'
                    #     # nodes.append((str(tag_num), {'label': node_content, 'shape': 'box'}))
                    #     # node_content = ''
                    #     # if s[0] == 'CREATE':
                    #     #     tmp = opcode['CREATE']
                    #     #     stack_sum += tmp[1] - tmp[0]
                    #     #     f_op_cons = os.path.join(os.path.dirname(__file__), 'opcode_cons')
                    #     #     edges.append(((str(tag_num), str(500)),
                    #     #                   {'label': '',
                    #     #                    'color': edge_color}))
                    #     #     nodes, edges, is_end = cfg_construction(f_op_cons, nodes, edges, 500)
                    #     # if s[0] == 'CALL':
                    #     #     tmp = opcode['CALL']
                    #     #     stack_sum += tmp[1] - tmp[0]
                    #     #     f_op_two = os.path.join(os.path.dirname(__file__), 'opcode_two')
                    #     #     edges.append(((str(tag_num), str(800)),
                    #     #                   {'label': '',
                    #     #                    'color': edge_color}))
                    #     #     nodes, edges, is_end = cfg_construction(f_op_two, nodes, edges, 800)
                    #     # else:
                    #     instruction = re.sub(r'\d+', '', str(s[0]))
                    #     tmp = opcode[instruction]
                    #     stack_sum += tmp[1] - tmp[0]
                    #     node_content += str(idx) + ': ' + line.rstrip() + '\n'
                    #     print(s, tag_num)
                    else:
                        if s[0] in ['REVERT', 'RETURN']:
                            stack_sum -= 2
                            if init_tag_num != 0:
                                is_end.append(tag_num)
                        node_content += str(idx) + ': ' + line.rstrip() + '\n' + 'Stack Sum: ' + str(stack_sum) + '\n' + 'Gas: ' + str(gas_total)#  + ' + [' + gas_constraint + ']'
                        nodes.append((str(tag_num), {'label': node_content, 'shape': 'box'}))
                        node_content = ''
                    if from_outer:
                        tag_num = int(jump_tag) + 100000 + init_tag_num
                    else:
                        tag_num = int(jump_tag) + 10000 + init_tag_num
                    stack_sum = 0
                    gas_total = 0
                    gas_constraint = ''
            else:
                if 'LOG' in s[0]:
                    log_number = s[0].split('LOG')[1]
                    stack_sum -= int(log_number) + 2
                elif 'PUSH' in s and '[tag]' in s:
                    push_tag_list.append(s[2])
                    stack_sum += 1
                else:
                    instruction = re.sub(r'\d+', '', str(s[0]))
                    tmp = opcode[instruction]
                    stack_sum += tmp[1] - tmp[0]

                node_content += str(idx) + ': ' + line.rstrip() + '\n'
            prev_ins = s

    print('cfg node count = ', len(nodes))
    print('cfg edge count = ', len(edges))
    graph_detail(nodes)

    return nodes, edges, is_end


def cycle_detection(nodes, edges):
    # queue = deque([])
    # queue.appendleft(nodes[0])
    # c_nodes = []
    # c_edges = []
    # node_list = [nodes[0][0]]
    # count = 0
    # loop_start_list = []

    visited = []
    rec_stack = []

    start_node = nodes[0]

    dfs_check(start_node, nodes, edges, visited, rec_stack)

    # while len(queue) > 0:
    #     n0 = queue.popleft()
    #     # print("n0 = ", n0)
    #     n0l = n0[0]
    #     # is_loop = False
    #     for e in edges:
    #         fnl = e[0][0]
    #         if fnl == n0l:
    #             cnl = e[0][1]
    #             for n in nodes:
    #                 nl = n[0]
    #                 if nl == cnl:
    #                     if nl in node_list:
    #                         ncontent = n0[1].get('label')
    #                         ncontent = ncontent.split('\n')
    #                         for s in ncontent:
    #                             s = s.split(': ')
    #                             if len(s) > 1:
    #                                 if s[1] == "JUMP":
    #                                     lb = n[1].get('label').split('\n')[1].split(': ')
    #                                     if s[0] > lb[0]:
    #                                         for n2 in nodes:
    #                                             n2l = n2[0]
    #                                             if n2l == str(int(cnl) + 1):
    #                                                 print(cnl)
    #                                                 loop_start_list.append(n2l)
    #                                                 queue.appendleft(n2)
    #                                         print(loop_start_list)
    #                                         count += 1
    #                                         c_nodes, c_edges = loop_graph(n0, nodes, edges, count, loop_start_list)
    #
    #                                     break
    #                     else:
    #                         node_list.append(nl)
    #                     # if 10000 > int(fnl) > int(cnl) or int(fnl)-10000 > int(cnl) or int(fnl) == int(cnl):
    #                     #     for e2 in edges:
    #                     #         if cnl == e2[0][0]:
    #                     #             is_loop = True
    #                     #     if is_loop:
    #                     #         ncontent = n0[1].get('label')
    #                     #         ncontent = ncontent.split('\n')
    #                     #         for s in ncontent:
    #                     #             s = s.split(': ')
    #                     #             if len(s) > 1:
    #                     #                 if s[1] == "JUMP":
    #                     #                     print(fnl, cnl)
    #                     #                     print(n0, s)
    #                     #                     c_nodes, c_edges = loop_graph(n0, nodes, edges)
    #                     #                     break
    #                     # else:
    #                         queue.appendleft(n)
    #                     break

    # print('loop count = ', count)
    #
    # return c_nodes, c_edges


def dfs_check(node, nodes, edges, visited, rec_stack):
    stack_impact = 0
    stack_sum = 0
    gas_consumption = 0
    is_jump = False

    visited.append(node)
    rec_stack.append(node)

    node_ins = node[1].get('label').split('\n')

    for i in node_ins:
        i = i.split(': ')[1]
        if i == 'JUMP' or i == 'JUMPI':
            is_jump = True

    for e in edges:
        if e[0][0] == node[0]:
            for n in nodes:
                if n[0] == e[0][1]:
                    neighbour_node = n
                    # print('neighbour = ', neighbour_node[0])

                    # ins = neighbour_node[1].get('label').split('\n')
                    # for i in ins:
                    #     if 'Stack Sum' in i:
                    #         stack_impact = int(i.split(': ')[1])
                    #     if 'Gas' in i:
                    #         gas_consumption = int(i.split(': ')[1])

                    if neighbour_node not in visited and neighbour_node != '':
                        if dfs_check(neighbour_node, nodes, edges, visited, rec_stack):
                            break
                            # return True
                    elif neighbour_node in rec_stack and is_jump:
                        if int(node[0]) > int(neighbour_node[0]):
                            print('CYCLE!!!!!')

                            # print(node[0], neighbour_node[0])
                            # print(rec_stack)

                            start = False

                            for block in rec_stack:
                                block_tag = block[0]
                                if block_tag == neighbour_node[0] or start:
                                    start = True
                                    block_label = block[1].get('label').split('\n')
                                    for block_ins in block_label:
                                        if 'Stack Sum' in block_ins:
                                            stack_impact = int(block_ins.split(': ')[1])
                                            stack_sum += stack_impact

                            print('Stack : ', stack_sum)

                            loop_graph(rec_stack, edges)

                            if stack_sum > 0:
                                print('POSITIVE')
                                print('\n')
                                if stack_sum > 1024:
                                    print('STACK OVERFLOW')
                                    return True
                            else:
                                print('NOT POSITIVE')
                                print('\n')
                                return True
                        else:
                            return False

    rec_stack.pop()

    return False


def loop_graph(nodes, edges):

    global loop_graph_count
    loop_graph_count += 1
    create_graph(nodes, edges, './cfg_loop/cfg_loop_part_{}'.format(loop_graph_count))

    wSE.write('\n\n{},{},{}'.format('Opcode', 'Constraints', 'Stack'))
    wSE.write('\n')

    stack = []
    storage = []
    memory = []
    f_con = []
    t_con = []
    gas_sum, c_nodes, c_edges = stack_status_constraint(stack, storage, memory, nodes, edges, '0', '', f_con, t_con, 0, 0, 0, 0)

    print('gas SUM = ', gas_sum)

    create_graph(c_nodes, c_edges, './cfg_constraint/cfg_loop_part_with_constraints_{}'.format(loop_graph_count))

    print('Done')

    # c_nodes = [start]
    # c_edges = []
    # queue = deque([])
    # queue.appendleft(start)
    # s0 = start[0]
    #
    # print('Start')
    # while len(queue) > 0:
    #     # print(queue)
    #     n0 = queue.popleft()
    #     sl = n0[0]
    #     if sl == '0':
    #         break
    #     else:
    #         for e in edges:
    #             fl = e[0][1]
    #             if fl == sl:
    #                 cl = e[0][0]
    #                 if cl == 0 or cl == s0:
    #                     if cl == s0:
    #                         if e not in c_edges:
    #                             c_edges.append(e)
    #                     break
    #                 else:
    #                     for n in nodes:
    #                         if n[0] == cl:
    #                             if n not in c_nodes:
    #                                 c_nodes.append(n)
    #                             if e not in c_edges:
    #                                 c_edges.append(e)
    #                             for e1 in edges:
    #                                 cl2 = e1[0][0]
    #                                 if cl == cl2:
    #                                     cl3 = e1[0][1]
    #                                     for n1 in nodes:
    #                                         if n1[0] == cl3:
    #                                             if n1 not in c_nodes:
    #                                                 c_nodes.append(n1)
    #                                             if e1 not in c_edges:
    #                                                 # print(e1)
    #                                                 c_edges.append(e1)
    #                             if n[0] not in loop_start_list:
    #                                 queue.appendleft(n)
    #                             break
    #
    # count_gas_and_stack(c_nodes)
    # create_graph(c_nodes, c_edges, './cfg_loop/cfg_loop_part_{}'.format(count))
    # print('Done')
    #
    # print('loop node count = ', len(c_nodes))
    # print('loop edge count = ', len(c_edges))

    # return c_nodes, c_edges


def stack_status(src):

    output = []
    f_funchash = os.path.join(os.path.dirname(__file__), 'functionHash')
    f_src = os.path.join(os.path.dirname(__file__), src)

    try:
        w = open(f_funchash, 'w')
        print('\n[INFO] Function Hashes')
        call(['solc', '--combined-json', 'hashes', f_src], stdout=w)
    except Exception as ex:
        print('Error: ', ex)

    with open(f_funchash, 'r') as fh:
        function_dict = json.load(fh)
        for key, val in function_dict.items():
            if key == 'contracts':
                for key2, val2 in val.items():
                    for key3, val3 in val2.items():
                        if key3 == 'hashes':
                            for key4, val4 in val3.items():
                                output.append(val4)

    return output
    # if inputs is not None:
    #     if inputs != ['no']:
    #         for i in inputs:
    #             data = hex(int(i)).split('0x')[1]
    #             count = 64 - len(data)
    #             while count > 0:
    #                 data = '0' + data
    #                 count -= 1
    #             function_input += data
    #     print(function_input)
    #     stack_simulation(function_input, inputs, binrun, funcname)
    #     return 0
    # else:
    #     output.append(function_input)
    #     return output


# def stack_simulation(function_input, inputs, binrun, funcname):
#
#     gas_cost = 0
#     input_data = function_input
#     f_binary = os.path.join(os.path.dirname(__file__), binrun)
#     f_result = os.path.join(os.path.dirname(__file__), 'ana_status')
#
#     try:
#         w = open(f_result, 'w')
#         try:
#             with open(f_binary, 'r') as bf:
#                 bf_data = bf.readline()
#                 print('\n[INFO] Stack simulating')
#                 check_output(['evm', '--debug', '--code', bf_data, '--input', input_data, 'run'], stderr=w)
#             w.close()
#         except Exception as ex:
#             print('[ERROR] Failed to open file \'ana_status.txt\'')
#             print('Error: ', ex)
#     except Exception as ex:
#         print('[ERROR] Failed to open file \'{}\''.format(binrun))
#         print('Error: ', ex)
#
#     try:
#         with open(f_result, 'r') as rf:
#             for line in rf:
#                 if 'gas'.lower() in line.rstrip():
#                     gas_cost += int(line.rstrip().split('cost=')[1])
#
#         print('[COMPLETE - Gas Estimation]')
#         print('[INFO] Gas cost using function \'{}\' with parameter set to {} => {:,} gas'.format(funcname,
#                                                                                                   inputs,
#                                                                                                   gas_cost))
#     except Exception as ex:
#         print('[ERROR] Failed to open file \'ana_status.txt\'')
#         print('Error: ', ex)


def constraint_jump(nodes, edges, stack, storage, memory, check, tag, input_data, f_con, t_con, count, init_tag, s):
    if count > 8:
        print('count = ', count)
    else:
        count += 1
        for n in nodes:
            n_tag = n[0]
            if n_tag == tag:
                q = deque([])
                n[1]['id'] = '\nStack now'
                print('======================================================== ')
                for item in stack:
                    n[1]['id'] += ' ' + str(item)
                start_tag = tag
                for n1 in nodes:
                    if n1[0] == start_tag:
                        tmp = n1[1].get('id').split('Stack now ')[1]
                        stack_new = tmp.split(' ')
                        q.appendleft(stack_new)
                        break
                # print('q before jumpi = ', q)
                stack_now = q.popleft()
                # print('stack for True = ', stack_now, t_con[-1])
                print('True Constraint: ', t_con[-1])
                wSE.write(' {0:80} |'.format(t_con[-1]))
                tag_num_1 = check[2]
                tag_num_0 = str(int(check[2]) + 10000)
                for e in edges:
                    if e[0][1] == tag_num_1:
                        # e[1]['label'] += '\n' + str(count) + ' ' + str(t_con[-1])
                        e[1]['color'] = 'red'
                        t_con.append(count)
                        t_con.append(tag_num_1)
                        t_con.append(s)
                # print('\n0<<<<<<<<<<0')
                value, init_tag, stack_new_0 = stack_status_constraint(stack_now, storage, memory, nodes, edges,
                                                                       tag_num_1, input_data,
                                                                       f_con, t_con, count, init_tag, str(int(tag_num_1)+int(s)))
                # print(value, init_tag, stack_new_0)
                # print('0>>>>>>>>>>0\n')
                if int(init_tag) > 0 or stack_new_0 == 0:
                    q.appendleft(stack_new_0)
                    # print('XXXXX')
                    for n1 in nodes:
                        if n1[0] == start_tag:
                            tmp = n1[1].get('id').split('Stack now ')[1]
                            stack_new = tmp.split(' ')
                            q.appendleft(stack_new)
                            break
                    stack_now = q.popleft()
                    # print('stack for False = ', stack_now, f_con[-1])
                    print('False Constraint: ', f_con[-1])
                    wSE.write(' {0:80} |'.format(f_con[-1]))
                    for e in edges:
                        if e[0][1] == tag_num_0:
                            # e[1]['label'] += '\n' + str(count) + ' ' + str(f_con[-1])
                            e[1]['color'] = 'red'
                            f_con.append(count)
                            f_con.append(tag_num_0)
                            f_con.append(s)
                    # print('\n1<<<<<<<<<<1')
                    # print('stack in = {}, tag num = {}'.format(stack_now, tag_num_0))
                    value, init_tag, stack_new_1 = stack_status_constraint(stack_now, storage, memory, nodes, edges,
                                                                           tag_num_0,
                                                                           input_data,
                                                                           f_con, t_con, count, init_tag, str(int(tag_num_0)+int(s)))
                    # print(value, init_tag, stack_new_1)
                    # print('1>>>>>>>>>>1\n')
                    q.append(stack_new_1)

                if int(init_tag) < 1 or count > 4:
                    break
                else:
                    stack_1 = q.popleft()
                    tmp_count = count
                    tag_num_1 = int(tag_num_1) + int(s)
                    # print('tagnum1 = ', tag_num_1)
                    value, init_tag, stack_start = stack_status_constraint(stack_1, storage, memory, nodes, edges,
                                                                           init_tag,
                                                                           input_data,
                                                                           f_con, t_con, count, init_tag, str(tag_num_1))
                    # print(init_tag, stack_start)
                    stack_0 = q.popleft()
                    # print('next stack = ', stack_0)
                    tag_num_0 = int(tag_num_0) + int(s)
                    # print('tagnum0 = ', tag_num_0)
                    value, init_tag, stack_start = stack_status_constraint(stack_0, storage, memory, nodes, edges,
                                                                           init_tag,
                                                                           input_data,
                                                                           f_con, t_con, tmp_count, init_tag, str(tag_num_0))
                    # print(init_tag, stack_start)
                    # print(f_con)
                    # print(t_con)
    # constraint_graph(t_con, f_con)


def stack_status_constraint(stack, storage, memory, nodes, edges, tag, input_data, f_con, t_con, count, init_tag, s, gas_sum):
    prev_ins = ''

    # print(count, tag, gas_sum)
    if count > 40:
        return gas_sum, nodes, edges
    else:
        for n in nodes:
            n_tag = n[0]
            # print(n, n_tag, tag)
            if n_tag == tag:
                n_label = n[1].get('label')
                ins = n_label.split('\n')
                # print(ins)
                for k in ins:
                    p = k.split(': ')
                    i = p[1]
                    j = p[0]
                    # print(i)
                    if j != 'Stack Sum' and j != 'Gas':
                        if len(stack) > 0:
                            wSE.write('{}'.format(str(stack)))
                        wSE.write('\n')
                        wSE.write('{},'.format(str(i)))
                        # mapping_to_sourcecode(k)
                    if i == 'JUMP':
                        gas_conumption = gas_table[i]
                        gas_sum += gas_conumption
                        flag, length, f_con, t_con, stack = se.stack_simulation(i, stack, storage, memory, 0, 0,
                                                                                input_data, f_con, t_con)
                        # check = prev_ins.split(' ')
                        # if check[1] == '[tag]':
                        #     tag_num = check[2]
                        #     for e in edges:
                        #         if e[0][1] == tag_num and e[0][0] == tag:
                        #             e[1]['color'] = 'red'
                        #     if tag_num < tag:
                        #         init_tag = tag_num
                        #         print('--------------------------------------------------------------------')
                        #         wSE.write(' {0:80} |'.format('X'))
                        #         break
                        #     else:
                        #         wSE.write(' {0:80} |'.format('X'))
                        #         value, init_tag, stack = stack_status_constraint(stack, storage, memory, nodes, edges,
                        #  tag_num, input_data, f_con, t_con, count, init_tag, s)
                        #         if value == 0:
                        #             # print('123')
                        #             break
                        # else:
                        #     continue

                        for e in edges:
                            if e[0][0] == n_tag:
                                # print(e[0][0])
                                for n1 in nodes:
                                    if n1[0] == e[0][1]:
                                        # print(n1[0])
                                        # print(f_con, t_con)
                                        wSE.write('{},'.format('X'))
                                        count += 1
                                        gas_sum, nodes, edges = stack_status_constraint(stack, storage, memory, nodes, edges, n1[0], input_data,
                                                                f_con, t_con, count, init_tag, s, gas_sum)
                    elif i == 'JUMPI':
                        gas_conumption = gas_table[i]
                        gas_sum += gas_conumption
                        flag, length, f_con, t_con, stack = se.stack_simulation(i, stack, storage, memory, 0, 0,
                                                                                input_data, f_con, t_con)
                        # check = prev_ins.split(' ')
                        # if flag == 1:
                        #     if check[1] == '[tag]':
                        #         tag_num = check[2]
                        #         for e in edges:
                        #             if e[0][1] == tag_num and e[0][0] == tag:
                        #                 e[1]['color'] = 'red'
                        #         wSE.write(' {0:80} |'.format('X'))
                        #         value, init_tag, stack = stack_status_constraint(stack, storage, memory, nodes, edges, tag_num, input_data, f_con, t_con, count, init_tag, s)
                        #         if value == 0:
                        #             # print('4456')
                        #             break
                        # elif flag == 0:
                        #     tag_num = str(int(check[2]) + 10000)
                        #     for e in edges:
                        #         if e[0][1] == tag_num:
                        #             e[1]['color'] = 'red'
                        #     wSE.write(' {0:80} |'.format('X'))
                        #     value, init_tag, stack = stack_status_constraint(stack, storage, memory, nodes, edges, tag_num, input_data, f_con, t_con, count, init_tag, s)
                        #     if value == 0:
                        #         # print('789')
                        #         break
                        # else:
                        #     constraint_jump(nodes, edges, stack, storage, memory, check, tag, input_data, f_con, t_con, count, init_tag, s)
                        #     break

                        for e in edges:
                            if e[0][0] == n_tag:
                                # print(e[0][0])
                                for n1 in nodes:
                                    if n1[0] == e[0][1]:
                                        if int(e[0][1]) > 10000:
                                            if flag != 1 and flag != 0:
                                                l = n1[1].get('label')
                                                no_pc = False
                                                for l_content in l.split('\n'):
                                                    if 'PC' in l_content:
                                                        no_pc = False
                                                        l_content = l_content.split(': ')
                                                        if f_con[-1] != l_content[1]:
                                                            n1[1].update({'label': l + '\n' + 'PC: ' + f_con[-1]})
                                                    else:
                                                        no_pc = True
                                                if no_pc:
                                                    n1[1].update({'label': l + '\n' + 'PC: ' + f_con[-1]})
                                                wSE.write('{},'.format(f_con[-1]))
                                            else:
                                                wSE.write('{},'.format('X'))
                                        else:
                                            if flag != 1 and flag != 0:
                                                l = n1[1].get('label')
                                                no_pc = False
                                                for l_content in l.split('\n'):
                                                    if 'PC' in l_content:
                                                        no_pc = False
                                                        l_content = l_content.split(': ')
                                                        if t_con[-1] != l_content[1]:
                                                            n1[1].update({'label': l + '\n' + 'PC: ' + t_con[-1]})
                                                    else:
                                                        no_pc = True
                                                if no_pc:
                                                    n1[1].update({'label': l + '\n' + 'PC: ' + t_con[-1]})
                                                wSE.write('{},'.format(t_con[-1]))
                                            else:
                                                wSE.write('{},'.format('X'))
                                        count += 1
                                        gas_sum, nodes, edges = stack_status_constraint(stack, storage, memory, nodes,
                                                                                        edges, n1[0], input_data,
                                                                                        f_con, t_con, count, init_tag,
                                                                                        s, gas_sum)

                    # elif i == 'REVERT' or i == 'STOP' or i == 'RETURN' or i == 'JUMP [out]':
                    #     # print('RRRRRRRRRRRRRRRRR')
                    #     return 0, 0, 0

                    elif j == 'Stack Sum' and (prev_ins == 'POP' or prev_ins == 'SWAP1' or 'PUSH' in prev_ins or prev_ins == 'TIMESTAMP' or prev_ins == 'JUMPDEST'):
                        for e in edges:
                            if e[0][0] == n_tag:
                                # print(e[0][0])
                                for n1 in nodes:
                                    if n1[0] == e[0][1]:
                                        # print(n1[0])
                                        wSE.write('{},'.format('X'))
                                        count += 1
                                        gas_sum, nodes, edges = stack_status_constraint(stack, storage, memory, nodes,
                                                                                        edges, n1[0], input_data,
                                                                                        f_con, t_con, count, init_tag,
                                                                                        s, gas_sum)

                                        # for e in edges:
                                        #     if e[0][0] == tag:
                                        #         tag_num = e[0][1]
                                        # e[1]['color'] = 'red'
                                        # wSE.write(' {0:80} |'.format('X'))
                                        # value, init_tag, stack = stack_status_constraint(stack, storage, memory, nodes, edges,
                                        #                                                  tag_num, input_data, f_con, t_con,
                                        #                                                  count, init_tag, s)
                                        # return 0, init_tag, stack
                    elif j == 'Stack Sum' or j == 'Gas' or j == 'PC':
                        return gas_sum, nodes, edges
                    else:
                        # print(k)
                        # print('stack size = ', len(stack))
                        gas = se.stack_simulation(i, stack, storage, memory, 0, 0, input_data, f_con, t_con)
                        if gas[0] is not None:
                            print(i)
                            print('gas = ', gas[0])
                            gas_sum += gas[0]
                        else:
                            if 'PUSH' in i:
                                i = i.split(' ')[0]
                                gas_conumption = gas_table[i]
                                gas_sum += gas_conumption
                            elif 'tag' in i:
                                continue
                            else:
                                t = re.sub(r'\d+', '', str(i))
                                gas_conumption = gas_table[t]
                                gas_sum += gas_conumption
                        wSE.write('{},'.format('X'))
                    prev_ins = i
                    # wSE.write(' {0:80} |'.format('X'))
                    # if int(init_tag) > 0:
                    #     # print('init_tag = ', init_tag)
                    #     break

        # create_graph(nodes, edges, 'cfg_with_constraint_{}'.format(666))
        # return 0, init_tag, stack

        return gas_sum, nodes, edges


def graph_detail(nodes):
    count = 0

    for n in nodes:
        label = n[1].get('label')
        label_content = label.split('\n')
        for l in label_content:
            if 'Stack' in l or 'Gas' in l or 'PC' in l:
                break
            else:
                count += 1

    print('Total instructions: ', count)


def count_gas_and_stack(nodes):
    stack_list = []
    stack_count = 0
    gas_count = 0

    for n in nodes:
        l = n[1].get('label').split('\n')
        for ln in l:
            if 'REVERT' in ln or 'STOP' in ln or 'RETURN' in ln:
                break
            else:
                if 'Stack' in ln:
                    stack_num = ln.split(': ')[1]
                    stack_count += int(stack_num)
                elif 'Gas' in ln:
                    gas_num = ln.split(': ')[1]
                    gas_count += int(gas_num)

    print('Stack Sum = ', stack_count)
    print('Gas count = ', gas_count)


def constraint_graph(t, f):
    n = []
    e = []
    new_t = []
    new_f = []
    n.append(('0', {'label': 'start', 'shape': 'box'}))
    for cons, level, tag, s in zip(*[iter(t)] * 4):
        new_t.append((level, tag, s, cons))
    for cons, level, tag, s in zip(*[iter(f)] * 4):
        new_f.append((level, tag, s, cons))
    new_t = sorted(new_t, key=lambda x: x[0])
    new_f = sorted(new_f, key=lambda x: x[0])
    tmp_t = []
    tmp_f = []
    final_t = []
    final_f = []
    prev_level = 1
    for i in new_t:
        if i[0] != prev_level:
            final_t.append(tmp_t)
            tmp_t = []
            prev_level = i[0]
        tmp_t.append(i)
    final_t.append(tmp_t)
    prev_level = 1
    for i in new_f:
        if i[0] != prev_level:
            final_f.append(tmp_f)
            tmp_f = []
            prev_level = i[0]
        tmp_f.append(i)
    final_f.append(tmp_f)

    prev_s = '0'
    for j in final_t:
        for i in j:
            # if i[0] % 2 == 1:
            n_name = str(int(i[2]) + int(i[1]) + int(prev_s))
            n.append((n_name, {'label': i[1] + ' at level: ' + str(i[0]) + ' ' + n_name, 'shape': 'box'}))
            e.append(((str(prev_s), n_name),
                      {'label': str(i[3]),
                       'color': 'blue'}))
            # else:
            #     n_name = str(int(i[2]) + int(i[1])) + str(prev_s) # + str(int(i[2]) + int(i[1]))
            #     n.append((n_name, {'label': i[1] + ' at level: ' + str(i[0]) + ' ' + n_name, 'shape': 'box'}))
            #     e.append(((str(prev_s), n_name),
            #               {'label': str(i[3]),
            #                'color': 'blue'}))
            prev_s = n_name

    prev_s = '0'
    for j in final_f:
        for i in j:
            # if i[0] % 2 == 1:
            n_name = str(int(i[2]) + int(i[1]) + int(prev_s))
            n.append((n_name, {'label': i[1] + ' at level: ' + str(i[0]) + ' ' + n_name, 'shape': 'box'}))
            e.append(((str(prev_s), n_name),
                      {'label': str(i[3]),
                       'color': 'blue'}))
            # else:
            #     n_name = str(int(i[2]) + int(i[1])) + str(prev_s) # + str(int(i[2]) + int(i[1]))
            #     n.append((n_name, {'label': i[1] + ' at level: ' + str(i[0]) + ' ' + n_name, 'shape': 'box'}))
            #     e.append(((str(prev_s), n_name),
            #               {'label': str(i[3]),
            #                'color': 'blue'}))
                # if i[0] != prev_level:
                #     prev_s = str(int(i[2]) + int(i[1]))
                #     prev_level = i[0]
            prev_s = n_name

    create_graph(n, e, 'cfg_constraint{}'.format(777))


def symbolic_gas(nodes, edges):
    g_nodes = []
    g_edges = []
    q = deque([])
    q.append(nodes[0])
    g_nodes.append(nodes[0])
    while len(q) > 0:
        n = q.popleft()
        index = n[0]
        gas = ''
        gas_symbolic = ''
        for e in edges:
            if e[0][0] == index:
                print(e)
                e_to = e[0][1]
                for n1 in nodes:
                    n_label = n1[0]
                    if n_label == e_to:
                        print(n1)
                        tmp = n1[1].get('label').split('\n')
                        for i in tmp:
                            if 'Gas' in i:
                                gas_symbolic = i.split(' + ')[0].split(':')[1]
                        if int(n_label) > 10000:
                            gas += '(1-b)*{}'.format(gas_symbolic)
                            print(gas_symbolic)
                        else:
                            gas += 'b*{}+'.format(gas_symbolic)
                        g_nodes.append(n1)
                g_edges.append(e)
    print(g_nodes, g_nodes)
    # create_graph(g_nodes, g_edges, 'gas_tree')


def find_graph_head(node_list, edge_list):
    head_list = []

    for idx, n in enumerate(node_list):
        if n not in edge_list:
            head_list.append((n, idx))

    print('\t-- Total {} graph(s) constructed --'.format(len(head_list)))

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

    print('==> Checking CFG ', end='')

    while len(queue):
        if count % 1000 == 0:
            print('.', end='')
            sys.stdout.flush()

        count += 1
        father_node = queue.popleft()
        f_idx = father_node[0]
        f_id = father_node[1].get('id')

        for e in edges:
            edge_relation = e[0]
            edge_from = edge_relation[0]
            edge_to = edge_relation[1]
            edge_weight = e[1].get('id')

            if edge_from == f_idx:
                for n in nodes:
                    child_idx = n[0]
                    if edge_to == child_idx:
                        n_label_idx = n[1].get('label').split(' ')
                        c_id = n[1].get('id')
                        if int(f_id) + int(edge_weight) > int(c_id):
                            child_node_info = n[1]
                            if int(c_id) > 0 \
                                    and int(child_idx) > 100000 \
                                    and 'JUMP' in father_node[1].get('label')\
                                    and 'JUMP [in]' not in father_node[1].get('label')\
                                    and father_node[1].get('label').rstrip().split()[1] != 'JUMPDEST':
                                if int(f_idx) > int(n_label_idx[0]):
                                    increase_amount = int(f_id) - int(c_id)
                                    print(father_node, n,  increase_amount)
                                    cycle_nodes.append((father_node, n, increase_amount))
                                    cycle_count += 1
                                    check_result = 1
                                    child_node_info['id'] = str(int(f_id) + int(edge_weight))
                                    break
                            else:
                                child_node_info['id'] = str(int(f_id) + int(edge_weight))
                                queue.appendleft(n)
                                break
    print('\n\t[Done, Found {} cycle(s) from assembly code]'.format(cycle_count))
    return check_result, cycle_nodes, cycle_count


def cycle_graph(cycle_nodes, nodes, edges):
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


def mapping_to_sourcecode(ins):
    # print('==> Mapping cycle node to source code')

    f_op_tmp = os.path.join(os.path.dirname(__file__), 'opcode_tmp')

    # f_src_tmp = os.path.join(os.path.dirname(__file__), 'img/{}/cycle_src_{}.txt'.format(row_id, row_id))
    # f_tmp = os.path.join(os.path.dirname(__file__), 'tmp')
    # f_op_gas = os.path.join(os.path.dirname(__file__), 'op_gas')

    # last_line = ''
    # src_text = ''
    # opcode_text = ''
    # op_gas_text = ''

    # w = open(f_src_tmp, 'w')
    # w2 = open(f_tmp, 'w')
    # w3 = open(f_op_gas, 'w')

    num = ins.split(': ')[0]

    with open(f_op_tmp, 'r') as f:
        for idx, line in enumerate(f):
            # print(idx, line.rstrip())
            if str(idx) == num:
                # print(idx, line.rstrip())
                wSE.write('{0:100} | '.format(line.rstrip()))
            # for n in cycle_nodes:
            #     n_label = n[1].get('label').split('\n')
            #     print(n_label)
                # if int(n_label[0]) == idx:
                #     w2.write(line)
                #     src = line.rstrip().split('  ')[-1].strip()
                #     src = src.replace('...', '') + '\n'
                #     op = line.rstrip().split('  ')[0] + '\n'
                #     op_gas = line.rstrip().split('  ')[0]
                #     op_gas = re.sub(r'\d+', '', str(op_gas.split(' ')[0]))
                #     opcode_text += op
                #     w3.write(op_gas + '\n')
                #     # op_gas_text += op_gas + '\n'
                #     if last_line != src:
                #         # w.write(src)
                #         src_text += src
                #         last_line = src
                #     break
    # w.close()
    # w2.close()
    # w3.close()
    # print('\t[Finishing mapping]')

    # return src_text, opcode_text


def trace_condition(cycle_node):
    print('==> Trace condition from opcode')
    # print(cycle_node)
    f_op_tmp = os.path.join(os.path.dirname(__file__), 'opcode_tmp')
    condition_node_list = []

    for n in cycle_node:
        # print(n)
        start_node = n[1][1].get('label').split(' ')
        increase_amount = n[2]
        start = int(start_node[0])
        with open(f_op_tmp, 'r') as f:
            for idx, line in enumerate(f):
                if idx == start:
                    seg = line.split('    ')
                    if seg[0] == 'MLOAD' or seg[0] == 'SLOAD':
                        condition_var = seg[1].rstrip()
                        condition_node_list.append([increase_amount, condition_var])
                        break
                    start += 1
    # print(condition_node_list)
    return condition_node_list


def create_graph(n, e, row_id):
    # print('[INFO] Constructing visualizing graph')
    digraph = functools.partial(gv.Digraph, format='svg')
    g = add_edges(add_nodes(digraph(), n), e)
    filename = 'img/{}/g{}'.format(row_id, row_id)
    g.render(filename=filename)
    # print('[COMPLETE - CFG construction]')

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


def opcode_ext(x, y):
    ans = math.pow(x, y)
    print(ans)


def init_graph(nodes, edges):
    print('==> Initiating Control Flow Graph')

    stack_push_one = ['PUSH', 'DUP', 'CALLER', 'CALLVALUE', 'GAS', 'CALLDATASIZE', 'PC', 'MSIZE',
                      'COINBASE', 'GASLIMIT', 'DIFFICULTY', 'TIMESTAMP', 'NUMBER', 'CODESIZE', 'GASPRICE', 'ADDRESS',
                      'ORIGIN']
    stack_pop_one = ['POP', 'LT', 'GT', 'EQ', 'AND', 'OR', 'XOR', 'ADD', 'SUB',
                     'MUL', 'DIV', 'EXP', 'KECCAK256', 'SHA3', 'BYTE', 'SIGNEXTEND', 'SUICIDE']
    stack_pop_two = ['MSTORE', 'SSTORE', 'RETURN', 'CREATE', 'ADDMOD', 'MULMOD']
    stack_pop_three = ['CODECOPY', 'CALLDATACOPY']
    stack_unchange = ['SWAP', 'MLOAD', 'SLOAD', 'NOT', 'ISZERO', 'CALLDATALOAD', 'EXTCODESIZE', 'STOP', 'INVALID',
                      'BALANCE', 'BLOCKHASH']

    opcode_with_formula = ['EXP', 'SHA3', 'CALLDATACOPY', 'RETURNDATACOPY', 'CODECOPY', 'EXTCODECOPY', 'SSTORE', 'CALL', 'CALLCODE', 'DELEGATECALL'
                           , 'SELFDESTRUCT', 'LOG0', 'LOG1', 'LOG2', 'LOG3', 'LOG4']

    stack_size = '0'
    stack_sum = 0
    edge_color = 'black'
    prev_instruction = '0'
    gas_total = 0
    stack = []
    storage = []
    memory = []
    gas_f = '0'
    jumpdest = -1
    jumpfound = True

    f_op = os.path.join(os.path.dirname(__file__), 'opcode')
    f_status = os.path.join(os.path.dirname(__file__), 'ana_status')

    w = open(f_status, 'w')

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
            t = re.sub(r'\d+', '', str(s[0]))

            # if line.rstrip() != 'RETURN' and jumpfound:
            #     stack, storage, memory, jumpdest, gas_f = se.stack_simulation(line, storage, stack, memory,
            #                                                                        jumpdest, 0)
            #
            # if jumpdest != -1:
            #     jumpfound = False
            #     print(jumpdest)
            #     if t == 'tag':
            #         if int(s[1]) == jumpdest:
            #             print(line)
            #             print("FFFFFFFFFFFFFF")
            #             jumpfound = True
            #             jumpdest = -1

            for g in gas_table:
                if t == g:
                    #print(g)
                    #print(gas_table[g])
                    #print(type(gas_table[g]))
                    gas_total += gas_table[g]

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

                if jumpfound:
                    w.write(line)
                    w.write('Stack size: ' + str(stack_sum) + '\n')
                    w.write('Gas: ' + str(gas_total) + '\n')
                    w.write('Stack: ' + str(stack) + '\n')
                    w.write('-----------------------------------------------------------------------------------------------\n')
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
                                  {'label': str(idx) + ' ' + line.rstrip(),
                                   'id': '-1'}))
                    tag_number = int(prev_instruction.split(' ')[2])
                    jump_from = str(stack_header)
                    jump_to = str(tag_number + 100000)
                    edges.append(((jump_from, jump_to),
                                  {'label': str(idx) + ' ',
                                   'color': edge_color,
                                   'id': '0'}))

                prev_instruction = line

                if jumpfound:
                    w.write(line)
                    w.write('Stack size: ' + str(stack_sum) + '\n')
                    w.write('Gas: ' + str(gas_total) + '\n')
                    w.write('Stack: ' + str(stack) + '\n')
                    w.write('-----------------------------------------------------------------------------------------------\n')
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
                          {'label': str(idx) + ' ' + line.strip(),
                           'id': '-1'}))
            edges.append(((one_before_header, stack_header),
                          {'label': str(idx) + ' ' + instruction + ' ' + stack_size,
                           'color': edge_color,
                           'id': str(stack_size)}))
            prev_instruction = line

            if jumpfound:
                w.write(line)
                w.write('Stack size: ' + str(stack_sum) + '\n')
                w.write('Gas: ' + str(gas_total) + '\n')
                w.write('Stack: ' + str(stack) + '\n')
                w.write('-----------------------------------------------------------------------------------------------\n')

    print('\t[Control Flow Graph Constructed]')

    node_list = []
    edge_list = []

    for n in nodes:
        node_idx = n[0]
        node_list.append(node_idx)
    for e in edges:
        edge_idx = e[0][1]
        edge_list.append(edge_idx)

    print('\t-- {} nodes, {} edges --'.format(len(node_list), len(edge_list)))

    return nodes, edges, node_list, edge_list, gas_total


def code_preproc(filename):
    f_op = os.path.join(os.path.dirname(__file__), 'opcode')
    f_op_cons = os.path.join(os.path.dirname(__file__), 'opcode_cons')
    f_op_two = os.path.join(os.path.dirname(__file__), 'opcode_two')
    f_op_tmp = os.path.join(os.path.dirname(__file__), 'opcode_tmp')
    f_src = os.path.join(os.path.dirname(__file__), filename)
    op_text = ''
    op_with_src_text = ''

    w = open(f_op, 'w')
    w2 = open(f_op_tmp, 'w')
    w3 = open(f_op_cons, 'w')
    w4 = open(f_op_two, 'w')

    is_data = False
    data_count = 0
    tag_idx_num = 0

    with open(f_src, 'r') as f:
        for idx, line in enumerate(f):
            is_tag = False
            new_line = line.replace('\t', ' ').split(' ')
            # print(new_line)
            if '.data\n' in new_line:
                is_data = True
                data_count += 1
                continue
            if is_data:
                if 'tag' in new_line:
                    is_tag = True
                    tag_idx_num = new_line.index('tag')
                if data_count % 2 == 1:
                    if len(new_line) > 8 and data_count == 1:
                        if 'REVERT\n' in new_line:
                            w.write('REVERT\n')
                            w2.write('REVERT\n')
                        elif is_tag:
                            text = new_line[tag_idx_num].rstrip().strip() + ' ' \
                                   + new_line[tag_idx_num + 1].rstrip().strip() + '\n'
                            w.write(text)
                            op_text += text
                            for l in range(tag_idx_num, len(new_line)):
                                w2.write(new_line[l].rstrip().strip() + ' ')
                                op_with_src_text += new_line[l].rstrip().strip() + ' '
                            w2.write('\n')
                            op_with_src_text += '\n'
                        elif new_line[6] != '':
                            text = new_line[6].rstrip().strip() + ' ' \
                                   + new_line[7].rstrip().strip() + ' ' \
                                   + new_line[8].rstrip().strip() + '\n'
                            w.write(text)
                            op_text += text
                            for l in range(6, len(new_line)):
                                w2.write(new_line[l].rstrip().strip() + ' ')
                                op_with_src_text += new_line[l].rstrip().strip() + ' '
                            w2.write('\n')
                            op_with_src_text += '\n'
                    elif len(new_line) > 15:
                        c2c = True
                        if 'REVERT\n' in new_line:
                            w4.write('REVERT\n')
                            w2.write('REVERT\n')
                        elif is_tag:
                            text = new_line[tag_idx_num].rstrip().strip() + ' ' \
                                   + new_line[tag_idx_num + 1].rstrip().strip() + '\n'
                            w4.write(text)
                            op_text += text
                            for l in range(tag_idx_num, len(new_line)):
                                w2.write(new_line[l].rstrip().strip() + ' ')
                                op_with_src_text += new_line[l].rstrip().strip() + ' '
                            w2.write('\n')
                            op_with_src_text += '\n'
                        elif new_line[14] != '':
                            text = new_line[14].rstrip().strip()
                            if len(new_line) > 15:
                                text += ' ' + new_line[15].rstrip().strip()
                            if len(new_line) > 16:
                                text += ' ' + new_line[16].rstrip().strip()
                                   # + new_line[15].rstrip().strip() + ' ' \
                                   # + new_line[16].rstrip().strip() + '\n'
                            text += '\n'
                            w4.write(text)
                            op_text += text
                            for l in range(14, len(new_line)):
                                w2.write(new_line[l].rstrip().strip() + ' ')
                                op_with_src_text += new_line[l].rstrip().strip() + ' '
                            w2.write('\n')
                            op_with_src_text += '\n'
                if data_count % 2 == 0:
                    if 'REVERT\n' in new_line:
                        w3.write('REVERT\n')
                        w2.write('REVERT\n')
                    elif is_tag:
                        text = new_line[tag_idx_num].rstrip().strip() + ' ' \
                               + new_line[tag_idx_num + 1].rstrip().strip() + '\n'
                        w3.write(text)
                        op_text += text
                        for l in range(tag_idx_num, len(new_line)):
                            w2.write(new_line[l].rstrip().strip() + ' ')
                            op_with_src_text += new_line[l].rstrip().strip() + ' '
                        w2.write('\n')
                        op_with_src_text += '\n'
                    elif len(new_line) > 10:
                        text = new_line[10].rstrip().strip() + ' ' + \
                               new_line[11].rstrip().strip() + ' ' \
                               + new_line[12].rstrip().strip() + '\n'
                        w3.write(text)
    w.close()
    w2.close()
    w3.close()
    w4.close()

    return op_text, op_with_src_text


if __name__ == '__main__':
    main()
