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


def assign():
    pass


def value(address):
    address = int(address)
    return get_address_container(address)[address]


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
    '--' : partial(sub, 1),
    DUPLICATED_OPERATORS['+'] : pos,
    DUPLICATED_OPERATORS['-'] : neg,
    'not' : not_,
    '=' : assign,
}

POLYMORPHIC_FUNCS = {'print'}


def play_note(lines, constants):
    memory['constant'] = constants

    line_list = lines.split('\n')

    for line in line_list[:-1]:
        quad = line.split()
        try:
            result = OPERATIONS[quad[0]](value(quad[1]))(value(quad[2]))
            store(result, quad[-1])
        except KeyError as e:
            raise NotImplementedError(
                f'The address {str(e)} was not found in memory, which means '
                f'that a necessary VM feature for your program is still '
                f'pending. Please contact our dev team. Sorry! *crashes '
                f'shamefully*')
