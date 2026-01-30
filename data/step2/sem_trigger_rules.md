# sem 트리거 규칙서 (step2 -> step3) 초안

최종 업데이트: 2026-01-30 14:38

## top% 계산 기준
- top% threshold는 전체 severity 분포(= scratch 포함)에서 계산합니다.
- top 5% threshold: 95.97
- top 10% threshold: 94.21

## routing
- pred_label == 'scratch' and in top%:
  - output: physical_damage_scratch_top5pct.csv / top10pct.csv
  - action: do_not_send_to_sem

## sem
- sem_candidates_top5pct.csv / sem_candidates_top10pct.csv:
  - scratch 제외(top% 내 non-scratch만)
- sem_send_top5pct.csv / sem_send_top10pct.csv:
  - non-scratch top% 안에서 random/blob/cluster는 반드시 포함
  - sem_budget을 설정하면 mandatory 먼저 포함하고 남는 슬롯은 severity 순으로 채움
