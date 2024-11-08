class GBN_sender:
    def __init__(
        self,
        input_file,
        window_size,
        packet_len,
        nth_packet,
        send_queue,
        ack_queue,
        timeout_interval,
        logger,
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
    def __init__(self, output_file, send_queue, ack_queue, logger):
        pass

    def process_packet(self, packet):
        pass

    def write_to_file(self):
        pass

    def run(self):
        pass
