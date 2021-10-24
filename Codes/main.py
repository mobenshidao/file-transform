import argparse
import time
import math
import os
import struct
from socket import *
from multiprocessing import Process
from os.path import join, isfile, getmtime, getsize
import sys

BLOCK = 512 * 1024
UDP = 26543
TCP = 23456

global gl_se_ip1
global gl_se_ip2


def parse():
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--ip', action='store', required=True, dest='ip', help='The ip of peer', type=str)
    return parser.parse_args()


def get_two_ip(parser):
    input_ip = parser.ip
    input_ip = input_ip.split(',')
    global gl_se_ip1
    gl_se_ip1 = input_ip[0]
    global gl_se_ip2
    gl_se_ip2 = input_ip[1]
    return gl_se_ip1, gl_se_ip2


def traverse(dir_path):
    file_list = []
    file_folder_list = os.listdir(dir_path)
    for file_folder_name in file_folder_list:
        if os.path.isfile(join(dir_path, file_folder_name)):
            file_list.append(join(dir_path, file_folder_name))
            change_size = 1
            print('file check')
            while change_size != 0:
                a = os.path.getsize(join(dir_path, file_folder_name))
                time.sleep(1)
                b = os.path.getsize(join(dir_path, file_folder_name))
                change_size = b - a
        else:
            file_list.extend(traverse(join(dir_path, file_folder_name)))
    return file_list


def print_file_list(file_list):
    for f in file_list:
        print(f, ': mtime', getmtime(f), 'size', getsize(f))


def check_file(dir_path):
    msg_file_list = []
    while True:
        f = open('own_file.log', 'a')
        ed_time_list1 = []
        ed_time_list2 = []
        file_list1 = traverse(dir_path)
        for file in file_list1:
            ed_time_list1.append(getmtime(file))
        time.sleep(0.1)
        g = open('other_file.log', 'r')
        files = g.read()
        g.close()
        other_new_file = files.split('\n')
        other_new_file.remove('')
        for message in other_new_file:
            message_list = message.split(' ')
            msg_file_list.append(message_list[0])
        file_list2 = traverse(dir_path)
        for file in file_list2:
            ed_time_list2.append(getmtime(file))
        for ed_time in ed_time_list2:
            if ed_time in ed_time_list2 and ed_time not in ed_time_list1:
                index = ed_time_list2.index(ed_time)
                if file_list2[index] not in msg_file_list:
                    f.write(file_list2[index] + ' ')
                    f.write(str(getmtime(file_list2[index])) + ' ')
                    ed_time_list2[index] = 0
        f.close()


def conn_by_UDP(ip):
    udp_socket = socket(AF_INET, SOCK_DGRAM)
    udp_socket.bind(('', UDP))
    ask = '0'
    respond = '1'
    last = '2'
    while True:
        udp_socket.sendto(ask.encode(), (ip, UDP))
        message, _ = udp_socket.recvfrom(3)
        if message.decode() == ask:
            udp_socket.sendto(respond.encode(), (ip, UDP))
        elif message.decode() == respond:
            print(ip + ' is online')
            print('I am server')
            udp_socket.sendto(last.encode(), (ip, UDP))
            connectionSocket = tcp_server()
            return connectionSocket
        else:
            print(ip + ' is online')
            print('I am client')
            connectionSocket = tcp_client(ip)
            return connectionSocket


def tcp_client(ip):
    clientSocket = socket(AF_INET, SOCK_STREAM)
    clientSocket.connect((ip, TCP))
    print('The client is ready')
    return clientSocket


def tcp_server():
    server_socket = socket(AF_INET, SOCK_STREAM)
    server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)  # allowed to use port in using
    server_socket.bind(('', TCP))
    server_socket.listen(10)
    connectionSocket, addr = server_socket.accept()
    print('The sever is ready')
    return connectionSocket


def send_new_file(filename):
    step_code = 0
    file_size = getsize(filename)
    total_block_num = math.ceil(file_size / BLOCK)
    index = 2000
    len_filename = len(filename.encode())
    header = struct.pack('!IIIII', step_code, total_block_num, file_size, index, len_filename)
    header_length = len(header)
    return struct.pack('!I', header_length) + header + filename.encode()


def get_file_block(filename, block_index):
    f = open(filename, 'rb')
    f.seek(block_index * BLOCK)
    file_block = f.read(BLOCK)
    f.close()
    return file_block


def make_get_file_block(filename, total_block_num, file_size, index, length_filename):
    step_code = 1
    print('total block is'+str(total_block_num))
    msg_header = struct.pack('!IIIII', step_code, total_block_num, file_size, index, length_filename)
    header_length = len(msg_header)
    return struct.pack('!I', header_length) + msg_header + filename.encode()


def keep_recv(connect: socket):
    while True:
        try:
            msg = connect.recv(24)
        except ConnectionResetError:
            socket3 = conn_by_UDP(gl_se_ip1)
            msg = connect.recv(24)
            msg_parse(msg, socket3)

        print('has recived')
        return_smg = msg_parse(msg, connect)
        if return_smg != bytes(0):
            connect.send(return_smg)
            print('has send')


