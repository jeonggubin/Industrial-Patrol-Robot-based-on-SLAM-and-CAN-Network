import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import socket

class Nav2ToUdpMapper(Node):
    def __init__(self):
        super().__init__('nav2_to_udp_mapper')
        
        # 1. ROS 2 구독 설정
        self.subscription = self.create_subscription(
            Twist,
            '/cmd_vel_nav',
            self.listener_callback,
            10)

        # 2. 로봇 물리 파라미터 및 제어 상수 설정
        self.WHEEL_TREAD = 0.15    # 바퀴 사이 거리 (m) [수정 가능]
        self.MAX_VEL_MS = 0.278   # 최대 속도 (1km/h ≈ 0.278m/s)
        self.MAX_ROBOT_VAL = 500  # 로봇 제어 최대값
        
        # 3. UDP 설정
        self.UDP_IP = "127.0.0.1" # STM32 또는 수신부 IP 주소로 수정하세요
        self.UDP_PORT = 10000
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.get_logger().info(f'UDP Mapping Node Started: Target {self.UDP_IP}:{self.UDP_PORT}')

    def listener_callback(self, msg):
        v = msg.linear.x
        w = msg.angular.z

        # 4. 차동 구동(Differential Drive) 역기구학 계산
        # 좌/우 바퀴의 물리적 속도(m/s) 계산
        v_left = v - (w * self.WHEEL_TREAD / 2.0)
        v_right = v + (w * self.WHEEL_TREAD / 2.0)

        # 5. m/s 단위를 0 ~ 500 범위로 매핑
        # (계산 속도 / 최대 속도) * 500
        val_left = int((v_left / self.MAX_VEL_MS) * self.MAX_ROBOT_VAL) * 5
        val_right = int((v_right / self.MAX_VEL_MS) * self.MAX_ROBOT_VAL) * 5


        if val_left > 300: val_left = 500
        elif val_left > 100: val_left = 300
        elif val_left < -300: val_left = -500
        elif val_left < -100: val_left = -300

        if val_right > 300: val_right = 500
        elif val_right > 100: val_right = 300
        elif val_right < -300: val_right = -500
        elif val_right < -100: val_right = -300

        # if val_left > 400: val_left = 500
        # elif val_left > 300: val_left = 400
        # elif val_left > 200: val_left = 300
        # elif val_left > 100: val_left = 200
        # elif val_left > 0: val_left = 100
        # elif val_left > -100: val_left = -100
        # elif val_left > -200: val_left = -200
        # elif val_left > -300: val_left = -300
        # elif val_left > -400: val_left = -400
        # elif val_left > -500: val_left = -500

        # if val_right > 400: val_right = 500
        # elif val_right > 300: val_right = 400
        # elif val_right > 200: val_right = 300
        # elif val_right > 100: val_right = 200
        # elif val_right > 0: val_right = 100
        # elif val_right > -100: val_right = -100
        # elif val_right > -200: val_right = -200
        # elif val_right > -300: val_right = -300
        # elif val_right > -400: val_right = -400
        # elif val_right > -500: val_right = -500

        # # 6. 값 제한 (클리핑: -500 ~ 500)
        # val_left = max(min(val_left, 500), -500)
        # val_right = max(min(val_right, 500), -500)

        # 7. 음수 처리 및 16진수 문자열 변환 (2바이트, 4자리)
        # 음수의 경우 2의 보수 방식으로 처리하기 위해 0xFFFF와 비트 연산
        hex_left = format(val_left & 0xFFFF, '04X')
        hex_right = format(val_right & 0xFFFF, '04X')

        # 예시 형식: 01F401F4 (왼쪽 4자리 + 오른쪽 4자리)
        udp_msg = hex_right + hex_left
        
        # 8. UDP 전송
        try:
            self.sock.sendto(udp_msg.encode(), (self.UDP_IP, self.UDP_PORT))
            self.get_logger().info(f'V:{v:.2f} W:{w:.2f} | L:{val_left} R:{val_right} | UDP:{udp_msg}')
        except Exception as e:
            self.get_logger().error(f'UDP Send Error: {e}')

def main(args=None):
    rclpy.init(args=args)
    node = Nav2ToUdpMapper()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
