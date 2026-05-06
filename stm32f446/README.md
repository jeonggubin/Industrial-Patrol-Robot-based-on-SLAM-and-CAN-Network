# STM32 Rover Control Firmware

STM32 기반 로버 제어 펌웨어입니다.  
CAN 통신으로 상위 제어기에서 **모터 속도**와 **서보 각도**를 수신하고, 초음파 센서를 이용해 후진 중 장애물이 가까워지면 자동으로 정지하는 기능을 포함합니다.

---

## 주요 기능

- CAN 통신 기반 모터 속도 명령 수신
- CAN 통신 기반 서보 각도 명령 수신
- 좌/우 DC 모터 PWM 제어
- 서보 모터 각도 제어
- 초음파 센서 거리 측정
- 후진 중 장애물 감지 시 자동 정지
- CAN을 통한 상태 정보 송신

---

## 시스템 구조

```text
상위 제어기 / Raspberry Pi
        |
        | CAN
        v
+----------------+
|    STM32       |
|                |
|  CAN 수신      |
|  모터 제어     |
|  서보 제어     |
|  초음파 측정   |
|  안전 정지     |
+----------------+
        |
        v
DC Motor / Servo / Ultrasonic Sensor
```

---

## 파일 구성

```text
.
└── APP
    └── ap
        ├── ap.c
        ├── ap.h
        ├── ap_def.h
        ├── motor.c
        ├── motor.h
        ├── ultrasonic.c
        ├── ultrasonic.h
        ├── safe_distance.c
        ├── safe_distance.h
        ├── can_comm.c
        ├── can_comm.h
        ├── servomotor.c
        └── servomotor.h
```

---

## 파일별 역할

| 파일 | 역할 |
|---|---|
| `ap.c` | 전체 제어 흐름 관리 |
| `motor.c/h` | 좌/우 DC 모터 PWM 및 방향 제어 |
| `ultrasonic.c/h` | 초음파 센서 거리 측정 |
| `safe_distance.c/h` | 거리 기반 안전 정지 판단 |
| `can_comm.c/h` | CAN 송수신 처리 |
| `servomotor.c/h` | 서보 모터 각도 제어 |
| `ap.h` | 핀맵 및 주요 함수 선언 |
| `ap_def.h` | 공통 정의용 헤더 |

---

## 사용 하드웨어

| 구분 | 내용 |
|---|---|
| MCU | STM32F4 계열 |
| Motor | DC 모터 2개 |
| Servo | SG90 계열 서보 모터 |
| Sensor | HC-SR04 계열 초음파 센서 |
| Communication | CAN |
| Timer | TIM2, TIM3, TIM4 |

---

## 주요 핀 및 타이머

```c
#define MOTOR_PWM_TIM   (&htim3)
#define MOTOR_L_CH      TIM_CHANNEL_1
#define MOTOR_R_CH      TIM_CHANNEL_2

#define ECHO_TIM        (&htim2)
#define ECHO_CH         TIM_CHANNEL_1

#define TRIG_PORT       TRIG_ultrasonic_GPIO_Port
#define TRIG_PIN        TRIG_ultrasonic_Pin
```

| 타이머 | 용도 |
|---|---|
| TIM2 | 초음파 ECHO Input Capture |
| TIM3 | 좌/우 DC 모터 PWM |
| TIM4 | 서보 모터 PWM |

---

## 전체 동작 흐름

```text
1. CAN으로 모터 속도와 서보 각도 수신
2. 수신한 각도로 서보 모터 제어
3. 수신한 속도로 좌/우 모터 목표 속도 설정
4. 초음파 센서로 거리 측정
5. 후진 중 장애물이 가까우면 안전 정지 판단
6. 안전 정지 상태이면 모터 속도를 0으로 제한
7. 최종 모터 속도를 PWM으로 출력
8. 현재 상태를 CAN으로 송신
```

---

## CAN 메시지 구조

### 모터 명령 수신

| 항목 | 내용 |
|---|---|
| CAN ID | `0x100` |
| 방향 | 상위 제어기 → STM32 |
| 데이터 | 좌/우 모터 속도 |

```text
Data[0] : Left Speed High
Data[1] : Left Speed Low
Data[2] : Right Speed High
Data[3] : Right Speed Low
```

---

### 서보 명령 수신

| 항목 | 내용 |
|---|---|
| CAN ID | `0x300` |
| 방향 | 상위 제어기 → STM32 |
| 데이터 | 서보 각도 |

```text
Data[0] : Servo Angle
```

서보 각도 범위는 `0 ~ 180도`입니다.

---

### 상태 송신

| 항목 | 내용 |
|---|---|
| CAN ID | `0x200` |
| 방향 | STM32 → 상위 제어기 |
| 송신 주기 | 1초 |

```text
Data[0] : AEB Flag
Data[1] : Servo Angle
Data[2] : Distance High
Data[3] : Distance Low
Data[4] : Left Speed High
Data[5] : Left Speed Low
Data[6] : Right Speed High
Data[7] : Right Speed Low
```

---

## 안전 정지 로직

초음파 센서로 측정한 거리를 기준으로 후진 중 장애물이 가까우면 모터 출력을 강제로 0으로 만듭니다.

현재 설정값은 다음과 같습니다.

