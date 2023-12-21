import time
import socket
import traceback
from threading import Thread, Event
from collections import deque

class SocketClientHandler():
    def __init__(self, HOST="127.0.0.1", PORT=8080, AUTOSTART=False):
        self.host = HOST
        self.port = PORT
        self.is_connected = False

        self.current_client = None
        self.recv_queue = deque(maxlen=10)
        self.shutdown_event = Event()
        if AUTOSTART:
            self.request_connection()


    def request_connection(self):
        ## 소켓 서버에 연결 요청, 연결시까지 지속적으로 1초마다 연결시도를 하게되며, 
        ## 연결되면 recv thread를 열어 서버로부터 데이터를 받을 수 있도록 준비한다.
        print("%s"%self.current_client)
        if not self.current_client == None:
            self.disconnection()
        self.shutdown_event.clear()
        while not self.shutdown_event.is_set():
            try:
                self.current_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
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
        self._request_shutdown_thread()
        self.current_client.close()
        self.is_connected = False
        print("[SocketClientHandler] successfully delete client instance")

    def disconnection(self):
        self.current_client.close()
        self._request_shutdown_thread()
        self.is_connected = False
        self.current_client = None

    def _request_shutdown_thread(self):
        # thread event를 활성화하는 함수
        self.shutdown_event.set()
    
    def send_msg(self, data):
        # 데이터 포멧 변경 및 전송
        data += "|"
        print("send : %s"%data)
        self.current_client.send(data.encode('utf-8'))

    def get_msg(self):
        # 외부에서 호출하게 되며, 받은 데이터가 있을 경우 데이터를 반환, 
        # 없을 경우 None 반환
        if not len(self.recv_queue) == 0:
            data = self.recv_queue.pop()
            # print("get : %s"%data)
            return data
        return None

    def _recv_thread(self):
        print("[SocketClientHandler] recv thread Start")
        while not self.shutdown_event.is_set():
            try:
                packet = self.current_client.recv(1024).decode('utf-8')
                success = False
                temp = packet.find("|")
                if temp != -1:
                    # '|' 문자가 있으면 해당 위치까지 문자열을 추출
                    print("recv data : %s"%packet[:temp])
                    self.recv_queue.append(packet[:temp])
                    success = True
            except socket.timeout:
                continue
            except Exception:
                pass
        print("[SocketClientHandler] recv thread Done")


if __name__ == "__main__":
    _host = "127.0.0.1"
    _port = 8080
    _cls = SocketClientHandler(HOST=_host, PORT=_port)
    conn = _cls.request_connection()
    while True:
        time.sleep(1)
        _cls.send_msg('{"B": 90, "S": 90, "E": 90, "G": 0}')
        time.sleep(1)
        _cls.send_msg('{"B": 120, "S": 90, "E": 90, "G": 0}')
        if not _cls.is_connected:
            break

    time.sleep(4)
    del _cls