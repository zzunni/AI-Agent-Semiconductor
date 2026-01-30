"""
Wafer Processor: Sequential wafer processing engine for realistic fab simulation

This module handles:
- Sequential processing of wafers through the pipeline
- Stage-based routing (normal wafers complete early)
- Rework logic with new sensor data generation
- Yield calculation and tracking
"""

import streamlit as st
import numpy as np
from datetime import datetime
import time


def process_next_wafer_in_lot(lot_id):
    """
    Process the next wafer in the LOT sequentially

    This is the main engine that drives sequential wafer processing.
    Each wafer goes through one stage at a time, with decisions at each stage.

    Returns:
        'CONTINUE': More wafers to process, call again
        'COMPLETE': All wafers processed, LOT done
        'WAITING': Current wafer needs engineer decision
        'ERROR': Something went wrong
    """
    if 'active_lots' not in st.session_state:
        return 'ERROR'

    # Find the LOT
    lot = None
    for l in st.session_state['active_lots']:
        if l['lot_id'] == lot_id:
            lot = l
            break

    if not lot:
        return 'ERROR'

    # Find next wafer to process
    wafer = get_next_queued_wafer(lot)

    if not wafer:
        # Check if all wafers are done
        all_done = all(w['status'] in ['COMPLETED', 'SCRAPPED'] for w in lot['wafers'])

        if all_done:
            # All wafers processed - LOT complete
            lot['status'] = 'COMPLETED'
            calculate_final_yield(lot)
            return 'COMPLETE'

        # Some wafers still waiting for decisions
        return 'WAITING'

    # Process this wafer through its current stage
    wafer['status'] = 'PROCESSING'
    lot['stats']['processing'] = 1
    lot['stats']['queued'] = sum(1 for w in lot['wafers'] if w['status'] == 'QUEUED')

    result = process_wafer_stage(wafer, wafer['current_stage'])

    if result['needs_decision']:
        # Add to decision queue and wait
        wafer['status'] = 'WAITING_DECISION'
        lot['stats']['processing'] = 0
        lot['stats']['waiting'] = sum(1 for w in lot['wafers'] if w['status'] == 'WAITING_DECISION')

        add_to_decision_queue(wafer, result['decision_data'])
        return 'WAITING'

    if result['outcome'] == 'PASS':
        # Normal result - complete wafer
        complete_wafer(wafer, lot)

        # Continue to next wafer
        return 'CONTINUE'

    # Should not reach here
    return 'ERROR'


def get_next_queued_wafer(lot):
    """Find the next QUEUED wafer to process"""
    for wafer in lot['wafers']:
        if wafer['status'] == 'QUEUED':
            return wafer
    return None


def process_wafer_stage(wafer, stage, is_rework=False):
    """
    Process wafer through a specific stage

    Args:
        wafer: Wafer object
        stage: 'Stage 0' | 'Stage 1' | 'Stage 2A' | 'Stage 2B' | 'Stage 3'
        is_rework: Whether this is a rework attempt

    Returns:
        {
            'needs_decision': bool,
            'outcome': 'PASS' | 'FAIL',
            'decision_data': {...} if needs_decision else None
        }
    """

    # 1. Generate sensor data (NEW if rework)
    if is_rework:
        sensor_data = generate_rework_sensor_data(wafer, stage)
    else:
        sensor_data = generate_stage_sensor_data(stage)

    # 2. Run AI analysis
    ai_result = run_stage_ai_analysis(stage, sensor_data)

    # 3. Record in stage history
    wafer['stage_history'].append({
        'stage': stage,
        'attempt': wafer.get('rework_count', 0) + 1,
        'result': 'PENDING',
        'ai_recommendation': ai_result['recommendation'],
        'sensor_data': sensor_data,
        'timestamp': datetime.now().isoformat()
    })

    # 4. Determine if decision needed
    if ai_result['anomaly_detected']:
        # Needs engineer decision
        return {
            'needs_decision': True,
            'outcome': 'FAIL',
            'decision_data': {
                'stage': stage,
                'ai_recommendation': ai_result['recommendation'],
                'ai_confidence': ai_result['confidence'],
                'ai_reasoning': ai_result['reasoning'],
                'sensor_data': sensor_data,
                'available_options': get_stage_options(stage),
                'economics': ai_result.get('economics', {}),
                'wafer_data': sensor_data,
                'yield_pred': ai_result.get('yield_pred')  # Add yield_pred for Stage 1
            }
        }
    else:
        # Normal - but still need engineer review (Option 2: Always show in Decision Queue)
        return {
            'needs_decision': True,  # ← Changed to True (always show in queue)
            'outcome': 'PASS',
            'decision_data': {
                'stage': stage,
                'ai_recommendation': ai_result['recommendation'],
                'ai_confidence': ai_result['confidence'],
                'ai_reasoning': ai_result['reasoning'],
                'sensor_data': sensor_data,
                'available_options': get_stage_options(stage),
                'economics': ai_result.get('economics', {}),
                'wafer_data': sensor_data,
                'yield_pred': ai_result.get('yield_pred')
            }
        }


