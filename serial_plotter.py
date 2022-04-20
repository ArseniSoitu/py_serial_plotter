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
    def __init__(self, port, baud):
        self.data_manager = mp.Manager()
        self.buf = mp.Queue()
        self.angles = self.data_manager.dict()
        self.angles[0] = []
        self.angles[1] = []
        self.angles[2] = []
        self.angles[3] = []
        self.angles[4] = []
        self.angles[5] = []
        self.port = port
        self.baudrate = baud
        self.parse_task = mp.Process(target=self.process_parse, args=(self.buf, self.angles,))
        self.plot_task = mp.Process(target=self.process_plot, args=(self.angles,))

    def work(self):
        self.parse_task.start()
        self.plot_task.start()
        self.process_read()

    def process_read_sim(self):
        data = [0x5A, 0xA5, 3,
                0x05, 0x00, 0x00, 0x00, 
                0x0A, 0x00, 0x00, 0x00, 
                0x14, 0x00, 0x00, 0x00, 
                0x00, 0x00]

        data_bytes = bytes(data)
        while True:
            for item in data_bytes:
                self.buf.put(item)
            sleep(0.01)

    def process_read(self):
        with serial.Serial(self.port, self.baudrate) as ser:
            while True:
                data = ser.read(29)
                for item in data:
                    self.buf.put(item)
                sleep(0.01)

    def process_plot(self, angles):
        fig, axs = plt.subplots(2, 3)
        ax = axs.flatten()
        
        while True:
            channel = 0

            for subplt in ax:
                if len(angles[channel]) == 0:
                    pass
                data = angles[channel]
                subplt.cla()
                subplt.set_title(channel)
                subplt.axis(xmin=max(0, len(angles[channel]) - 50), xmax = len(data) + 1)
                x_min = max(0, len(data) - 50)
                x_max = len(data)
                x_values = list(range(x_min, x_max))
                subplt.plot(x_values, data[max(0, len(data) - 50) : ])
                subplt.grid(visible=True, axis='both', which='both', 
                        color='black', linestyle='-', linewidth=0.5)
                channel += 1

            channel %= len(ax)

            plt.pause(0.05)
        
    def process_parse(self, buf, angles_shared):
        local_buf_lst = []
        local_buf_bytes = None

        while True:
            try:
                if buf.qsize() < 29:
                    pass
                
                raw_buf = []
                if buf.get() == 0x5A:
                    if buf.get() == 0xA5:
                        count = buf.get_nowait()
                        dummy = buf.get_nowait()

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
            sleep(0.01)

if __name__ == "__main__":

    port = None
    baud = 0

    if len(sys.argv) != 3:
        sys.exit("Wrong arguments number")

    if 'dev' in sys.argv[1]:
        port = sys.argv[1]
    else:
        sys.exit("Invalid port name")

    try:
        baud = int(sys.argv[2])
    except:
        sys.exit("Invalid baudrate format, should be integer")

    print("Port {} baud {}".format(port, baud))

    dev = Parser(port, baud)
    dev.work()

