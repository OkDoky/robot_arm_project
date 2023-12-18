import serial
import time
import traceback
from threading import Thread, Event
from collections import deque

class ArduinoBridge:
    def __init__(self, PORT="COM1", BUADRATE=9600, AUTOSTART=False):
        self.conn = None
        self.port = PORT
        self.buadrate = BUADRATE

        self.status = deque(maxlen=10)

        self.read_thread = Thread(target=self._status_thread)
        self.read_thread.daemon = True
        self.thread_event = Event()
        if AUTOSTART:
            self.connection()

    def connection(self):
        count = 1
        while True:
            try:
                self.conn = serial.Serial(self.port, self.buadrate, timeout=1)
                self.read_thread.start()
                break
            except Exception:
                print("[ArduinoBridge] fail to get serial connection, %s"%traceback.format_exc())
            if count >= 5:
                print("[ArduinoBridge] fail to connection, check port or buadrate or cable..")
                break
            count += 1
            time.sleep(1)
        return self.conn.is_open
    
    def disconnect(self):
        self.thread_event.set()
        self.conn.close()

    def get_msg(self):
        try:
            status = self.status.pop()
            return status
        except Exception:
            return None
    
    def send_msg(self, msg):
        try:
            self.conn.write(msg.encode())
        except Exception:
            print("[ArduinoBridge] failed to send message.. %s"%traceback.format_exc())

    def _status_thread(self):
        while not self.thread_event.is_set():
            try:
                if self.conn.in_waiting:
                    line = self.conn.readline().decode('utf-8').rstrip()
                    status = []
                    angles = line.split(", ")
                    status = [angles[i].split(':')[1] for i in range(len(angles))]
                    self.status.append(status)
            except Exception:
                print("ArduinoBridge] fail to read data from arduino.., %s"%traceback.format_exc())
            finally:
                time.sleep(0.005)

def test_thread(bridge, thread_event):
    while not thread_event.is_set():
        msg = bridge.get_msg()
        if not msg == None:
            print("current angle is : %s"%msg[0])
        time.sleep(0.1)

if __name__ == "__main__":
    ## 아두이노 연결 class 초기화
    bridge = ArduinoBridge(PORT="/dev/cu.usbserial-1130", BUADRATE=9600)
    
    ## 아두이노와 연결 시도 및 연결상태 확인
    is_conn = bridge.connection()

    ## 0.1초마다 가장 아래 모터를 90도에서 140도 까지 5초간 움직이고, 
    # 다시 반대로 움직이며 현재 각도를 읽어오도록 하는 루틴
    angle = 90
    dt = 0.1
    thread_event = Event()
    read_thread = Thread(target=test_thread, args=(bridge,thread_event))
    read_thread.daemon = True
    read_thread.start()
    for _ in range(50):
        angle += 1
        bridge.send_msg("B: %s"%int(angle))
        time.sleep(dt)
    for _ in range(50):
        angle -= 1
        bridge.send_msg("B: %s"%int(angle))
        time.sleep(dt)
    thread_event.set()
    bridge.disconnect()
    print("done")
    