def generate_stage_sensor_data(stage):
    """Generate sensor data for a stage (normal processing)"""

    if stage == 'Stage 0':
        # 10 sensors for Stage 0
        etch_rate = np.random.normal(3.5, 0.3)
        pressure = np.random.normal(150, 10)
        temperature = np.random.normal(65, 3)

        return {
            'etch_rate': float(etch_rate),
            'pressure': float(pressure),
            'temperature': float(temperature),
            'rf_power': float(np.random.normal(500, 30)),
            'gas_flow': float(np.random.normal(50, 5)),
            'endpoint_time': float(np.random.normal(60, 5)),
            'uniformity': float(np.random.normal(0.95, 0.03)),
            'chamber_temp': float(np.random.normal(25, 2)),
            'power_stability': float(np.random.normal(0.98, 0.02)),
            'process_pressure': float(np.random.normal(155, 8))
        }

    elif stage == 'Stage 1':
        # Stage 1 inline measurements (4 additional)
        return {
            'cd_uniformity': float(np.random.normal(0.92, 0.04)),
            'film_thickness': float(np.random.normal(500, 30)),
            'line_width': float(np.random.normal(50, 3)),
            'edge_bead': float(np.random.normal(2.0, 0.5))
        }

    elif stage == 'Stage 2A':
        # WAT (Wafer Acceptance Test) data
        return {
            'electrical_uniformity': float(np.random.normal(0.90, 0.05)),
            'contact_resistance': float(np.random.normal(100, 15)),
            'leakage_current': float(np.random.normal(1e-9, 5e-10)),
            'breakdown_voltage': float(np.random.normal(50, 5))
        }

    elif stage == 'Stage 2B':
        # Wafermap pattern data
        return {
            'defect_count': int(np.random.poisson(10)),
            'pattern_type': np.random.choice(['Edge-Ring', 'Center', 'Random', 'Scratch']),
            'severity_score': float(np.random.uniform(0.3, 0.9))
        }

    elif stage == 'Stage 3':
        # SEM/Root cause data
        return {
            'defect_type': np.random.choice(['Particle', 'Etch residue', 'Film delamination']),
            'defect_size_nm': float(np.random.normal(50, 15)),
            'composition': 'SiO2',
            'root_cause_confidence': float(np.random.uniform(0.7, 0.95))
        }

    # Unknown stage
    return {}


