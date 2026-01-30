"""
Prompt templates for LLM interactions

All prompts are in Korean as the analysis context is Korean semiconductor manufacturing.
"""

# Pattern Discovery Prompt Template
PATTERN_DISCOVERY_PROMPT = """
반도체 제조 패턴 분석 전문가로서 다음을 분석하세요.

## 발견된 패턴

**유형:** {pattern_type}

**증거:**
{evidence}

**통계적 유의성:**
- 상관계수: {correlation}
- P-value: {p_value}
- 신뢰도: {confidence}

**센서 데이터 요약:**
{sensor_summary}

**공정 이력:**
{process_history}

## 분석 요청

다음 질문에 구체적이고 실행 가능하게 답변하세요:

1. **근본 원인 (Root Cause)**
   - 이 패턴의 가장 가능성 높은 원인은?
   - 물리적/화학적 메커니즘은?
   - 왜 이 시기에 발생했는가?

2. **검증 방법**
   - 이 원인을 확인하려면 무엇을 해야 하나?
   - 추가로 필요한 데이터는?

3. **권장 조치**

   단기 (즉시~1주):
   - 구체적 실행 방법
   - 예상 효과
   - 소요 비용/시간
   - 위험도

   중기 (1~4주):
   - 구조적 개선 방안

   장기 (1~3개월):
   - 예방 체계 구축

4. **예상 영향**
   - 조치 시행 시 기대 효과
   - 미시행 시 리스크

구조화된 분석을 제공하세요.
"""


# Root Cause Analysis Prompt Template
ROOT_CAUSE_ANALYSIS_PROMPT = """
반도체 SEM 결함 분석 전문가로서 다음을 분석하세요.

## 결함 정보

**웨이퍼 ID:** {wafer_id}
**결함 유형:** {defect_type}
**결함 수량:** {defect_count}
**위치 패턴:** {location_pattern}
**신뢰도:** {confidence}

**공정 이력:**
{process_history}

**센서 데이터:**
{sensor_data}

**유사 과거 사례:**
{similar_cases}

## 분석 요청

1. **근본 원인 추정**
   - 가장 가능성 높은 원인 3가지
   - 각각의 발생 메커니즘
   - 확률적 판단

2. **공정 단계 특정**
   - 어느 공정에서 발생했는가?
   - 어느 장비/챔버?
   - 시간대 영향?

3. **권장 조치**
   - 즉시 조치 사항
   - 예방 방안
   - 모니터링 항목

간결하고 실행 가능하게 답변하세요.
"""


# Feedback Learning Prompt Template
FEEDBACK_LEARNING_PROMPT = """
엔지니어 의사결정 패턴을 분석하는 전문가입니다.

## 피드백 데이터

**분석 기간:** {date_range}
**총 의사결정:** {total_decisions}개
**승인율:** {approval_rate}

**거부 이유 분포:**
{rejection_reasons}

**구체적 사례 (최근 10개):**

{example_cases}

## 분석 요청

1. **의사결정 패턴**
   - 엔지니어가 승인하는 조건은?
   - 거부하는 조건은?
   - 수정하는 경우는?

2. **비용 민감도**
   - 어느 비용 수준까지 승인하는가?
   - 암묵적 임계값이 있는가?

3. **리스크 허용도**
   - HIGH risk: 어떻게 반응?
   - MEDIUM risk: 선별 기준?
   - 보수적? 공격적?

4. **신뢰 요인**
   - 무엇이 신뢰를 높이는가?
   - 무엇이 신뢰를 낮추는가?
   - 과거 false alarm의 영향?

5. **개선 제안**
   - 다음 AI 제안 시 무엇을 개선해야?
   - 어떤 정보를 추가로 제공하면 좋을까?
   - 제안 방식의 변경 필요?

구체적이고 실행 가능한 인사이트를 제공하세요.
"""


# Formatting Functions

def format_pattern_discovery_prompt(
    pattern_type: str,
    evidence: str,
    correlation: float,
    p_value: float,
    confidence: float,
    sensor_summary: str,
    process_history: str
) -> str:
    """
    Format pattern discovery prompt with variables

    Args:
        pattern_type: Type of pattern (e.g., "Edge-Ring", "Center")
        evidence: Evidence description
        correlation: Correlation coefficient (-1 to 1)
        p_value: Statistical p-value
        confidence: Confidence score (0-1)
        sensor_summary: Summary of sensor data
        process_history: Process history information

    Returns:
        Formatted prompt string

    Example:
        >>> prompt = format_pattern_discovery_prompt(
        ...     pattern_type="Edge-Ring",
        ...     evidence="201 웨이퍼에서 Edge-Ring 패턴 발견",
        ...     correlation=0.85,
        ...     p_value=0.001,
        ...     confidence=0.90,
        ...     sensor_summary="평균 etch rate: 3.95, 압력: 160 mTorr",
        ...     process_history="Chamber A, 1월 10-23일"
        ... )
    """
    return PATTERN_DISCOVERY_PROMPT.format(
        pattern_type=pattern_type,
        evidence=evidence,
        correlation=f"{correlation:.3f}",
        p_value=f"{p_value:.4f}",
        confidence=f"{confidence:.2%}",
        sensor_summary=sensor_summary,
        process_history=process_history
    )


