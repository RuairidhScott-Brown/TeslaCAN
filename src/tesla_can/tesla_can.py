# Standard imports.
import os
from multiprocessing import Event, Process, Queue
from pathlib import Path
from time import sleep

# 3rd party imports.
import can
import cantools
import pandas as pd


def read_in_excel(path: str | Path) -> pd.DataFrame:
    return pd.read_excel(path)


def read_in_csv(path: str | Path) -> pd.DataFrame:
    return pd.read_csv(path)


def load_dbc_file(dbc_path: Path | str) -> cantools.db.Database | None:
    try:
        db = cantools.database.load_file(db_path)
    except FileNotFoundError:
        print(f"File not found: {dbc_path}")
        return None
    except Exception as e:
        print(f"Error loading DBC file: {e}")
        return None

    return db


class TeslaCANProcess(Process):
    def __init__(self, interface: str, channel: str, db: cantools.db.Database, input_queue: Queue, output_queue: Queue, filtered_messages: pd.DataFrame):
        super().__init__()
        self.__channel = channel
        self.__interface = interface
        self.__db = db
        self.__input_queue = input_queue
        self.__output_queue = output_queue
        self.__filtered_messages = filtered_messages
        self.__stop_event = Event()


    def __filter_can_message(self, message: dict) -> bool:
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
        input_message = bus.recv(timeout=1.0)

        if input_message is None:
            return False

        decoded_message = self.__db.decode_message(input_message.arbitration_id, input_message.data)

        if self.__filter_can_message(decoded_message):
            return False

        self.__input_queue.put(input_message)

        if not self.__output_queue.empty():
            output_message = self.__output_queue.get_nowait()
            bus.send(output_message)

    def stop(self) -> None:
        print("being called")
        self.__stop_event.set()


if __name__ == "__main__":
    input_queue = Queue()
    output_queue = Queue()

    db_path = Path(os.path.abspath(__file__)).parent.parent / "data" / "tesla.dbc"
    messages_path = Path(os.path.abspath(__file__)).parent.parent / "data" / "messages.csv"

    db = cantools.database.load_file(db_path)
    messages_to_be_filtered = read_in_csv(messages_path)["Fruit"].to_list()

    process_1 = TeslaCANProcess("virtual", "test", db, input_queue, output_queue, messages_to_be_filtered)
    process_1.start()
    sleep(10)
    print("Here")
    process_1.stop()
    process_1.join()
    print("Finished")

