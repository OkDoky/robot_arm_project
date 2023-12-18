from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QGridLayout, QStyleFactory, QLabel
import sys
import time
from threading import Thread
from joystick import Joystick
from socket_bridge import SocketClientHandler
from arduino_bridge import ArduinoBridge

def main(joy1, joy2, ad, sc):
    B_value = int(joy1.vertical)
    A1_value = int(joy1.horizon)
    A2_value = int(joy2.vertical)
    G_value = int(joy2.horizon)

    while True:
        ## joystick 으로 부터 받은 값을 arduino로 전달
        if not B_value == int(joy1.vertical):
            B_value = int(joy1.vertical)
            ad.send_msg("B: %s"%B_value)
        elif not A1_value == int(joy1.horizon):
            A1_value = int(joy1.horizon)
            ad.send_msg("S: %s"%A1_value)
        elif not A2_value == int(joy2.vertical):
            A2_value = int(joy2.vertical)
            ad.send_msg("A: %s"%A2_value)
        elif not G_value == int(joy2.horizon):
            G_value = int(joy2.horizon)
            ad.send_msg("G: %s"%G_value)

        ## Arduino로 부터 받은 값을 socket server로 보내기
        temp = ad.get_msg()
        if not temp == None:
            status = temp
            status_msg = '{"B": %s'%status[0]
            status_msg += ', "S": %s'%status[1]
            status_msg += ', "A": %s'%status[2]
            status_msg += ', "G": %s}'%status[3]
            sc.send_msg(status_msg)
        time.sleep(0.01)


def update_label1(direction, value):
    global B_value_label, A1_value_label
    if direction == "Up" or direction == "Down":
        B_value_label.setText(str(value))
    if direction == "Left" or direction == "Right":
        A1_value_label.setText(str(value))

def update_label2(direction, value):
    global A2_value_label, G_value_label
    if direction == "Up" or direction == "Down":
        A2_value_label.setText(str(value))
    if direction == "Left" or direction == "Right":
        G_value_label.setText(str(value))

if __name__ == '__main__':
    # UI 활성화
    app = QApplication([])
    app.setStyle(QStyleFactory.create("Cleanlooks"))
    mw = QMainWindow()
    mw.setWindowTitle('Joystick example')

    cw = QWidget()
    ml = QGridLayout()
    cw.setLayout(ml)
    mw.setCentralWidget(cw)

    ## 2개의 조이스틱 생성 각각 로봇 플랫폼에 달려있는 조이스틱과 동일한 프로세스
    # joystic_ba1 의 경우 세로축은 bottom motor 제어, 가로축은 arm1 motor 제어
    # joystic_a2g 의 경우 세로축은 arm2 motor 제어, 가로축은 gripper motor 제어
    joystick_ba1 = Joystick(
        DEFAULT_HORIZON=110, DEFAULT_VERTICAL=100,
        MAX_HORIZON=140, MAX_VERTICAL=130,
        MIN_HORIZON=80, MIN_VERTICAL=70)
    joystick_a2g = Joystick(
        DEFAULT_HORIZON=0, DEFAULT_VERTICAL=90,
        MAX_HORIZON=60, MAX_VERTICAL=120,
        MIN_HORIZON=0, MIN_VERTICAL=60)
    
    arduino_bridge = ArduinoBridge(PORT="/dev/cu.usbserial-1130", 
                                   BUADRATE=9600, 
                                   AUTOSTART=True)
    socket_handler = SocketClientHandler(AUTOSTART=True)

    bridge_thread = Thread(target=main, args=(joystick_ba1, 
                                                      joystick_a2g, 
                                                      arduino_bridge, 
                                                      socket_handler))
    bridge_thread.daemon = True
    bridge_thread.start()
    
    ml.addWidget(joystick_ba1, 0, 0)
    ml.addWidget(joystick_a2g, 0, 1)

    # 각도를 표시할 레이블 생성 및 추가
    B_label = QLabel("Bottom")
    ml.addWidget(B_label, 1, 0)
    B_value_label = QLabel(str(joystick_ba1.vertical))
    ml.addWidget(B_value_label, 2, 0)

    A1_label = QLabel("Arm1")
    ml.addWidget(A1_label, 1, 1)
    A1_value_label = QLabel(str(joystick_ba1.horizon))
    ml.addWidget(A1_value_label, 2, 1)

    A2_label = QLabel("Arm2")
    ml.addWidget(A2_label, 1, 2)
    A2_value_label = QLabel(str(joystick_a2g.vertical))
    ml.addWidget(A2_value_label, 2, 2)

    G_label = QLabel("Gripper")
    ml.addWidget(G_label, 1, 3)
    G_value_label = QLabel(str(joystick_a2g.horizon))
    ml.addWidget(G_value_label, 2, 3)

    joystick_ba1.angleChange.connect(update_label1)
    joystick_a2g.angleChange.connect(update_label2)

    mw.show()
    sys.exit(app.exec_())
