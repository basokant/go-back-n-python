import queue
import logging
from typing import ByteString


class GBN_sender:
    def __init__(
        self,
        input_file: str,
        window_size: int,
        packet_len: int,
        nth_packet: int,
        send_queue: queue.Queue[ByteString],
        ack_queue: queue.Queue[int],
        timeout_interval: int,
        logger: logging.Logger,
    ):
        pass

    def prepare_packets(self):
        pass

    def send_packets(self):
        pass

    def send_next_packet(self):
        pass

    def check_timers(self):
        pass

    def receive_acks(self):
        pass

    def run(self):
        pass


class GBN_receiver:
    def __init__(
        self,
        output_file: str,
        send_queue: queue.Queue[ByteString],
        ack_queue: queue.Queue[int],
        logger: logging.Logger,
    ):
        pass

    def process_packet(self, packet):
        pass

    def write_to_file(self):
        pass

    def run(self):
        pass
