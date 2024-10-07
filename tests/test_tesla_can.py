# Standard
import multiprocessing as mp
import os
import time
from pathlib import Path
import random

# 3rd Party
import can
import cantools
import pytest
from can.interfaces.udp_multicast import UdpMulticastBus

# Local
from tesla_can.tesla_can import TeslaCANProcess
from tesla_can.tesla_can import read_in_ids_to_filter


def test_tesla_can_process_recieves_messages() -> None:
    interface = "udp_multicast"
    channel = UdpMulticastBus.DEFAULT_GROUP_IPv6
    queue_input = mp.Queue()
    queue_output = mp.Queue()
    current_dir = Path(os.path.dirname(os.path.abspath(__file__))).parent
    dbc_file_path = current_dir / "data" / "tesla.dbc"
    db = cantools.database.load_file(dbc_file_path)
    filtered_messages = [0xaaaaa, 0xbbbbb, 0xbbbbb]
    n = 10

    process =  TeslaCANProcess(interface, channel, db, queue_input, queue_output, filtered_messages)
    
    bus = can.interface.Bus(channel, interface=interface)
    messages = [can.Message(arbitration_id=0xabcde, data=[i]) for i in range(n)]

    process.start()
    for i in range(n):
        time.sleep(0.1)
        bus.send(messages[i])

    process.stop()

    process.close_can_interface(bus)

    for i in range(n):
        output_message = queue_input.get()
        assert output_message.arbitration_id == messages[i].arbitration_id
        assert output_message.data == messages[i].data


def test_tesla_can_process_filters_messages() -> None:
    interface = "udp_multicast"
    channel = UdpMulticastBus.DEFAULT_GROUP_IPv6
    queue_input = mp.Queue()
    queue_output = mp.Queue()
    current_dir = Path(os.path.dirname(os.path.abspath(__file__))).parent
    dbc_file_path = current_dir / "data" / "tesla.dbc"
    db = cantools.database.load_file(dbc_file_path)
    filtered_messages = [0xbbbbb]

    process =  TeslaCANProcess(interface, channel, db, queue_input, queue_output, filtered_messages)
    
    bus = can.interface.Bus(channel, interface=interface)

    message1 = can.Message(arbitration_id=0xaaaaa, data=[1])
    message2 = can.Message(arbitration_id=0xbbbbb, data=[1])
    message3 = can.Message(arbitration_id=0xccccc, data=[1])

    process.start()
    
    time.sleep(0.1)
    bus.send(message1)
    time.sleep(0.1)
    bus.send(message2)
    time.sleep(0.1)
    bus.send(message3)

    process.stop()

    process.close_can_interface(bus)
    
    output_message = queue_input.get()
    assert output_message.arbitration_id == message1.arbitration_id
    assert output_message.data == message1.data

    output_message = queue_input.get()
    assert output_message.arbitration_id == message3.arbitration_id
    assert output_message.data == message3.data

    assert queue_input.empty() == True


def test_read_in_ids_to_be_filtered() -> None:
    current_dir = Path(os.path.dirname(os.path.abspath(__file__))).parent
    file_path = current_dir / "data" / "messages.csv"
    ids = [0xaaaaa, 0xbbbbb, 0xbbbbb]
    data = read_in_ids_to_filter(file_path)

    assert len(ids) == len(data)
    for i in range(len(ids)):
        assert ids[i] == data[i]


def test_sending_messages() -> None:
    interface = "udp_multicast"
    channel = UdpMulticastBus.DEFAULT_GROUP_IPv6
    queue_input = mp.Queue()
    queue_output = mp.Queue()
    current_dir = Path(os.path.dirname(os.path.abspath(__file__))).parent
    dbc_file_path = current_dir / "data" / "tesla.dbc"
    db = cantools.database.load_file(dbc_file_path)
    filtered_messages = [0xaaaaa]

    process =  TeslaCANProcess(interface, channel, db, queue_input, queue_output, filtered_messages)
    
    bus = can.interface.Bus(channel, interface=interface)

    message2 = can.Message(arbitration_id=0xbbbbb, data=[1])

    process.start()
    
    queue_output.put(message2)
    returned_message = bus.recv(timeout=1.0)

    process.stop()

    process.close_can_interface(bus)
    
    assert returned_message.arbitration_id == message2.arbitration_id
    assert returned_message.data == message2.data


# def test_two_processes() -> None:
#     interface = "udp_multicast"
    
#     channel1 = UdpMulticastBus.DEFAULT_GROUP_IPv6
#     channel2 = UdpMulticastBus.DEFAULT_GROUP_IPv4

#     queue_input = mp.Queue()
#     queue_output = mp.Queue()

#     current_dir = Path(os.path.dirname(os.path.abspath(__file__))).parent
#     dbc_file_path = current_dir / "data" / "tesla.dbc"
#     db = cantools.database.load_file(dbc_file_path)
    
#     process1 =  TeslaCANProcess(interface, channel1, db, queue_input, queue_output)
#     process2 =  TeslaCANProcess(interface, channel2, db, queue_output, queue_input)
    
#     bus1 = can.interface.Bus(channel1, interface=interface)
#     bus2 = can.interface.Bus(channel2, interface=interface)

#     message1 = can.Message(arbitration_id=0xaaaaa, data=[1])
#     message2 = can.Message(arbitration_id=0xbbbbb, data=[2])

#     process1.start()
#     process2.start()
    
#     time.sleep(0.1)
#     bus1.send(message1)
#     time.sleep(0.1)
#     returned_message1 = bus2.recv(timeout=0.1)
#     test = bus1.recv(timeout=0.1)
    
#     # time.sleep(1)
#     # bus2.send(message2)
#     # # print(message2)
#     # returned_message2 = bus1.recv(timeout=0.1)
#     # # print(returned_message2)


#     process1.stop()
#     process2.stop()

#     process1.close_can_interface(bus1)
#     # process2.close_can_interface(bus2)

#     # assert returned_message1.arbitration_id == message1.arbitration_id
#     # assert returned_message1.data == message1.data 

#     # assert returned_message2.arbitration_id == message2.arbitration_id
#     # assert returned_message2.data == message2.data 



if __name__ == "__main__":
    test_two_processes()
