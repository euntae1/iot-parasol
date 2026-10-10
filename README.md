# Smart IoT Parasol System (스마트 파라솔 시스템)

> 라즈베리파이와 플러터(Flutter) 앱, 비전 알고리즘을 연동하여 태양의 각도와 날씨(비) 변화에 따라 자동으로 최적의 위치를 조절하는 스마트 IoT 파라솔 시스템입니다.

---

## 📖프로젝트 소개 (Overview)
- **개발 기간:** 2025년 8월 ~ 2025년 12월 (3인 프로젝트)
- **개발 목적:** 야외 환경에서 태양광의 위치와 빗물 방향을 실시간으로 추적하여 사용자에게 최적의 그늘과 편의를 제공하는 자동 제어 파라솔 구현
- **주요 특징:** 
  - `pvlib`을 활용한 실시간 태양 고도/방위각 계산 및 추적[cite: 17, 18, 41]
  - OpenCV Optical Flow 기반 비 방향 감지 및 모터 연동[cite: 170]
  - Flutter 모바일 앱을 통한 실시간 모니터링 및 수동/자동 제어[cite: 143, 151, 154]
  - `pigpio` 라이브러리를 이용한 서보모터 떨림 방지 및 부드러운 스무스 무브(Smooth Move) 구현[cite: 14, 138]

---

## 🛠️ 기술 스택 (Tech Stack)

- **Hardware:** Raspberry Pi, ESP32, Servo Motor (20KG/25KG 디지털 서보)[cite: 1, 119]
- **Backend / Server:** Python, Flask, `pigpio`, `pvlib`[cite: 14, 18, 78]
- **Frontend (App):** Flutter (Dart)[cite: 43]
- **Computer Vision:** OpenCV (Optical Flow Farneback)[cite: 170]

---

## ✨ 주요 기능 (Key Features)

1. **태양 자동 추적 모드 (Sun Tracking Mode)**
   - 지정된 GPS 좌표(위도/경도)와 실시간 시각을 바탕으로 `pvlib`이 태양의 고도와 방위각을 연산[cite: 17, 18, 41]
   - 계산된 각도에 맞춰 수평/수직 서보모어가 자동으로 회전하여 태양 방향 추적
2. **비 모드 및 날씨 연동 (Rain Mode & Weather Adaptive)**
   - 카메라 영상 처리(Optical Flow)를 통해 빗물의 방향과 강도를 분석하여 파라솔 각도 조절[cite: 170, 175]
   - 야간 또는 우천 시 상황에 맞는 안전/대피 모드 수행[cite: 42]
3. **Flutter 모바일 앱 원격 제어**
   - 태양 자동 제어, 비 자동 제어, 수동 제어(슬라이더 및 직접 입력) 모드 지원[cite: 143, 151, 154]
   - 현재 파라솔의 회전각과 기울기 실시간 모니터링 및 나침반 UI 연동[cite: 148, 164]
   - 앱 종료 시 파라솔 초기화(Safe Reset) 기능 팝업 구현[cite: 42, 144]
4. **모터 제어 최적화 (`pigpio` & Smooth Move)**
   - 일반 PWM 제어 시 발생하는 모터 떨림(Jitter) 현상을 해결하기 위해 `pigpio` 데몬 활용[cite: 14]
   - 목표 각도까지 단계별로 잘게 쪼개어 부드럽게 이동하는 `_smooth_move_to_angles` 알고리즘 적용[cite: 138]

---

## 📂 프로젝트 구조 (Directory Structure)

```text
iot-parasol/
├── Backend_RaspberryPi/     # 라즈베리파이 서버 및 모터 제어 부
│   ├── main.py              # Flask 통합 서버 및 모드 관리
│   ├── servo_controller.py  # pigpio 기반 서보모터 제어 및 부드러운 이동
│   └── sun_position.py      # pvlib 기반 태양 위치 계산 유틸리티
│
├── Frontend_FlutterApp/     # Flutter 모바일 앱 소스 코드
│   ├── lib/
│   │   ├── main.py          # 앱 진입점
│   │   ├── screens/         # 화면별 UI (home, auto_mode, manual_mode)
│   │   ├── services/        # Flask 서버 통신 API 연동
│   │   ├── widgets/         # 나침반, 파라솔 뷰, 날씨 배경 등 컴포넌트
│   │   └── utils/           # 시간 및 유틸 함수
│   └── pubspec.yaml
│
└── ComputerVision/          # 카메라 스트리밍 및 비전 처리 부
    ├── rain_detector.py     # 라즈베리파이 카메라 스트리밍
    └── real.py              # 노트북/PC 비전 통합 처리 및 각도 계산
text```

