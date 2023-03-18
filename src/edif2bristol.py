#!/usr/bin/env python

from enum import Enum
import os
import argparse

gate_counter = 0

InstanceType = Enum('InstanceType', ['Net', 'CellRef', 'Instance', 'Empty'])

def parse_args():
    parser = argparse.ArgumentParser(description='EDIF parser')
    parser.add_argument('--edif', help='path to EDIF file (.edif)', required=True)
    parser.add_argument('--out', help='path to output file', required=False)
    args = parser.parse_args()
    input_file = args.edif
    if not args.edif.endswith(".edif"):
        print("EDIF file should end with '.edif' extension.")
        exit(-1)
    if not os.path.isfile(args.edif):
        print("Input file '" + args.edif + "' does not exist.")
        exit(-2)
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
        self.nets = [""] * self.length

class LogicGate:
    def __init__(self, function, id):
        global gate_counter
        self.function = function
        self.id = id
        self.idx = gate_counter
        self.input_nets = []
        self.output_nets = []
        self.depends_on = []
        self.done = False
        gate_counter += 1

    def set_input_net(self, in_net):
        self.input_nets.append(in_net)
        for i in in_net.left:
            self.depends_on.append(i)

    def set_output_net(self, outNet):
        self.output_nets.append(outNet)

class Net:
    def __init__(self, name):
        self.name = name
        self.left = []
        self.right = []
        self.value = 0
        self.idx = -1
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

        if 'net' in line and 'rename' in line and "$" not in line and flag:
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

        for word in line.split():
            if wiremap_flag:
                prev_word_2 = ""
                for word_2 in prev_line.split():
                    if 'id' in word_2 or 'net' in prev_word_2:
                        temp_name = word_2.strip(')')
                    prev_word_2 = word_2
                if 'portRef' in prev_word:
                    for i in port_list:
                        if i.name == word.strip(')'):
                            if "(instanceRef" in prev_line:
                                i.nets[0] = word.strip(')')
                            else:
                                i.nets[0] = temp_name
                    wiremap_flag = False

            # identify input and output ports
            if interface_flag and "port" in word:
                port_flag = True
            elif interface_flag and port_flag and "array" in word:
                array_flag = True
            elif interface_flag and port_flag and "array" not in word and "port" in prev_word:
                temp_name = word
                bit_size = 1
            elif interface_flag and port_flag and array_flag and not name_flag:
                temp_name = word
                name_flag = True
            elif interface_flag and port_flag and array_flag and name_flag and 'direction' not in word and 'INPUT' not in word and 'OUTPUT' not in word:
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
                index = int(word[word.find("[") + 1:word.find("]")])  # Get index out of name[index]
                for i in port_list:
                    if i.name == word:
                        i.nets[int(index)] = temp_name
                        break
                map_flag = False

            if 'contents' in word:
                interface_flag = False
            if instance_type == InstanceType.Instance and 'id' in word:
                prevID = word
            elif instance_type == InstanceType.CellRef and 'id' in word and flag:
                index = int(word[-1]) - 1
                gate_list.append(LogicGate(cell_list[index], prevID))
            elif instance_type == InstanceType.Net and 'net' in prev_word and 'rename' not in word:
                new_net = Net(word)
                new_net.idx = 0
                new_net.port = word
                net_list.append(new_net)
            elif instance_type == InstanceType.Net and 'rename' in prev_word:
                new_net = Net(word)
                if line.find("[") != -1:
                    new_net.idx = int(line[line.find("[") + 1:line.find("]")])  # Get index out of name[index]
                    gate_name = line[line.find('"') + 1:line.find("[")]         # Get name out of name[index]
                    new_net.port = gate_name
                net_list.append(new_net)
            elif instance_type == InstanceType.Net and (word == "Y" or word == "q" or word == "Q"):
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
            for leftGate in net.left:
                if leftGate.id == gate.id:
                    gate.set_output_net(net)
            for rightGate in net.right:
                if rightGate.id == gate.id:
                    gate.set_input_net(net)

    # First line is "[NUM GATES] [NUM WIRES]"
    preamble = str(len(gate_list)) + " " + str(len(net_list))
    bristol_str = []
    bristol_str.append(preamble)

    # Next, we specify the number of inputs/outputs followed by the wordsizes
    inter_id_ctr = 0
    output_id_ctr = 0
    input_port_len = []
    output_port_len = []
    for port in port_list:
        if 'INPUT' in port.direction:
            input_port_len.append(port.length)
            inter_id_ctr += port.length
        else:
            output_port_len.append(port.length)
            output_id_ctr += port.length

    output_id_ctr = len(net_list) - output_id_ctr
    for wire in net_list:
        if wire.left == []:     # if input
            wire.name = port_dict[wire.port] + wire.idx
        elif wire.right == []:  # if output
            wire.name = output_id_ctr + port_dict[wire.port] + wire.idx
        else:
            wire.name = inter_id_ctr
            inter_id_ctr += 1
        
    # "[NUM INPUTS] [WORDSIZE 1] ... [WORDSIZE N]"
    preamble = str(len(input_port_len))
    for i in input_port_len:
        preamble = preamble + " " + str(i)
    bristol_str.append(preamble)

    # "[NUM OUTPUTS] [WORDSIZE 1] ... [WORDSIZE N]"
    preamble = str(len(output_port_len))
    for i in output_port_len:
        preamble = preamble + " " + str(i)
    bristol_str.append(preamble)
    bristol_str.append('')

    gates_written = 0
    while gates_written < len(gate_list):
        for gate in gate_list:
            if gate.done:
                continue
            if len(gate.depends_on) != 0:
                gate_not_ready = False
                for prevGate in gate.depends_on:
                    if not prevGate.done:
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
            bristol_str.append(entry)
            gate.done = True
            gates_written += 1
    print('Finished generating the circuit!')

    bristol_file = open(output_file, 'w')
    for line in bristol_str:
        bristol_file.write(line + '\n')
    bristol_file.close()

if __name__ == '__main__':
    main()
