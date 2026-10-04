"""Synthetic demo data seeder for Outbreak Sentinel Agent.

Creates simulated cases (is_simulated = 1) to demonstrate outbreak and watch scenarios.
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
import random

from sentinel_agent.db import get_connection, init_db, record_diagnosis


def seed_demo_data(
    district: str = "Anuradhapura",
    crop: str = "Rice",
    disease: str = "Bacterial Leaf Blight",
    db_path: Optional[str] = None,
) -> Dict[str, int]:
    """Seeds simulated cases for end-to-end demo validation.

    1. Seeds 28 days of low historical background cases (1 case every few days).
    2. Seeds 6 high-confidence cluster cases in the last 48 hours.
    """
    init_db(db_path)
    now = datetime.now(timezone.utc)
    seeded_background = 0
    seeded_cluster = 0

    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        # Clean previous simulated entries for a clean run
        cursor.execute("DELETE FROM diagnosis_log WHERE is_simulated = 1;")
        conn.commit()

    # 1. 28 days of low background cases (0 to 1 case per 48h bin)
    for day in range(3, 28, 4):
        past_time = now - timedelta(days=day)
        record_diagnosis(
            crop=crop,
            disease=disease,
            district=district,
            confidence=round(random.uniform(0.75, 0.85), 2),
            created_at=past_time.isoformat(),
            is_simulated=True,
            db_path=db_path,
        )
        seeded_background += 1

    # 2. 6 simulated recent cluster cases in last 48 hours (confidence 0.80 - 0.95)
    recent_confidences = [0.82, 0.88, 0.91, 0.85, 0.94, 0.89]
    for i, conf in enumerate(recent_confidences):
        recent_time = now - timedelta(hours=random.randint(2, 40))
        record_diagnosis(
            crop=crop,
            disease=disease,
            district=district,
            confidence=conf,
            created_at=recent_time.isoformat(),
            is_simulated=True,
            db_path=db_path,
        )
        seeded_cluster += 1

    return {
        "background_cases": seeded_background,
        "recent_cluster_cases": seeded_cluster,
        "district": district,
        "crop": crop,
        "disease": disease,
    }
