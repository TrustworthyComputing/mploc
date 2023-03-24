#!/usr/bin/env python

from enum import Enum
import os
import sys
import argparse

GATE_COUNTER = 0

InstanceType = Enum('InstanceType', ['Net', 'CellRef', 'Instance', 'Empty'])

def parse_args():
    parser = argparse.ArgumentParser(description='EDIF parser')
    parser.add_argument('--edif', help='path to EDIF file (.edif)', required=True)
    parser.add_argument('--out', help='path to output file', required=False)
    args = parser.parse_args()
    input_file = args.edif
    if not args.edif.endswith(".edif"):
        print("EDIF file should end with '.edif' extension.")
        sys.exit(-1)
    if not os.path.isfile(args.edif):
        print("Input file '" + args.edif + "' does not exist.")
        sys.exit(-2)
    output_file = None
    if args.out is None:
        output_file = input_file[:-5] + '.out'
    else:
        output_file = args.out
    return input_file, output_file

class Port:
    def __init__(self, name, direction, length):
        self.name = name
        self.direction = direction
        self.length = length
        self.invalid = False
        self.nets = [""] * self.length

class LogicGate:
    def __init__(self, function, id):
        global GATE_COUNTER
        self.function = function
        self.id = id
        self.idx = GATE_COUNTER
        self.input_nets = []
        self.output_nets = []
        self.depends_on = []
        self.done = False
        GATE_COUNTER += 1

    def set_input_net(self, in_net):
        self.input_nets.append(in_net)
        for i in in_net.left:
            self.depends_on.append(i)

    def set_output_net(self, out_net):
        self.output_nets.append(out_net)

class Net:
    def __init__(self, name):
        self.name = name
        self.left = []
        self.right = []
        self.value = 0
        self.idx = -1
        self.invalid = False
        self.port = ''

    def set_left(self, left_gate):
        self.left.append(left_gate)

    def set_right(self, right_gate):
        self.right.append(right_gate)