def format_root_cause_prompt(
    wafer_id: str,
    defect_type: str,
    defect_count: int,
    location_pattern: str,
    confidence: float,
    process_history: str,
    sensor_data: str,
    similar_cases: str
) -> str:
    """
    Format root cause analysis prompt

    Args:
        wafer_id: Wafer identifier
        defect_type: Type of defect (e.g., "Particle", "Scratch")
        defect_count: Number of defects
        location_pattern: Location pattern (e.g., "edge", "center")
        confidence: Confidence score (0-1)
        process_history: Process history
        sensor_data: Sensor data summary
        similar_cases: Similar past cases

    Returns:
        Formatted prompt string

    Example:
        >>> prompt = format_root_cause_prompt(
        ...     wafer_id="W0001",
        ...     defect_type="Particle",
        ...     defect_count=15,
        ...     location_pattern="edge",
        ...     confidence=0.85,
        ...     process_history="Chamber A, Etch_v3.2",
        ...     sensor_data="압력: 162 mTorr, 온도: 61°C",
        ...     similar_cases="W0025, W0026: 유사 패턴"
        ... )
    """
    return ROOT_CAUSE_ANALYSIS_PROMPT.format(
        wafer_id=wafer_id,
        defect_type=defect_type,
        defect_count=defect_count,
        location_pattern=location_pattern,
        confidence=f"{confidence:.2%}",
        process_history=process_history,
        sensor_data=sensor_data,
        similar_cases=similar_cases
    )


def format_feedback_learning_prompt(
    date_range: str,
    total_decisions: int,
    approval_rate: float,
    rejection_reasons: str,
    example_cases: str
) -> str:
    """
    Format feedback learning prompt

    Args:
        date_range: Date range of analysis (e.g., "2026-01-10 ~ 2026-01-23")
        total_decisions: Total number of decisions
        approval_rate: Approval rate (0-1)
        rejection_reasons: Distribution of rejection reasons
        example_cases: Specific example cases

    Returns:
        Formatted prompt string

    Example:
        >>> prompt = format_feedback_learning_prompt(
        ...     date_range="2026-01-10 ~ 2026-01-23",
        ...     total_decisions=100,
        ...     approval_rate=0.85,
        ...     rejection_reasons="비용 과다: 40%, 리스크 낮음: 35%, 기타: 25%",
        ...     example_cases="Case 1: W0001, 승인...\nCase 2: W0002, 거부..."
        ... )
    """
    return FEEDBACK_LEARNING_PROMPT.format(
        date_range=date_range,
        total_decisions=total_decisions,
        approval_rate=f"{approval_rate:.1%}",
        rejection_reasons=rejection_reasons,
        example_cases=example_cases
    )


# Quick access prompt builders with common defaults

def build_edge_ring_analysis(
    wafer_count: int,
    avg_etch_rate: float,
    avg_pressure: float
) -> str:
    """
    Quick builder for Edge-Ring pattern analysis

    Args:
        wafer_count: Number of wafers with pattern
        avg_etch_rate: Average etch rate
        avg_pressure: Average pressure

    Returns:
        Formatted prompt
    """
    evidence = f"{wafer_count}개 웨이퍼에서 Edge-Ring 패턴 발견"
    sensor_summary = f"""
- 평균 etch rate: {avg_etch_rate:.2f} µm/min
- 평균 압력: {avg_pressure:.1f} mTorr
- 패턴 발생률: {(wafer_count/1252)*100:.1f}%
"""
    process_history = "Chamber A, B, C 공용 발생\n1월 10일~23일 기간"

    return format_pattern_discovery_prompt(
        pattern_type="Edge-Ring",
        evidence=evidence,
        correlation=0.85,
        p_value=0.001,
        confidence=0.90,
        sensor_summary=sensor_summary,
        process_history=process_history
    )


def build_particle_defect_analysis(
    wafer_id: str,
    defect_count: int,
    chamber: str,
    pressure: float
) -> str:
    """
    Quick builder for Particle defect analysis

    Args:
        wafer_id: Wafer identifier
        defect_count: Number of particle defects
        chamber: Chamber ID
        pressure: Pressure reading

    Returns:
        Formatted prompt
    """
    sensor_data = f"""
- 압력: {pressure:.1f} mTorr (기준: 145-155)
- Chamber: {chamber}
"""
    similar_cases = "과거 유사 사례: 압력 >158에서 Particle 다발 발생"

    return format_root_cause_prompt(
        wafer_id=wafer_id,
        defect_type="Particle",
        defect_count=defect_count,
        location_pattern="edge",
        confidence=0.80,
        process_history=f"Chamber {chamber}, Etch_v3.2",
        sensor_data=sensor_data,
        similar_cases=similar_cases
    )
