"""Unit tests for scoring engine."""
import pytest
from datetime import datetime, timedelta, timezone

from app.services.scoring import compute_score, calculate_risk_level, explain_score, SIGNAL_PRESETS


def test_calculate_risk_level():
    """Test risk level calculation."""
    assert calculate_risk_level(95) == 'none'
    assert calculate_risk_level(90) == 'none'
    assert calculate_risk_level(75) == 'low'
    assert calculate_risk_level(60) == 'low'
    assert calculate_risk_level(45) == 'medium'
    assert calculate_risk_level(30) == 'medium'
    assert calculate_risk_level(15) == 'high'
    assert calculate_risk_level(0) == 'high'


def test_compute_score_hdfc_like():
    """Test scoring for HDFC-like entity with Wikipedia and App Store."""
    verifications = [
        {
            'status': 'verified',
            'source_type': 'wikipedia',
            'score_contrib': 45.0,
            'weight': 1.5,
            'expires_at': None
        },
        {
            'status': 'verified',
            'source_type': 'appstore',
            'score_contrib': 50.0,
            'weight': 1.5,
            'expires_at': None
        }
    ]
    lookalikes = []
    
    score, risk_level = compute_score(verifications, lookalikes)
    
    # 45*1.5 + 50*1.5 = 67.5 + 75 = 142.5, capped at 100
    assert score == 100.0
    assert risk_level == 'none'


def test_compute_score_new_domain():
    """Test scoring for new domain with no signals."""
    verifications = []
    lookalikes = []
    
    score, risk_level = compute_score(verifications, lookalikes)
    
    assert score == 0.0
    assert risk_level == 'high'


def test_compute_score_with_penalty():
    """Test scoring with homoglyph penalty."""
    verifications = [
        {
            'status': 'verified',
            'source_type': 'wikipedia',
            'score_contrib': 45.0,
            'weight': 1.5,
            'expires_at': None
        }
    ]
    lookalikes = [
        {
            'domain': 'paypai.com',
            'distance': 1,
            'flagged': True
        }
    ]
    
    score, risk_level = compute_score(verifications, lookalikes)
    
    # 45*1.5 - 40 = 67.5 - 40 = 27.5
    assert score == 27.5
    assert risk_level == 'high'


def test_compute_score_expired_verification():
    """Test scoring with expired verification."""
    past_date = datetime.now(timezone.utc) - timedelta(days=30)
    
    verifications = [
        {
            'status': 'verified',
            'source_type': 'wikipedia',
            'score_contrib': 45.0,
            'weight': 1.5,
            'expires_at': past_date
        }
    ]
    lookalikes = []
    
    score, risk_level = compute_score(verifications, lookalikes)
    
    # 45*1.5*0.5 = 33.75
    assert score == 33.75
    assert risk_level == 'medium'


def test_compute_score_needs_review():
    """Test that needs_review status is included."""
    verifications = [
        {
            'status': 'needs_review',
            'source_type': 'appstore',
            'score_contrib': 50.0,
            'weight': 1.5,
            'expires_at': None
        }
    ]
    lookalikes = []
    
    score, risk_level = compute_score(verifications, lookalikes)
    
    # 50*1.5 = 75
    assert score == 75.0
    assert risk_level == 'low'


def test_compute_score_rejected_ignored():
    """Test that rejected verifications are ignored."""
    verifications = [
        {
            'status': 'rejected',
            'source_type': 'wikipedia',
            'score_contrib': 45.0,
            'weight': 1.5,
            'expires_at': None
        }
    ]
    lookalikes = []
    
    score, risk_level = compute_score(verifications, lookalikes)
    
    assert score == 0.0
    assert risk_level == 'high'


def test_explain_score():
    """Test score explanation."""
    verifications = [
        {
            'status': 'verified',
            'source_type': 'wikipedia',
            'score_contrib': 45.0,
            'weight': 1.5,
            'expires_at': None
        },
        {
            'status': 'verified',
            'source_type': 'appstore',
            'score_contrib': 50.0,
            'weight': 1.5,
            'expires_at': None
        }
    ]
    lookalikes = []
    
    explanations = explain_score(verifications, lookalikes)
    
    assert len(explanations) == 2
    assert explanations[0]['source_type'] == 'wikipedia'
    assert explanations[0]['contribution'] == 67.5
    assert explanations[1]['source_type'] == 'appstore'
    assert explanations[1]['contribution'] == 75.0


def test_explain_score_with_penalty():
    """Test score explanation with penalty."""
    verifications = []
    lookalikes = [
        {
            'domain': 'paypai.com',
            'distance': 1,
            'flagged': True
        }
    ]
    
    explanations = explain_score(verifications, lookalikes)
    
    assert len(explanations) == 1
    assert explanations[0]['source_type'] == 'lookalike_penalty'
    assert explanations[0]['contribution'] == -40