def generate_rework_sensor_data(wafer, stage):
    """
    Generate NEW sensor data for reworked wafer

    Real fab: After rework, wafer goes through process again
    → New sensor readings (different from before)
    → 70% chance of improvement
    → 30% chance still defective or worse
    """

    # Get previous sensor data
    previous_data = wafer['stage_history'][-1]['sensor_data']

    # Simulate rework effect
    improvement_roll = np.random.random()

    if stage == 'Stage 0':
        if improvement_roll < 0.7:
            # 70% chance: Improved - tighter distribution
            etch_rate = np.random.normal(3.5, 0.2)
            pressure = np.random.normal(150, 8)
            temperature = np.random.normal(65, 2)
        else:
            # 30% chance: Still defective or worse
            etch_rate = np.random.normal(3.6, 0.4)
            pressure = np.random.normal(155, 12)
            temperature = np.random.normal(66, 4)

        return {
            'etch_rate': float(etch_rate),
            'pressure': float(pressure),
            'temperature': float(temperature),
            'rf_power': float(np.random.normal(500, 30)),
            'gas_flow': float(np.random.normal(50, 5)),
            'endpoint_time': float(np.random.normal(60, 5)),
            'uniformity': float(np.random.normal(0.95, 0.03)),
            'chamber_temp': float(np.random.normal(25, 2)),
            'power_stability': float(np.random.normal(0.98, 0.02)),
            'process_pressure': float(np.random.normal(155, 8)),
            'is_rework': True,
            'rework_attempt': wafer.get('rework_count', 0) + 1,
            'previous_etch_rate': previous_data.get('etch_rate'),
            'previous_pressure': previous_data.get('pressure')
        }

    elif stage == 'Stage 1':
        if improvement_roll < 0.7:
            # Improved inline measurements
            cd_uniformity = np.random.normal(0.94, 0.03)
            film_thickness = np.random.normal(500, 20)
        else:
            # Still problematic
            cd_uniformity = np.random.normal(0.89, 0.05)
            film_thickness = np.random.normal(480, 40)

        return {
            'cd_uniformity': float(cd_uniformity),
            'film_thickness': float(film_thickness),
            'line_width': float(np.random.normal(50, 3)),
            'edge_bead': float(np.random.normal(2.0, 0.5)),
            'is_rework': True,
            'rework_attempt': wafer.get('rework_count', 0) + 1
        }

    return {}