def send_own_file(connect: socket):
    file_list2 = []
    while True:
        file_list1 = []
        ed_time_list1 = []
        f = open('own_file.log', 'r')
        files = f.read()
        own_file_list1 = files.split(' ')
        own_file_list1.remove('')
        for num in range(len(own_file_list1)):
            if (num % 2) == 0:
                file_list1.append(own_file_list1[num])
            else:
                ed_time_list1.append(own_file_list1[num])
        for file in file_list1:
            if file in file_list1 and file not in file_list2:
                print(file)
                mes = send_new_file(file)
                connect.send(mes)
        file_list2 = file_list1[:]


def msg_parse(msg, connect: socket):
    header_length_b = msg[:4]
    header_length = b''
    try:
        header_length = struct.unpack('!I', header_length_b)[0]
    except struct.error:
        socket3 = conn_by_UDP(gl_se_ip1)
        msg = connect.recv(24)
        msg_parse(msg, socket3)

    header_b = msg[4:4 + header_length]
    step_code, total_block_number, file_size, index, len_filename = struct.unpack('!IIIII', header_b[:20])
    print('step code code is ' + str(step_code) + ' index is ' + str(index) + ' len_filename is ' + str(len_filename))

    if step_code == 0:
        print('step is 0')
        buffer_of_filename = b''
        while len(buffer_of_filename) < len_filename:
            buffer_of_filename += connect.recv(len_filename)
        filename = buffer_of_filename[0:].decode()
        f = open('other_file.log', 'a')
        f.write(filename + ' ' + str(total_block_number) + ' ' + str(index) + '\n')
        f.close()
        dir = filename.split('/')
        if len(dir) > 2:
            try:
                os.makedirs(join(dir[0], dir[1]))
            except FileExistsError:
                None
        g = open(filename, 'wb')
        g.close()
        meg = make_get_file_block(filename, total_block_number, file_size, 0, len_filename)
        return meg

    if step_code == 1:
        print('step is 1')
        buffer_of_filename = b''
        while len(buffer_of_filename) < len_filename:
            buffer_of_filename += connect.recv(len_filename)
        filename = buffer_of_filename[0:].decode()
        print(filename)
        step_code = 2
        if index < total_block_number:
            file_block = get_file_block(filename, index)
            header = struct.pack('!IIIII', step_code, total_block_number, file_size, index, len_filename)
            header_length = len(header + file_block)
            print('I have send ' + str(index) + ' block!')
            return struct.pack('!I', header_length) + header + filename.encode() + file_block
        else:
            print('trans finish!')
            return bytes(0)

    if step_code == 2:
        print('step 2')
        buffer_of_filename = b''
        while len(buffer_of_filename) < len_filename:
            buffer_of_filename += connect.recv(len_filename)
        filename = buffer_of_filename[0:].decode()
        print(filename)
        buffer_of_block = b''
        if file_size < BLOCK:
            buffer_of_block = connect.recv(file_size)
        while len(buffer_of_block) < BLOCK and len(buffer_of_block) != file_size:
            buffer_of_block += connect.recv(BLOCK - len(buffer_of_block))
            print(len(buffer_of_block))
            if len(buffer_of_block) == file_size - (BLOCK * (total_block_number - 1)):
                break
        print('block recv finish!')
        print(len(buffer_of_block))
        g = open(filename, 'ab')
        g.write(buffer_of_block)
        print('I have write ' + str(index) + ' block!')
        g.close()
        l = open('other_file.log', 'r')
        files = l.read()
        l.close()
        other_new_file = files.split('\n')
        other_new_file.remove('')
        for message in other_new_file:
            message_list = message.split(' ')
            if message_list[0] == filename:
                message_list[2] = str(index)
                change = message_list[0] + ' ' + message_list[1] + ' ' + message_list[2]
                message_index = other_new_file.index(message)
                other_new_file[message_index] = change
                k = open('other_file.log', 'w')
                for m in other_new_file:
                    k.write(m + '\n')
                k.close()
        return_index = index + 1
        msg = make_get_file_block(filename, total_block_number, file_size, return_index, len_filename)
        return msg


if __name__ == '__main__':
    parser = parse()
    gl_se_ip1, gl_se_ip2 = get_two_ip(parser)
    print(gl_se_ip1)
    print(gl_se_ip2)
    f = open('own_file.log', 'w')
    g = open('other_file.log', 'a')
    f.close()
    g.close()
    check_file_thread = Process(target=check_file, args=('share',))
    check_file_thread.start()
    connectSocket1 = conn_by_UDP(gl_se_ip1)
    ip1_recv_thread = Process(target=keep_recv, args=(connectSocket1,))
    ip1_recv_thread.start()
    ip1_send_thread = Process(target=send_own_file, args=(connectSocket1,))
    ip1_send_thread.start()

    connectSocket2 = conn_by_UDP(gl_se_ip2)
    ip2_recv_thread = Process(target=keep_recv, args=(connectSocket2,))
    ip2_recv_thread.start()
    ip2_send_thread = Process(target=send_own_file, args=(connectSocket2,))
    ip2_send_thread.start()
