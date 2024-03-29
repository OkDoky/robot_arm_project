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

        self.thread_event = Event()
        if AUTOSTART:
            self.connection()

    def connection(self):
        ## 아두이노와 연결 시도, 최대 5회의 시도 후 연결 실패시 재시도 중지
        if not self.conn == None:
            self.disconnect()
        self.thread_event.clear()
        count = 1
        while True:
            try:
                self.conn = serial.Serial(self.port, self.buadrate, timeout=1)
                self.read_thread = Thread(target=self._status_thread)
                self.read_thread.daemon = True
                self.read_thread.start()
                return True
            except Exception:
                print("[ArduinoBridge] fail to get serial connection, %s"%traceback.format_exc())
            if count >= 5:
                return False
            count += 1
            time.sleep(1)
    
    def disconnect(self):
        self.thread_event.set()
        self.conn.close()
        self.conn = None

    def get_msg(self):
        if not len(self.status) == 0:
            status = self.status.pop()
            return status
        else:
            return None
    
    def send_msg(self, msg):
        try:
            print("[ArduinoBridge] control msg : %s"%msg)
            self.conn.write(msg.encode())
        except Exception:
            print("[ArduinoBridge] failed to send message.. %s"%traceback.format_exc())

    def _status_thread(self):
        print("[ArduinoBridge] start status thread")
        while not self.thread_event.is_set():
            if self.conn.in_waiting:
                line = self.conn.readline().decode('utf-8').rstrip()
                status = []
                angles = line.split(", ")
                status = [angles[i].split(':')[1] for i in range(len(angles))]
                self.status.append(status)
            time.sleep(0.005)
        print("[ArduinoBridge] Done status thread")

def test_thread(bridge, thread_event):
    while not thread_event.is_set():
        msg = bridge.get_msg()
        if not msg == None:
            print("current angle is : %s"%msg[0])
        time.sleep(0.1)

if __name__ == "__main__":
    ## 아두이노 연결 class 초기화
    bridge = ArduinoBridge(PORT="/dev/cu.usbserial-130", BUADRATE=9600)
    
    ## 아두이노와 연결 시도 및 연결상태 확인
    is_conn = bridge.connection()
    if is_conn:
        ## 0.01초마다 가장 아래 모터를 90도에서 140도 까지 2.5초간 움직이고, 
        # 다시 반대로 움직이며 현재 각도를 읽어오도록 하는 루틴
        angle = 90
        dt = 0.05
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
    else:
        print("[ArduinoBridge] fail to connection, check port or buadrate or cable..")

    
