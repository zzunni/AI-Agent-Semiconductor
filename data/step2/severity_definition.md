# severity 정의서 (step2)

최종 업데이트: 2026-01-30 14:38

- scratch는 학습/예측/시각화(severity 계산)에는 포함됩니다.
- 다만 top% 후보에서 pred_label이 scratch인 샘플은 sem으로 보내지 않고,
  'physical_damage_scratch_top_percent'로 별도 분리합니다.
- sem 후보/전송 리스트는 scratch를 제외한 top%에서 구성되며,
  그 안에서 random/blob/cluster는 sem_send에 반드시 포함됩니다.
