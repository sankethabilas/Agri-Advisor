from types import SimpleNamespace

import agents.crop.agent as crop_module
from agents.crop.agent import CropAgent


# ============================================================
# Helper
# ============================================================

def create_crop_agent():
    """
    Create CropAgent without running __init__ so unit tests
    do not reload JSON files unnecessarily.
    """

    agent = CropAgent.__new__(
        CropAgent
    )

    agent.crop_db = {}

    agent.best_practices = {
        "rice": {
            "sustainability": [
                "Apply organic matter."
            ],
            "planting": [
                "Use certified seed."
            ],
            "fertilizer": [
                "Follow DOA recommendations."
            ],
            "irrigation": [
                "Maintain correct water depth."
            ],
            "pest_disease_management": [
                "Use integrated pest management."
            ],
            "harvesting": [
                "Harvest at physiological maturity."
            ],
            "rotation": [
                "Rotate with legumes."
            ],
        }
    }

    agent.seasonal_calendar = {}

    return agent


# ============================================================
# T-27.3.1
# Crop alias normalization
# ============================================================

def test_crop_name_normalization():

    agent = create_crop_agent()

    assert (
        agent.normalize_crop_name(
            "Paddy"
        )
        == "rice"
    )

    assert (
        agent.normalize_crop_name(
            "chili"
        )
        == "chilli"
    )

    assert (
        agent.normalize_crop_name(
            "corn"
        )
        == "maize"
    )


# ============================================================
# T-27.3.2
# Section 1 - Recommended varieties
# ============================================================

def test_varieties_section(
    monkeypatch
):

    agent = create_crop_agent()

    fake_varieties = [
        {
            "name": "Bg 352",
            "age_class_months": 3.5,
            "yield_potential_mt_ha": 6.5,
            "grain_type": "White Short Grain",
            "suitability_reasons": [
                "Suitable for dry zone cultivation"
            ],
        }
    ]

    monkeypatch.setattr(
        crop_module,
        "get_crop_varieties",
        lambda crop: fake_varieties,
    )

    result = (
        agent._build_varieties_section(
            normalized_crop="rice",
            display_crop="Rice",
            zone="DL1b",
            district="Anuradhapura",
            season="Maha",
        )
    )

    assert (
        "recommended_varieties"
        in result
    )

    assert len(
        result["recommended_varieties"]
    ) > 0

    assert (
        result[
            "recommended_varieties"
        ][0]["variety_name"]
        == "Bg 352"
    )


# ============================================================
# T-27.3.3
# Section 2 - Land preparation
# ============================================================

def test_land_preparation_section():

    agent = create_crop_agent()

    result = (
        agent._build_land_prep_section(
            normalized_crop="rice",
            display_crop="Rice",
        )
    )

    assert (
        "section_title"
        in result
    )

    assert (
        "first_plowing"
        in result
    )

    assert (
        "second_plowing_and_puddling"
        in result
    )

    assert (
        "bund_maintenance"
        in result
    )

    assert (
        "leveling"
        in result
    )


# ============================================================
# T-27.3.4
# Section 3 - Planting schedule
# ============================================================

def test_planting_section(
    monkeypatch
):

    agent = create_crop_agent()

    monkeypatch.setattr(
        crop_module,
        "get_planting_window",
        lambda crop, season: [
            "November"
        ],
    )

    result = (
        agent._build_planting_section(
            normalized_crop="rice",
            display_crop="Rice",
            season="Maha",
        )
    )

    assert (
        result["sowing_window"]
        == "November"
    )

    assert (
        "establishment_method"
        in result
    )

    assert (
        "seed_rate_kg_per_acre"
        in result
    )

    assert (
        "spacing"
        in result
    )


# ============================================================
# T-27.3.5
# Section 4 - Fertilizer management
# ============================================================

def test_fertilizer_section_has_four_stages():

    agent = create_crop_agent()

    result = (
        agent._build_fertilizer_section(
            normalized_crop="rice",
            display_crop="Rice",
            extent_acres=1.0,
        )
    )

    assert (
        "chemical_stages"
        in result
    )

    assert len(
        result["chemical_stages"]
    ) == 4

    assert (
        result[
            "chemical_stages"
        ][0]["stage_number"]
        == 1
    )

    assert (
        result[
            "chemical_stages"
        ][3]["stage_number"]
        == 4
    )


