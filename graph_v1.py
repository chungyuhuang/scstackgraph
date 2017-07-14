for key_world in stack_push_one:
    if key_world in instruction:
        edge_color = 'black'
        node_label = 'JUMPDEST' + '(' + str(stack_size) + ')'
        if key_world != 'JUMPDEST':
            stack_size += 1
            edge_color = 'red'
            node_label = str(stack_size)
        two_before_header = one_before_header
        one_before_header = stack_header
        stack_header = node_header
        nodes.append((stack_header, {'label': node_label}))
        edges.append(((one_before_header, stack_header),
                      {'label': 'step' + str(idx + 1) + instruction, 'color': edge_color}))
        break
for key_world in stack_pop_two:
    if key_world in instruction:
        tmp = one_before_header
        one_before_header = stack_header
        stack_header = two_before_header
        two_before_header = tmp
        edges.append(((one_before_header, stack_header),
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
                    stack_size -= 1
                    break
for key_world in stack_unchange:
    if key_world in instruction:
        edges.append(((stack_header, stack_header),
                      {'label': 'step' + str(idx + 1) + instruction, 'color': 'brown'}))
        break
if s[1] in ['JUMP', 'JUMPI']:
    jump_from = stack_header
    jump_to = '[' + str(push_value_list[-1]) + ']'
    edges.append(((jump_from, jump_to),
                  {'label': 'step' + str(idx + 1) + instruction, 'color': 'blue'}))