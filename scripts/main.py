from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QGridLayout, QStyleFactory, QLabel
import sys
import time
from threading import Thread
from joystick import Joystick
from socket_bridge import SocketClientHandler
from arduino_bridge import ArduinoBridge

def main(joy1, joy2, ad, sc):
    global B_value_label, S_value_label
    global E_value_label, G_value_label
    ## 변수 초기화(자료형은 int)
    B_value = int(joy1.vertical)
    S_value = int(joy1.horizon)
    E_value = int(joy2.vertical)
    G_value = int(joy2.horizon)

    while True:
        ## joystick 으로 부터 받은 값을 arduino로 전달(기존 값과 다를 경우에만)
        ## 각 변수의 값은 ()_value : joystick으로 받은 값을 저장하며, 자료형은 int로 한다. joystick값과 비교한다.
        if not B_value == int(joy1.vertical):
            B_value = int(joy1.vertical)
            ad.send_msg("B: %s"%B_value)
        elif not S_value == int(joy1.horizon):
            S_value = int(joy1.horizon)
            ad.send_msg("S: %s"%S_value)
        elif not E_value == int(joy2.vertical):
            E_value = int(joy2.vertical)
            ad.send_msg("E: %s"%E_value)
        elif not G_value == int(joy2.horizon):
            G_value = int(joy2.horizon)
            ad.send_msg("G: %s"%G_value)

        ## Arduino로 부터 받은 값을 socket server로 보내기
        ## 제어 주기가 맞지 않아 arduino로 부터 값을 받지 못할 경우 기존에 업데이트한 값을 그대로 사용한다.
        temp = ad.get_msg()
        if not temp == None:
            status = temp
            status_msg = '{"B": %s'%status[0]
            status_msg += ', "S": %s'%status[1]
            status_msg += ', "E": %s'%status[2]
            status_msg += ', "G": %s}'%status[3]
            sc.send_msg(status_msg)
        time.sleep(0.03)


def update_label1(direction, value):
    global B_value_label, S_value_label
    if direction in ["Up" ,"Down"]:
        B_value_label.setText(str(value))
    if direction in ["Left", "Right"]:
        S_value_label.setText(str(value))

def update_label2(direction, value):
    global E_value_label, G_value_label
    if direction in ["Up" ,"Down"]:
        E_value_label.setText(str(value))
    if direction in ["Left", "Right"]:
        G_value_label.setText(str(value))

if __name__ == '__main__':
    # UI 활성화
    app = QApplication([])  ## PyQt5 인스턴스 생성
    app.setStyle(QStyleFactory.create("Cleanlooks"))  ## 애플리케이션의 스타일 설정, cleanlook 스타일 생성
    mw = QMainWindow()  ## 메뉴바, 상태바 등을 생성
    mw.setWindowTitle('Joystick example')  ## 메인 윈도우의 제목을 설정

    cw = QWidget()  ## 다른 위젯을 포함가능한 컨테이너 역할
    ml = QGridLayout()  ## 그리드 레이아웃 설정, 위젯을 격자 형태로 정렬하는데 사용
    cw.setLayout(ml)  ## cw 위젯에 ml 그리드 레이아웃을 설정, cw안에 추가된 위젯들은 ml 그리아 형식에 따라 배치
    mw.setCentralWidget(cw)  ## mw 메인 윈도우의 중앙 위젯을 cw로 설정

    ## 2개의 조이스틱 생성 각각 로봇 플랫폼에 달려있는 조이스틱과 동일한 프로세스
    # joystic_ba1 의 경우 세로축은 bottom motor 제어, 가로축은 arm1 motor 제어
    # joystic_a2g 의 경우 세로축은 arm2 motor 제어, 가로축은 gripper motor 제어
    joystick_ba1 = Joystick(
        DEFAULT_HORIZON=110, DEFAULT_VERTICAL=100,
        MAX_HORIZON=120, MAX_VERTICAL=125,
        MIN_HORIZON=80, MIN_VERTICAL=70)
    joystick_a2g = Joystick(
        DEFAULT_HORIZON=0, DEFAULT_VERTICAL=90,
        MAX_HORIZON=60, MAX_VERTICAL=120,
        MIN_HORIZON=0, MIN_VERTICAL=70)
    
    ## 아두이노, socket client instance 생성
    arduino_bridge = ArduinoBridge(PORT="/dev/cu.usbserial-130", 
                                   BUADRATE=9600, 
                                   AUTOSTART=True)
    socket_handler = SocketClientHandler(AUTOSTART=True)

    ## 메인 쓰레드 생성
    bridge_thread = Thread(target=main, args=(joystick_ba1, 
                                                joystick_a2g, 
                                                arduino_bridge, 
                                                socket_handler))
    bridge_thread.daemon = True
    bridge_thread.start()
    
    ## 2개의 생성된 조이스틱을 위젯에 추가
    ml.addWidget(joystick_ba1, 0, 0)
    ml.addWidget(joystick_a2g, 0, 1)

    # 각도를 표시할 레이블 생성 및 추가
    B_label = QLabel("Bottom")
    ml.addWidget(B_label, 1, 0)
    B_value_label = QLabel(str(joystick_ba1.vertical))
    ml.addWidget(B_value_label, 2, 0)

    S_label = QLabel("Shoulder")
    ml.addWidget(S_label, 1, 1)
    S_value_label = QLabel(str(joystick_ba1.horizon))
    ml.addWidget(S_value_label, 2, 1)

    E_label = QLabel("Elbow")
    ml.addWidget(E_label, 1, 2)
    E_value_label = QLabel(str(joystick_a2g.vertical))
    ml.addWidget(E_value_label, 2, 2)

    G_label = QLabel("Gripper")
    ml.addWidget(G_label, 1, 3)
    G_value_label = QLabel(str(joystick_a2g.horizon))
    ml.addWidget(G_value_label, 2, 3)

    ## Joystic의 angleChange 신호가 발생할때마다 
    ## update_label1, 2 함수가 호출되어 레이블 업데이트
    joystick_ba1.angleChange.connect(update_label1)
    joystick_a2g.angleChange.connect(update_label2)

    mw.show()
    sys.exit(app.exec_())
