# Track A Report
## 시스템/웹 데모/오케스트레이션 — Core와 혼합 금지

TrackA는 운영 UX·오케스트레이션·모니터링을 제공한다. 검증 결론은 TrackB Core만 사용한다.

---

## TrackA 기능

- 오케스트레이션: 단계별 실행·스케줄링
- UX: 의사결정 카드, 모니터링 대시보드
- 감사 로그: 결정 추적

---

## TrackB와의 연결

- Validated Core 결과(recall, cost, primary CI)를 운영 UI에서 소비.
- Core 수치만 대시보드에 표시; Proxy는 별도 표시 또는 제외.

---

## 확장성

- 실제 fab 의사결정 시스템에 붙일 때: Core 지표로 게이팅 정책 결정, Proxy는 참고만.

---

## 스크린샷/데모 근거

스크린샷 없음. streamlit_app/, docs/, figures/ 에 PNG/JPG 추가 시 위 테이블에 반영됨.