def run_stage_ai_analysis(stage, sensor_data):
    """
    Run AI analysis on sensor data for a given stage

    Returns:
        {
            'anomaly_detected': bool,
            'recommendation': str,
            'confidence': float,
            'reasoning': str,
            'economics': {...}
        }
    """

    if stage == 'Stage 0':
        # Anomaly detection based on sensor values
        etch_rate = sensor_data['etch_rate']
        pressure = sensor_data['pressure']
        temperature = sensor_data['temperature']

        # Check for anomalies
        is_anomaly = (etch_rate > 3.8 or etch_rate < 3.2 or
                     pressure > 160 or pressure < 140)

        if is_anomaly:
            anomaly_score = min(1.0, (abs(etch_rate - 3.5) / 0.5 + abs(pressure - 150) / 20) / 2)

            issues = []
            if etch_rate > 3.8:
                issues.append(f"High etch_rate: {etch_rate:.2f}")
            if pressure > 160:
                issues.append(f"High pressure: {pressure:.1f}")

            return {
                'anomaly_detected': True,
                'recommendation': 'INLINE',
                'confidence': 0.75 + anomaly_score * 0.2,
                'reasoning': f"Anomaly detected: {', '.join(issues)}. Recommend inline inspection.",
                'economics': {
                    'cost': 150,
                    'loss': 12000,
                    'benefit': 11850
                }
            }
        else:
            # Normal - no inspection needed
            return {
                'anomaly_detected': False,
                'recommendation': 'PASS',
                'confidence': 0.90,
                'reasoning': "All sensors within normal range",
                'economics': {'cost': 0, 'loss': 0, 'benefit': 0}
            }

    elif stage == 'Stage 1':
        # Yield prediction based on inline data
        cd_uniformity = sensor_data.get('cd_uniformity', 0.92)
        film_thickness = sensor_data.get('film_thickness', 500)

        # Simple yield model
        yield_pred = min(1.0, cd_uniformity * (1 - abs(film_thickness - 500) / 1000))

        if yield_pred < 0.85:
            # Low yield prediction
            wafer_value = 1000
            rework_cost = 200

            value_proceed = yield_pred * wafer_value
            value_rework = min(1.0, yield_pred + 0.15) * wafer_value - rework_cost

            if value_rework > value_proceed:
                recommendation = 'REWORK'
            elif yield_pred < 0.5:
                recommendation = 'SCRAP'
            else:
                recommendation = 'PROCEED'

            return {
                'anomaly_detected': True,
                'recommendation': recommendation,
                'confidence': 0.82,
                'reasoning': f"Predicted yield: {yield_pred:.1%}. Economic analysis suggests {recommendation}.",
                'economics': {
                    'cost': rework_cost if recommendation == 'REWORK' else 0,
                    'proceed_value': value_proceed,
                    'rework_value': value_rework,
                    'benefit': max(value_proceed, value_rework)
                },
                'yield_pred': yield_pred
            }
        else:
            # Good yield - no action needed
            return {
                'anomaly_detected': False,
                'recommendation': 'PASS',
                'confidence': 0.88,
                'reasoning': f"Good predicted yield: {yield_pred:.1%}",
                'economics': {'cost': 0, 'loss': 0, 'benefit': 0},
                'yield_pred': yield_pred
            }

    # Stage 2A: WAT analysis
    elif stage == 'Stage 2A':
        # 50% chance needs pattern analysis
        needs_analysis = np.random.random() < 0.5

        if needs_analysis:
            return {
                'anomaly_detected': True,
                'recommendation': 'PROCEED',
                'confidence': 0.80,
                'reasoning': "Wafermap shows patterns that need investigation",
                'economics': {'cost': 500, 'loss': 0, 'benefit': 2000}
            }
        else:
            return {
                'anomaly_detected': False,
                'recommendation': 'PASS',
                'confidence': 0.90,
                'reasoning': "WAT results normal",
                'economics': {'cost': 0, 'loss': 0, 'benefit': 0}
            }

    # Stage 2B: Pattern analysis
    elif stage == 'Stage 2B':
        # 40% chance needs SEM analysis
        needs_sem = np.random.random() < 0.4

        if needs_sem:
            return {
                'anomaly_detected': True,
                'recommendation': 'PROCEED',
                'confidence': 0.75,
                'reasoning': "Pattern detected: Edge-Ring defect cluster",
                'economics': {'cost': 1000, 'loss': 0, 'benefit': 5000}
            }
        else:
            return {
                'anomaly_detected': False,
                'recommendation': 'PASS',
                'confidence': 0.85,
                'reasoning': "No significant patterns detected",
                'economics': {'cost': 0, 'loss': 0, 'benefit': 0}
            }

    # Stage 3: Root cause analysis
    elif stage == 'Stage 3':
        # Always needs engineer review for root cause
        return {
            'anomaly_detected': True,
            'recommendation': 'COMPLETE',
            'confidence': 0.82,
            'reasoning': "Root cause identified: Chamber temperature drift",
            'economics': {'cost': 2000, 'loss': 0, 'benefit': 10000}
        }

    # Unknown stage
    return {
        'anomaly_detected': False,
        'recommendation': 'PASS',
        'confidence': 0.85,
        'reasoning': "Stage analysis complete",
        'economics': {'cost': 0, 'loss': 0, 'benefit': 0}
    }


def get_stage_options(stage):
    """Get available decision options for a stage"""

    stage_options = {
        'Stage 0': ['INLINE', 'SKIP'],
        'Stage 1': ['SKIP', 'PROCEED', 'REWORK', 'SCRAP'],
        'Stage 2A': ['PROCEED', 'SKIP'],
        'Stage 2B': ['PROCEED', 'SKIP'],
        'Stage 3': ['COMPLETE', 'INVESTIGATE']
    }

    return stage_options.get(stage, ['PROCEED'])


def add_to_decision_queue(wafer, decision_data):
    """Add wafer to decision queue for engineer review"""

    if 'pending_decisions' not in st.session_state:
        st.session_state['pending_decisions'] = []

    decision = {
        'id': f"{wafer['wafer_id']}-{decision_data['stage'].lower().replace(' ', '')}",
        'wafer_id': wafer['wafer_id'],
        'lot_id': wafer['lot_id'],
        'stage': decision_data['stage'],
        'priority': determine_priority(decision_data),
        'ai_recommendation': decision_data['ai_recommendation'],
        'ai_confidence': decision_data['ai_confidence'],
        'ai_reasoning': decision_data['ai_reasoning'],
        'available_options': decision_data['available_options'],
        'economics': decision_data.get('economics', {}),
        'wafer_data': decision_data.get('wafer_data', {}),
        'yield_pred': decision_data.get('yield_pred'),
        'time_elapsed': '< 1 min',
        'created_at': datetime.now()
    }

    st.session_state['pending_decisions'].append(decision)

    print(f"[DEBUG] Decision added to queue: {decision['id']}")