# ============================================================
# T-27.3.6
# Section 5 - Water management
# ============================================================

def test_water_management_section():

    agent = create_crop_agent()

    result = (
        agent._build_water_section(
            normalized_crop="rice",
            display_crop="Rice",
        )
    )

    assert (
        "regime"
        in result
    )

    assert (
        "Alternate Wetting and Drying"
        in result["regime"]
    )

    assert (
        "stages"
        in result
    )

    assert len(
        result["stages"]
    ) == 4


# ============================================================
# T-27.3.7
# Section 6 - Weed control
# ============================================================

def test_weed_management_section():

    agent = create_crop_agent()

    result = (
        agent._build_weed_section(
            normalized_crop="rice",
            display_crop="Rice",
        )
    )

    assert (
        "preventive_measures"
        in result
    )

    assert (
        "cultural_and_mechanical"
        in result
    )

    assert (
        "chemical_control"
        in result
    )

    assert (
        "practices"
        in result
    )


# ============================================================
# T-27.3.8
# Section 7 - Harvesting
# ============================================================

def test_harvest_section():

    agent = create_crop_agent()

    result = (
        agent._build_harvest_section(
            normalized_crop="rice",
            display_crop="Rice",
        )
    )

    assert (
        "maturity_indices"
        in result
    )

    assert (
        "drying_and_moisture_target"
        in result
    )

    assert (
        result[
            "drying_and_moisture_target"
        ][
            "target_moisture_percentage"
        ]
        == 13.5
    )

    assert (
        "storage"
        in result
    )


# ============================================================
# T-27.3.9
# Section 8 - Crop rotation
# ============================================================

def test_rotation_section():

    agent = create_crop_agent()

    result = (
        agent._build_rotation_section(
            normalized_crop="rice",
            display_crop="Rice",
        )
    )

    assert (
        "recommended_rotations"
        in result
    )

    assert len(
        result["recommended_rotations"]
    ) > 0

    assert (
        "benefits"
        in result
    )

    assert (
        "practices"
        in result
    )


# ============================================================
# T-27.3.10
# Complete eight-section advisory
# ============================================================

def test_complete_advisory_contains_all_eight_sections(
    monkeypatch
):

    agent = create_crop_agent()

    # Keep this test isolated from external data files.
    monkeypatch.setattr(
        agent,
        "_build_varieties_section",
        lambda *args, **kwargs: {
            "section_title": "Varieties"
        },
    )

    monkeypatch.setattr(
        agent,
        "_build_land_prep_section",
        lambda *args, **kwargs: {
            "section_title": "Land Preparation"
        },
    )

    monkeypatch.setattr(
        agent,
        "_build_planting_section",
        lambda *args, **kwargs: {
            "section_title": "Planting"
        },
    )

    monkeypatch.setattr(
        agent,
        "_build_fertilizer_section",
        lambda *args, **kwargs: {
            "section_title": "Fertilizer"
        },
    )

    monkeypatch.setattr(
        agent,
        "_build_water_section",
        lambda *args, **kwargs: {
            "section_title": "Water"
        },
    )

    monkeypatch.setattr(
        agent,
        "_build_weed_section",
        lambda *args, **kwargs: {
            "section_title": "Weed"
        },
    )

    monkeypatch.setattr(
        agent,
        "_build_harvest_section",
        lambda *args, **kwargs: {
            "section_title": "Harvest"
        },
    )

    monkeypatch.setattr(
        agent,
        "_build_rotation_section",
        lambda *args, **kwargs: {
            "section_title": "Rotation"
        },
    )

    request = SimpleNamespace(
        crop="rice",
        season="Maha",
        soil_type="Reddish Brown Earths",
        land_extent_acres=1.0,
        location=SimpleNamespace(
            district="Anuradhapura",
            agro_ecological_zone="DL1b",
        ),
    )

    response = (
        agent.get_crop_advice(
            request
        )
    )

    sections = (
        response.advisory_sections
    )

    assert len(sections) == 8

    expected_sections = {
        "1_varieties",
        "2_land_preparation",
        "3_planting_schedule",
        "4_fertilizer_management",
        "5_water_management",
        "6_weed_control",
        "7_harvesting_and_post_harvest",
        "8_crop_rotation_and_intercropping",
    }

    assert (
        set(sections.keys())
        == expected_sections
    )