# Standard imports.
import os
import multiprocessing as mp
from pathlib import Path
from time import sleep
from typing import Any, Optional
from queue import Queue

# 3rd party imports.
import can
import cantools
import pandas as pd
import os
import sys


def read_in_excel(path: str | Path) -> pd.DataFrame:
    return pd.read_excel(path)


def read_in_ids_to_filter(path: str | Path, name: str = "IDs") -> list:
    return [int(id, 16) for id in read_in_csv(path)[name].to_list()]


def read_in_csv(path: str | Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str)


def load_dbc_file(dbc_path: Path | str) -> cantools.db.Database | None:
    try:
        db = cantools.database.load_file(dbc_path)
    except FileNotFoundError:
        print(f"File not found: {dbc_path}")
        return None
    except Exception as e:
        print(f"Error loading DBC file: {e}")
        return None

    return db


class TeslaCANProcess(mp.Process):
    def __init__(
        self, 
        interface: str, 
        channel: str, 
        db: cantools.db.Database, 
        input_queue: Optional[mp.Queue] = None, 
        output_queue: Optional[mp.Queue] = None, 
        filtered_messages: list = list(),
    ):
        super().__init__()
        self.__channel = channel
        self.__interface = interface
        self.__db = db
        self.__input_queue = input_queue
        self.__output_queue = output_queue
        self.__filtered_messages = filtered_messages
        self.__stop_event = mp.Event()


    def __filter_can_message(self, message: can.Message) -> bool:
        can_id = message.arbitration_id
        if can_id in self.__filtered_messages:
            return True
        else:
            return False

    @staticmethod
    def create_can_interface(interface: str, channel: str) -> can.BusABC | None:
        try:
            can_interface = can.interface.Bus(channel=channel, interface=interface)
        except Exception as e:
            print(f"Error creating CAN interface: {e}")
            return None

        return can_interface

    @staticmethod
    def close_can_interface(bus: can.BusABC) -> None:
        bus.shutdown()


    def run(self) -> None:
        bus = self.create_can_interface(channel=self.__channel, interface=self.__interface)
        while True:
            if self.__stop_event.is_set():
                self.close_can_interface(bus)
                break

            if not self.process_can_message(bus):
                continue

    def process_can_message(self, bus: can.BusABC) -> bool:
        input_message = bus.recv(timeout=0.1)
        print(self.__channel, "RECV", input_message)

        if self.__output_queue and not self.__output_queue.empty():
            output_message = self.__output_get(wait=False)
            # print(self.__channel, "SEND", output_message)
            bus.send(output_message)

        if input_message is None:
            return False

        # decoded_message = self.__db.decode_message(input_message.arbitration_id, input_message.data)
        # print(self.__channel, "RECV", input_message)

        if self.__filter_can_message(input_message):
            return False

        self.__input_put(input_message)


    def stop(self) -> None:
        self.__stop_event.set()


    def start_logging(self) -> None:
        pass

    def __input_put(self, data) -> None:
        if self.__input_queue is None:
            return None
        else:
            return self.__input_queue.put(data)

    def __input_get(self) -> Any | None:
        if self.__input_queue is None:
            return None
        else:
            return self.__input_queue.get(timeout=0.1)

    def __output_put(self, data) -> None:
        if self.__output_queue is None:
            return None
        else:
            return self.__output_queue.put(data)

    def __output_get(self, wait: bool = True) -> Any | None:
        if self.__output_queue is None:
            return None
        else:
            return self.__output_queue.get(wait)

    def __empty_inptut_queue(self) -> None:
        if self.__input_queue is not None:
            while not self.__input_queue.empty():
                self.__input_queue.get()
        else:
            return None

    def __empty_output_queue(self) -> None:
        if self.__output_queue is not None:
            while not self.__output_queue.empty():
                self.__output_queue.get()
        else:
            return None


    def empty(self) -> None:
        self.__empty_inptut_queue()
        self.__empty_output_queue()



if __name__ == "__main__":
    input_queue = mp.Queue()
    output_queue = mp.Queue()

    db_path = Path(os.path.abspath(__file__)).parent.parent.parent / "data" / "tesla.dbc"
    messages_path = Path(os.path.abspath(__file__)).parent.parent.parent / "data" / "messages.csv"

    db = cantools.database.load_file(db_path)
    messages_to_be_filtered = read_in_csv(messages_path)["IDs"].to_list()

    process_1 = TeslaCANProcess("pcan", "PCAN_USBBUS2", db, input_queue, output_queue, messages_to_be_filtered)
    # process_2 = TeslaCANProcess("pcan", "PCAN_USBBUS1", db, output_queue, input_queue, messages_to_be_filtered)

    try:
        process_1.start()
        # process_2.start()

        print("Start")
        sleep(12)
        process_1.stop()
        # process_2.stop()

        # process_2.empty()
        process_1.empty()
        sleep(2)
        process_1.join()
        # process_2.join()

    except KeyboardInterrupt:
        print("*"*50)
        process_1.stop()
        # process_2.stop()

        # process_2.empty()
        process_1.empty()

        process_1.join()
        # process_2.join()
    print("Finished")