def determine_priority(decision_data):
    """Determine priority based on AI analysis"""

    confidence = decision_data['ai_confidence']
    stage = decision_data['stage']

    if stage == 'Stage 1' and decision_data.get('yield_pred', 1.0) < 0.5:
        return '🔴 HIGH'
    elif confidence > 0.85:
        return '🔴 HIGH'
    elif confidence > 0.75:
        return '🟡 MEDIUM'
    else:
        return '🟢 LOW'


def complete_wafer(wafer, lot):
    """Mark wafer as completed"""

    wafer['status'] = 'COMPLETED'
    wafer['completion_stage'] = wafer['current_stage']
    wafer['completed_at'] = datetime.now().isoformat()
    wafer['final_status'] = 'COMPLETED'

    # Update LOT stats
    lot['stats']['completed'] += 1
    lot['stats']['processing'] = 0
    lot['stats']['queued'] = sum(1 for w in lot['wafers'] if w['status'] == 'QUEUED')

    # Update yield stats
    if wafer['completion_stage'] == 'Stage 0':
        lot['yield']['completed_at_stage0'] += 1
    elif wafer['completion_stage'] == 'Stage 1':
        lot['yield']['completed_at_stage1'] += 1

    if wafer.get('rework_count', 0) > 0:
        lot['yield']['completed_after_rework'] += 1

    print(f"[DEBUG] Wafer {wafer['wafer_id']} completed at {wafer['completion_stage']}")


def calculate_final_yield(lot):
    """Calculate comprehensive yield metrics for completed LOT"""

    total = lot['wafer_count']
    completed = lot['stats']['completed']
    scrapped = lot['stats']['scrapped']

    # Overall yield
    processed = completed + scrapped
    yield_rate = (completed / processed * 100) if processed > 0 else 0

    # Breakdown scrapped wafers by stage
    scrapped_stage1 = sum(1 for w in lot['wafers']
                         if w['status'] == 'SCRAPPED' and w.get('completion_stage') == 'Stage 1')
    scrapped_stage3 = sum(1 for w in lot['wafers']
                         if w['status'] == 'SCRAPPED' and w.get('completion_stage') == 'Stage 3')

    # Cost breakdown
    total_cost = sum(w.get('total_cost', 0) for w in lot['wafers'])

    lot['yield']['total_wafers'] = total
    lot['yield']['completed_wafers'] = completed
    lot['yield']['scrapped_wafers'] = scrapped
    lot['yield']['scrapped_stage1'] = scrapped_stage1  # Defective wafers
    lot['yield']['scrapped_stage3_sem'] = scrapped_stage3  # SEM destructive testing
    lot['yield']['yield_rate'] = yield_rate
    lot['yield']['total_cost'] = total_cost
    lot['yield']['cost_per_good_wafer'] = total_cost / completed if completed > 0 else 0

    print(f"[DEBUG] LOT {lot['lot_id']} yield: {yield_rate:.1f}% ({completed}/{total})")
    print(f"[DEBUG] Scrapped breakdown: Stage 1 (defective): {scrapped_stage1}, Stage 3 (SEM): {scrapped_stage3}")

    return lot['yield']


def initialize_wafer(lot_id, wafer_number):
    """Initialize a new wafer with proper structure"""

    wafer_id = f"{lot_id[-8:]}-W{wafer_number:02d}"

    return {
        'wafer_id': wafer_id,
        'lot_id': lot_id,
        'wafer_number': wafer_number,

        # Processing state
        'current_stage': 'Stage 0',
        'status': 'QUEUED',
        'completion_stage': None,

        # Rework tracking
        'rework_count': 0,
        'rework_history': [],

        # Stage history
        'stage_history': [],

        # Final status
        'final_status': 'IN_PROGRESS',
        'completed_at': None,
        'total_cost': 0.0
    }
