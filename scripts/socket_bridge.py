import time
import socket
import traceback
import signal
from threading import Thread, Event
from collections import deque

class SocketClientHandler():
    def __init__(self, HOST="127.0.0.1", PORT=8080, AUTOSTART=False):
        self.host = HOST
        self.port = PORT
        self.is_connected = False

        self.current_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.recv_queue = deque(maxlen=10)
        self.shutdown_event = Event()
        if AUTOSTART:
            self.request_connection()


    def request_connection(self):
        while not self.shutdown_event.is_set():
            try:
                self.current_client.connect((self.host, self.port))
                recv_thread = Thread(target=self._recv_thread)
                recv_thread.daemon = True
                recv_thread.start()
                self.is_connected = True
                break
            except Exception:
                print("[SocketClientHandler] failed to connect to server, %s"%traceback.format_exc())
                time.sleep(1)
        return True

    def __del__(self):
        self.request_shutdown_thread()
        self.current_client.close()
        self.is_connected = False
        print("[SocketClientHandler] successfully delete client instance")

    def request_shutdown_thread(self):
        try:
            self.shutdown_event.set()
        except Exception:
            print("[SocketClientHandler] failed to shutdown thread")
    
    def send_msg(self, data):
        data += "|"
        print("send : %s"%data)
        self.current_client.send(data.encode('utf-8'))

    def get_msg(self):
        if not len(self.recv_queue) == 0:
            data = self.recv_queue.pop()
            print("get : %s"%data)
            return data
        return None

    def _recv_thread(self):
        while not self.shutdown_event.is_set():
            try:
                packet = self.current_client.recv(1024).decode('utf-8')
            except socket.timeout:
                continue
            while True:
                success = False
                try:
                    temp = packet.find("|")
                    success = True
                except Exception:
                    pass
                finally:
                    if success:
                        self.recv_queue.append(packet[:temp])
                        print(packet[:temp])


if __name__ == "__main__":
    _host = "127.0.0.1"
    _port = 8080
    _cls = SocketClientHandler(HOST=_host, PORT=_port)
    conn = _cls.request_connection()
    while True:
        time.sleep(1)
        _cls.send_msg("B: 90")
        time.sleep(1)
        _cls.send_msg("B: 120")
        if not _cls.is_connected:
            break

    time.sleep(4)
    del _cls