| 항목 | 값 |
|---|---:|
| 정지 거리 | 15 cm |
| 정지 해제 거리 | 20 cm |
| 정지 조건 | 2회 연속 |
| 해제 조건 | 2회 연속 |
| 센서 타임아웃 | 200 ms |

안전 정지는 현재 **후진 상황에서만 적용**됩니다.

```c
if (l_tgt_raw < 0 && r_tgt_raw < 0) {
  safe_distance_apply_cmd(&sd,
                          l_tgt_raw,
                          r_tgt_raw,
                          now_ms,
                          &l_tgt_safe,
                          &r_tgt_safe);
}
```

안전 정지 상태가 되면 최종 모터 명령은 0으로 제한됩니다.

```c
if (sd->state == SAFE_ESTOP) {
  *left_out = 0;
  *right_out = 0;
}
```

---

## 주요 초기화 코드

`apInit()`에서 전체 모듈을 초기화합니다.

```c
void apInit(void) {
  uint32_t pwm_max = __HAL_TIM_GET_AUTORELOAD(&htim3);

  motor_init(&mL, MOTOR_PWM_TIM, MOTOR_L_CH, MOTOR_DIR_PORT, MOTOR_L_DIR_PIN,
             pwm_max, 0);
  motor_init(&mR, MOTOR_PWM_TIM, MOTOR_R_CH, MOTOR_DIR_PORT, MOTOR_R_DIR_PIN,
             pwm_max, 1);

  motor_start(&mL);
  motor_start(&mR);

  motor_set_ramp_step(&mL, 10);
  motor_set_ramp_step(&mR, 10);

  ultrasonic_init(&us, &htim2, ECHO_CH, TRIG_PORT, TRIG_PIN, 50);

  safe_distance_init(&sd, 15, 20, 2, 2, 200);

  Servo_Init(&myServo, &htim4, TIM_CHANNEL_1);
  Servo_SetAngle(&myServo, target_angle);

  extern CAN_HandleTypeDef hcan1;
  can_comm_init(&hcan1, on_can_motor_cmd, on_can_servo_cmd);
}
```

---

## 주요 제어 주기

| 항목 | 주기 |
|---|---:|
| 메인 제어 루프 | 10 ms |
| 초음파 Trigger | 60 ms |
| CAN 상태 송신 | 1000 ms |
| 초음파 타임아웃 | 50 ms |
| 안전 거리 타임아웃 | 200 ms |

---

## 모듈별 핵심 설명

### Motor

DC 모터는 PWM과 DIR 핀으로 제어합니다.

```text
speed > 0  : 정방향
speed < 0  : 역방향
speed = 0  : 정지
```

Ramp 기능을 사용하여 속도가 급격히 변하지 않도록 합니다.

---

### Ultrasonic

초음파 센서는 TRIG 핀으로 10us 펄스를 출력하고, ECHO 핀은 TIM Input Capture로 측정합니다.

거리 계산은 다음 식을 사용합니다.

```text
distance_cm = echo_us / 58
```

---

### Safe Distance

초음파 측정값을 기반으로 안전 상태를 판단합니다.

```text
RUN      : 정상 주행 가능
ESTOP    : 안전 정지 상태
```

거리 값은 단순히 바로 사용하지 않고, 비정상 값 제거와 필터링을 거친 뒤 안전 판단에 사용합니다.

---

### Servo

서보 모터는 PWM 펄스폭으로 각도를 제어합니다.

```c
#define SERVO_MIN_PULSE 500
#define SERVO_MAX_PULSE 2500
```

각도 범위는 `0 ~ 180도`입니다.

---

## CubeMX 설정 체크리스트

- TIM3 PWM 활성화
  - Channel 1: Left Motor
  - Channel 2: Right Motor
- TIM2 Input Capture 활성화
  - 초음파 ECHO 측정용
  - 1 tick = 1us 권장
- TIM4 PWM 활성화
  - 서보 모터 제어용
  - 50Hz 권장
- CAN1 활성화
  - RX FIFO0 interrupt 사용
- DIR 핀 GPIO Output 설정
- TRIG 핀 GPIO Output 설정

---

## 인터럽트 연결

### 초음파 Input Capture

```c
void HAL_TIM_IC_CaptureCallback(TIM_HandleTypeDef *htim)
{
  apUltrasonic_OnCapture(htim);
}
```

### CAN RX

```c
void HAL_CAN_RxFifo0MsgPendingCallback(CAN_HandleTypeDef *hcan)
{
  can_comm_rx_handler(hcan);
}
```

---

## 주의사항

- 서보 명령 CAN ID는 실제 코드 기준 `0x300`입니다.
- 초음파 거리 계산을 위해 TIM2는 1us 단위로 카운트되도록 설정하는 것이 좋습니다.
- 서보 PWM은 50Hz 기준으로 설정하는 것이 일반적입니다.
- 현재 안전 정지는 후진 명령에서만 적용됩니다.
- 전진 장애물 감지를 추가하려면 안전 정지 적용 조건을 수정해야 합니다.

---

## 프로젝트 요약

이 프로젝트는 STM32를 이용해 로버의 DC 모터, 서보 모터, 초음파 센서, CAN 통신을 통합 제어하는 펌웨어입니다.

상위 제어기에서 CAN으로 주행 명령을 보내면 STM32가 모터와 서보를 제어하고, 후진 중 초음파 센서로 장애물을 감지하면 자동으로 모터 출력을 0으로 제한하여 안전 정지를 수행합니다.
