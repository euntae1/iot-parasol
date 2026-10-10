# ☂️ Smart IoT Parasol System (지능형 IoT 스마트 파라솔)

> **건국대학교 전기전자공학부 지능형IoT설계 최종 프로젝트**  
> 라즈베리파이, ESP32, 플러터(Flutter) 앱, 그리고 컴퓨터 비전(Optical Flow)을 연동하여 태양의 각도와 강우 방향에 따라 최적의 그늘을 자동으로 유지하는 지능형 보호 장치입니다[cite: 179, 181].

---

## 👥 팀원 정보 및 역할 분담 (Role & Contributions)

| 이름 | 주요 담당 업무 |
| :--- | :--- |
| **박용균** | • GPS 및 `pvlib` 기반 태양 위치(방위각, 고도각) 자동 제어 로직 구현<br>• Flutter 기반 모바일 애플리케이션 개발<br>• Flask 서버 통합 및 통신 구조 설계[cite: 224] |
| **장은태 (본인)** | • **라즈베리파이 카메라 및 ESP32 카메라 직교(Orthogonal) 환경 구축**[cite: 184, 224]<br>• **OpenCV `Farneback Optical Flow` 및 Sobel 필터 기반 빗물 탐지 및 방향 각도 계산 알고리즘 설계**[cite: 193, 224]<br>• **영상 기반 모터 각도 변환 및 빗물 유입 방향 연동 제어 구현**[cite: 195, 224] |
| **한지혜** | • 구동부 요구 토크 산정 및 서보 모터 선정[cite: 187, 224]<br>• 18650 배터리 전원 시스템 설계 및 안정성 확보[cite: 189, 224]<br>• Autodesk Inventor 기반 하단부 하우징 설계 및 시스템 조립[cite: 190, 224] |

---

## 📖 1. 프로젝트 개요 (Overview)
- **개발 배경:** 기존의 단순 자동 개폐 우산/파라솔은 사선으로 내리는 비나 시간대별 태양 고도 변화에 대응하지 못하는 한계가 존재합니다[cite: 181]. 본 프로젝트는 **환경 변화 인지 ➔ 방향 계산 ➔ 모터 자동 조정**의 전 과정이 실시간으로 이루어지는 지능형 스마트 파라솔을 구현하였습니다[cite: 182, 183].
- **주요 특징:**
  - **3차원 비 방향 인식:** 2대 카메라의 직교 배치와 Optical Flow를 통해 비가 유입되는 입체적 방향 산출[cite: 184, 193]
  - **실시간 태양 추적:** GPS와 `pvlib` 라이브러리를 결합하여 설치 위치 변경에도 대응하는 태양 위치 추적[cite: 196, 197]
  - **모바일 원격 제어:** Flutter 앱을 통한 태양 자동제어, 비 자동제어, 수동 제어 모드 및 안전 초기화 기능[cite: 205, 211, 213]
  - **모터 제어 안정화:** `pigpio` PWM 제어 및 부드러운 보간 이동(Smooth Move) 알고리즘 적용[cite: 208]

---

## 🛠️ 2. 사용 기술 스택 (Tech Stack)

- **Hardware:** Raspberry Pi, ESP32-CAM, L80-M39 GPS 모듈, 20KG/25KG 디지털 서보모터, 18650 배터리 (2S)[cite: 1, 186, 189]
- **Backend / Server:** Python, Flask, `pigpio`, `pvlib`, `pynmea2`, `pyserial`[cite: 14, 196, 206]
- **Frontend (App):** Flutter (Dart)[cite: 205]
- **Computer Vision:** OpenCV (`Farneback Optical Flow`, Sobel Filter, HSV Color Space)[cite: 193]
- **Mechanics / Tools:** Autodesk Inventor (하우징 설계)[cite: 190]

---

## ⚙️ 3. 핵심 기능 및 본인 담당 업무 상세 (Key Contributions)

### 🔹 [장은태 담당] OpenCV 기반 빗물 방향 감지 및 각도 계산 알고리즘
1. **듀얼 카메라 직교(Orthogonal) 배치:**
   - 단일 카메라의 2차원 한계를 극복하기 위해 $\varphi=0^\circ$(x축) 방향에 ESP32 카메라, $\varphi=90^\circ$(y축) 방향에 라즈베리파이 카메라를 직교 배치하여 빗물의 3차원 유입 성분을 독립적으로 관측[cite: 184].
2. **Optical Flow & Sobel 필터 결합:**
   - OpenCV의 `calcOpticalFlowFarneback`을 이용해 프레임간 픽셀 이동 벡터를 추출하고, `Sobel 필터`를 함께 적용하여 노이즈 및 배경 움직임을 필터링[cite: 193].
   - HSV 색공간 변환($S < 90, V > 120$)을 통해 반사광 및 조명 변화로 인한 오검출을 최소화[cite: 193].
3. **히스토그램 양자화 및 스무딩:**
   - 검출된 빗물 각도를 1도 단위 히스토그램 가중 평균으로 산출한 뒤, 모터의 과도한 진동과 잦은 회전을 방지하기 위해 각도 변화 폭을 제한하는 시간적 스무딩(Smoothing) 기법 적용[cite: 195].

---

## 📂 4. 프로젝트 디렉토리 구조 (Directory Structure)

```text
smart-parasol-system/
├── Backend_RaspberryPi/     # 라즈베리파이 서버 및 모터 제어 부
│   ├── test_server.py       # Flask 통합 서버 및 상태 공유 매니저
│   ├── test_servo_controller.py # pigpio 기반 서보모터 및 스무스 무브 제어
│   └── test_sun_position.py # pvlib 기반 태양 고도/방위각 연산
│
├── Frontend_FlutterApp/     # Flutter 모바일 앱 소스 코드
│   ├── lib/
│   │   ├── main.dart        # 앱 진입점
│   │   ├── screens/         # 홈, 자동제어, 수동제어 화면 UI
│   │   ├── services/        # REST API 서버 통신 연동 (api.dart)
│   │   ├── widgets/         # 나침반, 파라솔 뷰, 날씨 배경 컴포넌트
│   │   └── utils/           # 시간 유틸 함수
│   └── pubspec.yaml
│
└── ComputerVision/          # 영상 처리 및 비전 시스템 부
    ├── rain_detector.py     # 라즈베리파이 카메라 스트리밍
    └── real.py              # 노트북 비전 통합 처리 및 빗물 각도 계산


[Flutter Mobile App] --(HTTP POST/GET REST API)--> [Raspberry Pi (Flask Server)] 
                                                          │
          ┌───────────────────────────────────────────────┴───────────────────────────────────────────────┐
          ▼                                               ▼                                               ▼
[Sun Tracking (GPS + pvlib)]                [Rain Detection (Laptop + ESP32)]               [Servo Motor Control (pigpio)]
- 위도/경도 기반 태양 고도·방위각 산출       - Optical Flow 기반 비 방향 및 각도 연산        - 2축(회전/기울기) 부드러운 보간 제어



📱 6. 주요 시연 결과 (Demonstration)
태양 자동제어 모드비 자동제어 모드수동 제어 모드GPS 및 pvlib를 통해 실시간 태양 방위각을 계산하여 파라솔이 태양 방향을 추적[cite: 197, 216]
카메라 영상 분석을 통해 비가 유입되는 방향(예: 135°)을 실시간 인지하고 각도 조절[cite: 219]
사용자가 앱에서 슬라이더 및 직접 입력을 통해 원하는 각도로 정밀 제어[cite: 223]
