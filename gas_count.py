import os
from gas_price import *
from z3 import *

def cal_loop_gas():
    # l = 0
    # l += -3
    # print(l)
    # x = Int('x')
    # y = Int('y')
    # solve(x > 2, y < 10, x + 2 * y == 7)
    # # hex(int('ffffff', 16)) / hex(int('60fe47b1', 16))
    # print()
    # a = '0x{:x}'.format(int('0x60fe47b1', 16))
    # print(a)
    # print(int(a, 16))
    # print('0x{:x}'.format(int(0xffffffff & int(a, 16))))
    #
    # str1 = "a = b"
    # a = BitVec('a', 3)
    # b = BitVec('b', 3)
    # constraint1 = a == b  # sets constraint1 to be the z3 expression a == b
    # s = Solver()
    # s.push()
    # # s.add(str1) # error: 'True, False or Z3 Boolean expression expected'
    # s.add(constraint1)
    # constraint2 = eval(str1)
    # print(constraint2)


    gas_total = 0
    f_op_gas = os.path.join(os.path.dirname(__file__), 'op_gas')
    with open(f_op_gas, 'r') as f:
        for idx, line in enumerate(f):
            for g in gas_table:
                if line.rstrip() == g:
                    # print(gas_table[g])
                    print(line.rstrip(), gas_table[g])
                    gas_total += gas_table[g]
    print('==> loop gas = {} \n'.format(gas_total))


def sign(x):
    if x > 0:
        return 1
    elif x == 0:
        return 0
    elif x < 0:
        return -1
    else:
        return x


if __name__ == '__main__':
    print(round(((sign(0) + 1) / 2), 0))
    # cal_loop_gas()
