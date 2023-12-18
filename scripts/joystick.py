from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QGridLayout, QStyleFactory, QLabel
from PyQt5.QtGui import QPainter
from PyQt5.QtCore import QRectF, QPointF, QLineF, Qt, pyqtSignal

import sys
from enum import Enum


class Direction(Enum):
    Left = 0
    Right = 1
    Up = 2
    Down = 3

class Joystick(QWidget):
    angleChange = pyqtSignal(str, float)
    def __init__(self, DEFAULT_VERTICAL=0, DEFAULT_HORIZON=0, 
                 MAX_VERTICAL = 10, MAX_HORIZON=10, 
                 MIN_VERTICAL = -10, MIN_HORIZON = -10, parent=None):
        super(Joystick, self).__init__(parent)
        self.vertical = DEFAULT_VERTICAL
        self.horizon = DEFAULT_HORIZON
        
        self.max_vertical = MAX_VERTICAL
        self.max_horizon = MAX_HORIZON
        self.min_vertical = MIN_VERTICAL
        self.min_horizon = MIN_HORIZON

        if self.vertical < MIN_VERTICAL:
            self.vertical = MIN_VERTICAL
        elif self.vertical > MAX_VERTICAL:
            self.vertical = MAX_VERTICAL
        if self.horizon < MIN_HORIZON:
            self.horizon = MIN_HORIZON
        elif self.horizon > MAX_HORIZON:
            self.horizon = MAX_HORIZON

        self.setMinimumSize(100, 100) # 조이스틱 위젯의 최소 크기 설정
        self.movingOffset = QPointF(0, 0)  # 조이스틱의 현재 위치
        self.grabCenter = False  # 조이스틱이 잡혔는지 여부
        self.__maxDistance = 50 # 조이스틱이 이동할 수 있는 최대 거리

    def paintEvent(self, event):
        painter = QPainter(self)
        # 조이스틱의 경계를 그리는 코드
        bounds = QRectF(-self.__maxDistance, -self.__maxDistance, 
                        self.__maxDistance * 2, self.__maxDistance * 2).translated(self._center())
        painter.drawEllipse(bounds)
        painter.setBrush(Qt.black)
        # 조이스틱의 중심을 그리는 코드
        painter.drawEllipse(self._centerEllipse())

    def _centerEllipse(self):
        # 조이스틱 중심의 위치를 반환하는 함수
        if self.grabCenter:
            return QRectF(-20, -20, 40, 40).translated(self.movingOffset)
        return QRectF(-20, -20, 40, 40).translated(self._center())

    def _center(self):
        # 위젯의 중심점을 반환하는 함수
        return QPointF(self.width()/2, self.height()/2)

    def _boundJoystick(self, point):
        # 조이스틱이 이동할 수 있는 경계 내에서 위치를 조정하는 함수
        limitLine = QLineF(self._center(), point)
        if (limitLine.length() > self.__maxDistance):
            limitLine.setLength(self.__maxDistance)
        return limitLine.p2()

    def joystickDirection(self):
        # 조이스틱의 방향과 거리를 계산하는 함수
        if not self.grabCenter:
            return (False, 0,0)
        normVector = QLineF(self._center(), self.movingOffset)
        currentDistance = normVector.length()
        angle = normVector.angle()

        distance = min(currentDistance / self.__maxDistance, 1.0)
        ## 아직 조이스틱을 조금밖에 움직이지 않았을 경우(노이즈 제거를 위한 부분)
        if distance < 0.3:
            return (False, 0,0)
        
        # 각 파트를 움직여 실시간 변수 조정
        if 45 <= angle < 135: # up
            self.vertical += distance
            self.vertical = min(self.max_vertical, self.vertical)
            return (True, Direction.Up, int(self.vertical))
        elif 135 <= angle < 225: # left
            self.horizon -= distance
            self.horizon = max(self.min_horizon, self.horizon)
            return (True, Direction.Left, int(self.horizon))
        elif 225 <= angle < 315: # down
            self.vertical -= distance
            self.vertical = max(self.min_vertical, self.vertical)
            return (True, Direction.Down, int(self.vertical))
        else: # right
            self.horizon += distance
            self.horizon = min(self.max_horizon, self.horizon)
            return (True, Direction.Right, int(self.horizon))

    def mousePressEvent(self, event):
        # 마우스 버튼이 눌릴 때 이벤트 처리
        self.grabCenter = self._centerEllipse().contains(event.pos())
        return super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        # 마우스 버튼이 떼어질 때 이벤트 처리
        self.grabCenter = False
        self.movingOffset = QPointF(0, 0)
        self.update()

    def mouseMoveEvent(self, event):
        # 마우스가 움직일 때 이벤트 처리
        if self.grabCenter: # 조이스틱이 잡힌경우
            self.movingOffset = self._boundJoystick(event.pos()) # 조이스틱 위치 업데이트
            self.update()  # Gui 화면 업데이트
            success, direction, distance = self.joystickDirection()
            if success:
                self.angleChange.emit(direction.name, distance) # signal 신호 업데이트

def update_label(direction, value):
    global V_value_label, H_value_label
    if direction in ["Up" ,"Down"]:
        V_value_label.setText(str(value))
    if direction in ["Left", "Right"]:
        H_value_label.setText(str(value))

if __name__ == "__main__":
    # UI 활성화
    app = QApplication([])  ## PyQt5 인스턴스 생성
    app.setStyle(QStyleFactory.create("Cleanlooks"))  ## 애플리케이션의 스타일 설정, cleanlook 스타일 생성
    mw = QMainWindow()  ## 메뉴바, 상태바 등을 생성
    mw.setWindowTitle('Joystick example')  ## 메인 윈도우의 제목을 설정

    cw = QWidget()  ## 다른 위젯을 포함가능한 컨테이너 역할
    ml = QGridLayout()  ## 그리드 레이아웃 설정, 위젯을 격자 형태로 정렬하는데 사용
    cw.setLayout(ml)  ## cw 위젯에 ml 그리드 레이아웃을 설정, cw안에 추가된 위젯들은 ml 그리아 형식에 따라 배치
    mw.setCentralWidget(cw)  ## mw 메인 윈도우의 중앙 위젯을 cw로 설정

    ## joy stick 인스턴스 생성
    joy = Joystick(
        MAX_VERTICAL = 100, MAX_HORIZON=100, 
        MIN_VERTICAL = -100, MIN_HORIZON = -100)
    
    ## 생성된 조이스틱을 위젯에 추가
    ml.addWidget(joy, 0, 0)

    # 각도를 표시할 레이블 생성 및 추가
    global V_value, H_value
    V_label = QLabel("Vertical")
    ml.addWidget(V_label, 1, 0)
    V_value_label = QLabel(str(joy.vertical))
    ml.addWidget(V_value_label, 2, 0)

    H_label = QLabel("Horizon")
    ml.addWidget(H_label, 1, 1)
    H_value_label = QLabel(str(joy.horizon))
    ml.addWidget(H_value_label, 2, 1)

    ## Joystic의 angleChange 신호가 발생할때마다 
    ## update_label 함수가 호출되어 레이블 업데이트
    joy.angleChange.connect(update_label)

    mw.show()
    sys.exit(app.exec_())