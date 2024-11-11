import queue
import logging
import textwrap
import time

SEQ_NUM_LEN = 16


def get_seq_num(packet: str):
    return int(packet[:-SEQ_NUM_LEN], 2)


class GBN_sender:
    def __init__(
        self,
        input_file: str,
        window_size: int,
        packet_len: int,
        nth_packet: int,
        send_queue: queue.Queue[str],
        ack_queue: queue.Queue[int],
        timeout_interval: int,
        logger: logging.Logger,
    ):
        self.input_file = input_file

        self.window_size = window_size
        self.packet_len = packet_len
        self.packet_data_len = packet_len - SEQ_NUM_LEN
        self.nth_packet = nth_packet

        self.send_queue = send_queue
        self.ack_queue = ack_queue
        self.timeout_interval = timeout_interval

        self.logger = logger

        self.base = 0
        self.packets = self.prepare_packets()
        self.acks_list = [False for _ in self.packets]
        self.packet_timers = [0.0 for _ in self.packets]
        self.dropped_list: list[int] = []

    def prepare_packets(self) -> list[str]:
        packets = []

        with open(self.input_file, "r") as f:
            data = f.read()
            binary_data = "".join([bin(ord(c)).zfill(8) for c in data])

            packet_data = textwrap.wrap(binary_data, self.packet_data_len)
            packets = [d + bin(i).zfill(SEQ_NUM_LEN) for i, d in enumerate(packet_data)]

        return packets

    def send_packets(self):
        start = self.base
        end = self.base + self.window_size
        sliding_window = self.packets[start:end]

        for packet in sliding_window:
            seq_num = get_seq_num(packet)
            if seq_num == self.nth_packet and seq_num not in self.dropped_list:
                self.dropped_list.append(seq_num)
                self.logger.info(f"packet {seq_num} dropped")
                continue

            if seq_num in self.dropped_list:
                continue

            self.logger.info(f"sending packet {seq_num}")

            self.packet_timers[seq_num] = time.time()
            self.send_queue.put(packet)

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
        send_queue: queue.Queue[str],
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
