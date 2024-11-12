import queue
import logging
import textwrap
import threading
import time
from typing import Union

SEQ_NUM_LEN = 16


def get_seq_num(packet: str):
    return int(packet[-SEQ_NUM_LEN:], 2)


def get_data(packet: str) -> str:
    return packet[:-SEQ_NUM_LEN]


class GBN_sender:
    def __init__(
        self,
        input_file: str,
        window_size: int,
        packet_len: int,
        nth_packet: int,
        send_queue: queue.Queue[Union[str, None]],
        ack_queue: queue.Queue[int],
        timeout_interval: int,
        logger: logging.Logger,
    ):
        self.input_file = input_file

        self.window_size = window_size
        self.packet_len = packet_len
        self.packet_data_len = packet_len - SEQ_NUM_LEN
        self.nth_packet = nth_packet
        self.sent_packet_num = 1

        self.send_queue = send_queue
        self.ack_queue = ack_queue
        self.timeout_interval = timeout_interval

        self.logger = logger.getChild("Sender")

        self.base = 0
        self.packets = self.prepare_packets()
        self.acks_list = [False for _ in self.packets]
        self.packet_timers = [0.0 for _ in self.packets]
        self.dropped_list: list[int] = []

        logger.info(
            f"{len(self.packets)} packets created, Window size: {self.window_size}, Packet length: {self.packet_len}, Nth packet to be dropped: {self.nth_packet}, Timeout interval: {self.timeout_interval}"
        )

    def prepare_packets(self) -> list[str]:
        packets = []

        with open(self.input_file, "r") as f:
            data = f.read()
            binary_data = "".join([format(ord(c), "08b") for c in data])

            packet_data = textwrap.wrap(binary_data, self.packet_data_len)
            packets = [
                d + format(i, f"0{SEQ_NUM_LEN}b") for i, d in enumerate(packet_data)
            ]

        return packets

    def send_packet(self, packet: str):
        seq_num = get_seq_num(packet)
        self.logger.info(f"sending packet {seq_num}")

        is_nth_packet = self.sent_packet_num == self.nth_packet
        self.packet_timers[seq_num] = time.time()

        if is_nth_packet and seq_num not in self.dropped_list:
            self.dropped_list.append(seq_num)
            self.logger.info(f"packet {seq_num} dropped")
            self.sent_packet_num = 1
            return

        self.sent_packet_num += 1
        self.send_queue.put(packet)

    def send_packets(self):
        start = self.base
        end = self.base + self.window_size
        sliding_window = self.packets[start:end]

        for packet in sliding_window:
            self.send_packet(packet)

    def send_next_packet(self):
        self.base += 1
        next_idx = self.base + self.window_size - 1
        if 0 > next_idx or next_idx > len(self.packets) - 1:
            return

        next_packet = self.packets[next_idx]
        self.send_packet(next_packet)

    def check_timers(self) -> bool:
        start = self.base
        end = self.base + self.window_size
        sliding_window = self.packets[start:end]
        packet_timers = self.packet_timers[start:end]

        for packet, timer in zip(sliding_window, packet_timers):
            seq_num = get_seq_num(packet)
            elapsed = time.time() - timer

            if timer != 0.0 and elapsed >= self.timeout_interval:
                self.logger.info(f"packet {seq_num} timed out")
                return True

        return False

    def receive_acks(self):
        while not self.acks_list[-1]:
            seq_num = self.ack_queue.get()

            already_ack = self.acks_list[seq_num]
            if already_ack:
                self.logger.info(f"ack {seq_num} received, Ignoring")
                self.ack_queue.task_done()
                continue

            self.logger.info(f"ack {seq_num} received")
            self.acks_list[seq_num] = True
            self.packet_timers[seq_num] = 0

            self.send_next_packet()
            self.ack_queue.task_done()

    def run(self):
        self.send_packets()
        receive_acks_thread = threading.Thread(target=self.receive_acks)
        receive_acks_thread.start()

        while self.base < len(self.packets):
            timeout = self.check_timers()
            if timeout:
                self.send_packets()

        receive_acks_thread.join()
        self.logger.info("All packets have been sent and acknowledgements processed")
        self.send_queue.put(None)


class GBN_receiver:
    def __init__(
        self,
        output_file: str,
        send_queue: queue.Queue[Union[str, None]],
        ack_queue: queue.Queue[int],
        logger: logging.Logger,
    ):
        self.output_file = output_file
        self.send_queue = send_queue
        self.ack_queue = ack_queue
        self.logger = logger.getChild("Receiver")

        self.packet_list: list[str] = []
        self.expected_seq_num: int = 0

    def process_packet(self, packet: str):
        seq_num = get_seq_num(packet)
        if seq_num != self.expected_seq_num:
            self.ack_queue.put(self.expected_seq_num - 1)
            self.logger.info(f"packet {seq_num} received out of order")
            return False

        self.packet_list.append(packet)
        self.ack_queue.put(seq_num)
        self.expected_seq_num += 1
        self.logger.info(f"packet {seq_num} received")
        return True

    def write_to_file(self):
        packet_data = [get_data(packet) for packet in self.packet_list]
        binary_data = "".join(packet_data)
        data = "".join([chr(int(byte, 2)) for byte in textwrap.wrap(binary_data, 8)])

        with open(self.output_file, "w") as f:
            f.write(data)

    def run(self):
        while self.send_queue:
            packet = self.send_queue.get()
            if packet is None:
                self.send_queue.task_done()
                break

            self.process_packet(packet)
            self.send_queue.task_done()

        self.write_to_file()
