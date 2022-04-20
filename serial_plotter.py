from threading import Thread
import numpy as np
import matplotlib.pyplot as plt
import serial
import multiprocessing as mp
import queue
from time import sleep
import sys
from time import perf_counter


class Parser:
    def __init__(self):
        self.data_manager = mp.Manager()
        self.buf = mp.Queue()
        self.data_buf = []
        self.is_finished = False
        self.is_plot_finished = False
        self.angles = self.data_manager.dict()
        self.angles[0] = []
        self.angles[1] = []
        self.angles[2] = []
        self.angles[3] = []
        self.angles[4] = []
        self.angles[5] = []
        self.parse_task = mp.Process(target=self.process_parse, args=(self.buf, self.angles,))
        self.plot_task = mp.Process(target=self.process_plot, args=(self.angles,))

    def work(self):
        self.parse_task.start()
        self.plot_task.start()
        self.process_read_sim()

    def process_read_sim(self):
        data = [0x5A, 0xA5, 0x05, 0x00, 0x00, 0x00, 0x05, 0x00, 0x00, 0x00, 0x05, 0x00, 0x00, 0x00]
        data_bytes = bytes(data)
        while True:
            for item in data_bytes:
                self.buf.put(item)
            sleep(0.1)

    def process_read(self):
        with serial.Serial('/dev/ttyUSB0', 115200) as ser:
            while True:
                data = ser.read(28)
                for item in data:
                    self.buf.put(item)
                sleep(0.1)

    def process_plot(self, angles):
        count = 0
        x = []
        
        while True:
            plt.cla()
            plt.xlim(left = max(0, len(angles['roll']) - 50), right = len(angles['roll']) + 1)
            plt.plot(list(range(max(0, len(angles['roll']) - 50), len(angles['roll']) - 1)), angles['roll'][max(0, len(angles['roll']) - 50):-1])
            plt.grid(visible=True, axis='both', which='both', color='r', linestyle='-', linewidth=0.5)

            count +=1
            plt.pause(0.05)
        
    def process_parse(self, buf, angles_shared):
        rolls = angles_shared['roll']
        pitchs = angles_shared['pitch']
        yaws = angles_shared['yaw']
        while True:
            try:
                raw_buf = []
                if buf.get() == 0x5A:
                    if buf.get() == 0xA5:
                        count = buf.get_nowait()

                        for channel in range(count):
                            for k in range(4):
                                raw_buf.append(int(hex(buf.get_nowait()), 16))
                            data = angles_shared[channel]
                            data.append(float(int.from_bytes(bytearray(raw_buf), byteorder='little', signed=True))/100.0)
                            raw_buf.clear()
                            angles_shared[channel] = data

                        crc16_low = buf.get_nowait()
                        crc16_high = buf.get_nowait()

            except queue.Empty:
                pass
            sleep(0.1)

if __name__ == "__main__":
    dev = Parser()
    dev.work()

