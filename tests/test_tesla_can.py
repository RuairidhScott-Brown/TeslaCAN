# Standard
import multiprocessing as mp
import os
import time
from pathlib import Path

# 3rd Party
import can
import cantools
import pandas as pd
import pytest
from can.interfaces.udp_multicast import UdpMulticastBus

# Local
from tesla_can.tesla_can import TeslaCANProcess


def test_tesla_can_process_recieves_messages() -> None:
    interface = "udp_multicast"
    channel = UdpMulticastBus.DEFAULT_GROUP_IPv6
    queue_input = mp.Queue()
    queue_output = mp.Queue()
    current_dir = Path(os.path.dirname(os.path.abspath(__file__))).parent
    dbc_file_path = current_dir / "data" / "tesla.dbc"
    db = cantools.database.load_file(dbc_file_path)
    filtered_messages = pd.DataFrame({"Fruit": ["Banans", "Apples"]})

    process =  TeslaCANProcess(interface, channel, db, queue_input, queue_output, filtered_messages)
    process.start()
    bus1 = can.interface.Bus(channel, interface=interface)
    msg1 = can.Message(arbitration_id=0xabcde, data=[1,2,3])
    time.sleep(2)
    bus1.send(msg1)
    message = queue_output.get()
    print(message)
    process.stop()


if __name__ == "__main__":
    test_tesla_can_process_recieves_messages()
