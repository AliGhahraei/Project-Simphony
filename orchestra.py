from collections import namedtuple
from functools import partial
from lexer import Types, DUPLICATED_OPERATORS
from operator import (add, sub, mul, truediv, mod, eq, gt, lt, ge, le, and_,
                      or_, pos, neg, not_)


MEMORY_SECTORS = [
    ('global_', 10_000),
    ('local', 50_000),
    ('temporal', 170_000),
    ('constant', 200_000),
    ('end', 240_000),
]


memory = {sector[0]: {type_ : {} for type_ in Types}
          for sector in MEMORY_SECTORS[:-1]}


parameters = []

output = []

class UninitializedError(Exception):
    pass


def generate_memory_addresses(end_addresses=False):
    ADDRESS_TUPLE = namedtuple('ADDRESSES', [address[0] for address
                                             in MEMORY_SECTORS[:-1]])

    current_address = MEMORY_SECTORS[0][1]
    addresses = []
    for sector in MEMORY_SECTORS[1:]:
        next_address = sector[1]
        sector_size = next_address - current_address

        type_start_addresses = [starting_address for starting_address in
                                range(current_address, next_address,
                                      int(sector_size / len(Types)))]

        if end_addresses:
            type_end_addresses = type_start_addresses[1:] + [next_address]

            type_addresses = dict(zip(Types, zip(type_start_addresses,
                                                 type_end_addresses)))
        else:
            type_addresses = dict(zip(Types, type_start_addresses))

        addresses.append(type_addresses)
        current_address = next_address

    return ADDRESS_TUPLE._make(addresses)


addresses = generate_memory_addresses(end_addresses=True)


def value(address):
    try:
        address = int(address)
        return get_address_container(address)[address]
    except KeyError as e:
        raise UninitializedError(f'Sorry, but you tried to use a variable '
                                 f'before assignment. Please check your program')


def store(value, address):
    address = int(address)
    get_address_container(address)[address] = value


def get_address_container(address):
    for i, sector in enumerate(MEMORY_SECTORS[-2::-1], start=1):
        sector_name, sector_address = sector
        if address >= sector_address:
            for type_address in addresses[-i].items():
                type_, (start_address, end_address) = type_address
                if start_address <= address < end_address:
                    return memory[sector_name][type_]


def store_param(address):
    parameters.append(value(address))


def print_(end='\n'):
    output.append(str(parameters.pop()) + end)
    # print(printed_value, end=end)


def goto(jump):
    return int(jump)


def gotof(address, jump):
    if not value(address):
        return goto(jump)


OPERATIONS = {
    '+' : add,
    '-' : sub,
    '*' : mul,
    '/' : truediv,
    '**' : pow,
    'mod' : mod,
    'equals' : eq,
    '>' : gt,
    '<' : lt,
    '>=' : ge,
    '<=' : le,
    'and' : and_,
    'or' : or_,
    '++' : partial(add, 1),
    '--' : lambda value: sub(value, 1),
    DUPLICATED_OPERATORS['+'] : pos,
    DUPLICATED_OPERATORS['-'] : neg,
    'not' : not_,
    '=' : lambda value: value,
}

VM_FUNCTIONS = {
    'PARAM' : store_param,
    'print' : partial(print_, end=''),
    'println' : print_,
    'GOTO' : goto,
    'GOTOF': gotof,
}

SPECIAL_PARAMETER_TYPES = {
    'print' : [{type_ for type_ in Types}],
    'println' : [{type_ for type_ in Types}],
    'to_str' : [{type_ for type_ in Types}],
    'get' : [{Types.STR}, {Types.INT}],
}


def handle_vm_function(quad):
    try:
        operation = VM_FUNCTIONS[quad[0]]
        address1 = quad[1]
        return operation(address1)
    except TypeError:
        # Thrown if function needs two parameters
        address2 = quad[2]
        return operation(address1, address2)
    except IndexError:
        # No quad 0: parameterless
        return operation()
    except KeyError:
        raise NotImplementedError(f"This operation isn't supported yet "
                                  f"({quad[0]})")


def handle_operation(operation, quad):
    address1 = quad[1]
    address2 = quad[2]

    try:
        address3 = quad[3]
    except IndexError:
        # Only 1 operand and 1 address to store the result
        result = operation(value(address1))
        store(result, address2)
    else:
        try:
            # 2 operands and 1 address to store the result
            value1 = value(address1)
            value2 = value(address2)
            result = operation(value1, value2)
            store(result, address3)
        except ZeroDivisionError as e:
            raise ZeroDivisionError(f'Oops! You tried to divide {value1} by 0. '
                                    f'Please correct your program') from e


def play_note(lines, constants):
    memory['constant'] = constants
    output.clear()

    line_list = [line.split() for line in lines.split('\n')]

    current_quad_idx = 0
    while current_quad_idx < len(line_list):
        try:
            quad = line_list[current_quad_idx]
        except IndexError:
            # Finish when accessing non-existent quadruple (naive GOTO did it)
            return output

        try:
            operation = OPERATIONS[quad[0]]
        except KeyError:
            vm_result = handle_vm_function(quad)

            if vm_result is not None:
                current_quad_idx = vm_result
            else:
                current_quad_idx += 1
        except IndexError:
            # Empty operation (empty line) might only be found at the end
            return output
        else:
            handle_operation(operation, quad)
            current_quad_idx += 1

    return output