def main():
    input_file, output_file = parse_args()
    edif_file = open(input_file, "r")

    flag = False
    interface_flag = False
    index_flag = False
    port_flag = False
    wiremap_flag = False
    rename_flag = True
    map_flag = False
    array_flag = False
    name_flag = False
    prev_word = 'ERROR'
    temp_name = ''
    gate_list = []
    port_list = []
    cell_list = []
    net_list = []
    port_dict = {}
    wire_input_index = 0
    wire_output_index = 0

    print("Parsing EDIF net_list...")
    print("Declaring nets and gates...")
    for line in edif_file:
        is_left = False
        if 'GND' in line or 'VCC' in line or 'VDD' in line:
            continue
        if 'cell' in line and not flag and 'GENERIC' not in line:
            cell_list.append(line[line.find('"$_') + 3:line.find('_"')]) # get gate type
        if 'DESIGN' in line:
            flag = True
        if flag and 'portRef' in line:
            if '(instanceRef' not in line and 'member' not in line:
                wiremap_flag = True
        elif flag and 'interface' in line:
            interface_flag = True
        if 'net' in line and 'rename' in line and flag:
            map_flag = True
        elif 'portRef' in line and "(member" in line and flag:
            map_flag = True
        elif 'net' in line and 'rename' not in line and 'joined' in line:
            map_flag = True
            rename_flag = False
        if 'net' in line or 'portRef' in line:
            instance_type = InstanceType.Net
        elif 'instance' in line:
            instance_type = InstanceType.Instance
        elif "cellRef" in line:
            instance_type = InstanceType.CellRef           
        else:
            instance_type = InstanceType.Empty

        # print(line, temp_name)
        for word in line.split():
            if wiremap_flag:
                prev_word_2 = ""
                for word_2 in prev_line.split():
                    if 'id' in word_2 and 'net' in prev_word_2:
                        temp_name = word_2.strip(')')
                    prev_word_2 = word_2
                if 'portRef' in prev_word:
                    for i in port_list:
                        if i.name == word.strip(')'):
                            # if "(instanceRef" in prev_line:
                            #     i.nets[0] = word.strip(')')
                            # else:
                            #     i.nets[0] = temp_name
                            i.nets[0] = temp_name
                            temp_name = ''
                            for w in net_list:
                                if i.nets[0] == w.name:
                                    if w.port != '':
                                        break
                                    w.port = i.name
                                    w.idx = 0
                    wiremap_flag = False

            # identify input and output ports
            if interface_flag and "port" in word:
                port_flag = True
            elif interface_flag and port_flag and "array" in word:
                array_flag = True
            elif interface_flag and port_flag and "array" not in word \
                and "port" in prev_word:
                temp_name = word
                bit_size = 1
            elif interface_flag and port_flag and array_flag and not name_flag:
                temp_name = word
                name_flag = True
            elif interface_flag and port_flag and array_flag and name_flag \
                and 'direction' not in word and 'INPUT' not in word \
                and 'OUTPUT' not in word:
                bit_size = int(word.strip(')'))
            elif interface_flag and 'direction' in prev_word:
                if 'INPUT' in word:
                    port_dict[temp_name] = wire_input_index
                    wire_input_index += bit_size
                else:
                    port_dict[temp_name] = wire_output_index
                    wire_output_index += bit_size
                port_list.append(Port(temp_name, word.strip(')'), bit_size))
                port_flag = False
                array_flag = False
                name_flag = False

            # port mapping
            if map_flag and not rename_flag and 'net' in prev_word:
                for i in port_list:
                    if i.name == word:
                        i.nets[0] = word
                        break
                map_flag = False
                rename_flag = True

            if map_flag and 'id' in word:
                temp_name = word
            elif map_flag and 'member' in prev_word:
                port_name = word
                index_flag = True
            elif map_flag and index_flag:
                index = word.strip(')')
                index_flag = False
                temp_name = prev_line[prev_line.find('rename ') + 7:prev_line.find(' "')]
                for i in port_list:
                    if i.name == port_name:
                        i.nets[int(index)] = temp_name
                        break
                map_flag = False
            elif map_flag and 'id' in prev_word:
                try:
                    index = int(word[word.find("[") + 1:word.find("]")])  # Get index out of name[index]
                except:
                    index = 0
                    map_flag = False
                    continue
                for i in port_list:
                    if i.name == word:
                        i.nets[int(index)] = temp_name
                        break
                map_flag = False

            if 'contents' in word:
                interface_flag = False
            if instance_type == InstanceType.Instance and 'id' in word:
                prev_id = word
            elif instance_type == InstanceType.CellRef and 'id' in word and flag:
                index = int(word[-1]) - 1
                gate_list.append(LogicGate(cell_list[index], prev_id))
            elif instance_type == InstanceType.Net and 'net' in prev_word \
                and 'rename' not in word:
                new_net = Net(word)
                new_net.idx = 0
                new_net.port = word
                net_list.append(new_net)
                print("word:", word, "index:", new_net.idx)
            elif instance_type == InstanceType.Net and 'rename' in prev_word:
                new_net = Net(word)
                if line.find("[") != -1:
                    new_net.idx = int(line[line.find("[") + 1:line.find("]")])  # Get index out of name[index]
                    if line.find("$") != -1:
                        gate_name = line[line.rfind('$') + 1:line.find("[")]    # Get name out of name[index]
                    else:
                        gate_name = line[line.find('"') + 1:line.find("[")]     # Get name out of name[index]
                    new_net.port = gate_name
                    print("gate_name:", gate_name, "index:", new_net.idx)
                net_list.append(new_net)
            elif instance_type == InstanceType.Net and word in ('Y', 'q', 'Q'):
                is_left = True
            elif instance_type == InstanceType.Net and 'instanceRef' in prev_word:
                for gate in gate_list:
                    if gate.id in word:
                        if is_left:
                            new_net.set_left(gate)
                        else:
                            new_net.set_right(gate)
            prev_word = word
        prev_line = line
    edif_file.close()
    print('Finished parsing net_list!')

    print('Establishing connections between nets and gates...')
    for gate in gate_list:
        for net in net_list:
            for left_gate in net.left:
                if left_gate.id == gate.id:
                    gate.set_output_net(net)
            for right_gate in net.right:
                if right_gate.id == gate.id:
                    gate.set_input_net(net)

    # Next, we specify the number of inputs/outputs followed by the wordsizes
    inter_id_ctr = 0
    output_id_ctr = 0
    invalid_ctr = 0 # mark hanging wires (no gate to the left or right)
    input_port_len = []
    output_port_len = []
    invalid_ports = [] # mark port if it's an output that's connected directly to an input
    visited = {}
    for wire in net_list:
        if wire.port != '':
            visited[wire.port] = True
        if len(wire.left) == 0 and len(wire.right) == 0:
            wire.invalid = True
            invalid_ctr += 1
    for port in port_list:
        if port.name not in visited:
            port.invalid = True
            invalid_ports.append(port)
            continue
        is_invalid = True
        for j in range(len(port.nets)):
            for wire in net_list:
                if wire.name == port.nets[j]:
                    if "OUTPUT" in port.direction and wire.left == []: # ignore input -> output
                        break
                    if not wire.invalid:
                        is_invalid = False
                        break
        port.invalid = is_invalid
        if is_invalid:
            invalid_ports.append(port)
            continue

    for port in port_list:
        if 'INPUT' in port.direction and not port.invalid:
            input_port_len.append(port.length)
            inter_id_ctr += port.length
        elif not port.invalid:
            output_port_len.append(port.length)
            output_id_ctr += port.length

    num_inputs = inter_id_ctr
    num_outputs = output_id_ctr
    output_id_ctr = len(net_list) - invalid_ctr - output_id_ctr
    visited = {}
    for wire in net_list:
        if wire.invalid:
            continue
        if wire.left == []: # if input
            try:
                wire.name = port_dict[wire.port] + wire.idx
                visited[wire.port] = True
                for port in invalid_ports:
                    if 'INPUT' in port.direction \
                        and port_dict[port.name] < port_dict[wire.port]:
                        wire.name -= port.length
            except Exception as exc:
                raise RuntimeError("[!] In wire ID:", wire.name) from exc
        elif wire.port in port_dict:  # if output
            try:
                visited[wire.port] = True
                wire.name = output_id_ctr + port_dict[wire.port] + wire.idx
                for port in invalid_ports:
                    if 'OUTPUT' in port.direction \
                        and port_dict[port.name] < port_dict[wire.port]:
                        wire.name -= port.length
            except Exception as exc:
                raise RuntimeError("[!] Out wire ID:", wire.name) from exc
        else:
            wire.name = inter_id_ctr
            inter_id_ctr += 1
    for port in port_list:
        if port.name not in visited and not port.invalid:
            print("[!] Missed port:", port.name)

    # First line is "[NUM GATES] [NUM WIRES]"
    preamble = str(len(gate_list)) + " " + str(num_outputs+inter_id_ctr)
    bristol_str = []
    bristol_str.append(preamble)

    # "[NUM INPUTS] [WORDSIZE 1] ... [WORDSIZE N]"
    if num_inputs % 64:
        preamble = str(num_inputs//64+1)
    else:
        preamble = str(num_inputs//64)
    cnt = num_inputs
    while cnt >= 64:
        preamble = preamble + ' 64'
        cnt -= 64
    if cnt:
        preamble = preamble + " " + str(cnt)
    bristol_str.append(preamble)

    # "[NUM OUTPUTS] [WORDSIZE 1] ... [WORDSIZE N]"
    if num_outputs % 64:
        preamble = str(num_outputs//64+1)
    else:
        preamble = str(num_outputs//64)
    cnt = num_outputs
    while cnt >= 64:
        preamble = preamble + ' 64'
        cnt -= 64
    if cnt:
        preamble = preamble + " " + str(cnt)
    bristol_str.append(preamble)
    bristol_str.append('')

    wire_cnt = {}
    gates_written = 0
    while gates_written < len(gate_list):
        for gate in gate_list:
            if gate.done:
                continue
            if len(gate.depends_on) != 0:
                gate_not_ready = False
                for prev_gate in gate.depends_on:
                    if not prev_gate.done:
                        gate_not_ready = True
                        break
                if gate_not_ready:
                    continue
            if gate.function == 'NOT':
                entry = '1 1 ' + str(gate.input_nets[0].name) + ' ' + \
                    str(gate.output_nets[0].name) + ' INV'
            else:
                entry = '2 1 ' + str(gate.input_nets[0].name) + ' ' + \
                    str(gate.input_nets[1].name) + ' ' + \
                    str(gate.output_nets[0].name) + ' ' + gate.function
                wire_cnt[gate.input_nets[1].name] = True
            wire_cnt[gate.input_nets[0].name] = True
            wire_cnt[gate.output_nets[0].name] = True
            bristol_str.append(entry)
            gate.done = True
            gates_written += 1
    print('Finished generating the circuit!')

    bristol_file = open(output_file, 'w')
    for line in bristol_str:
        bristol_file.write(line + '\n')
    bristol_file.close()

    for i in range(num_outputs + inter_id_ctr):
        if i not in wire_cnt:
            print("[!] Missing wire (ID):", i)

if __name__ == '__main__':
    main()
