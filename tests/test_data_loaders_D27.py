import json

import pytest

import knowledge_base.data_loader as data_loader

from knowledge_base.data_loader import (
    get_crop_varieties,
    get_database_summary,
    get_disease,
    get_diseases_by_crop,
    get_planting_window,
    get_treatment,
    load_best_practices,
    load_crop_db,
    load_disease_kb,
    load_seasonal_calendar,
    load_treatment_db,
)


# ============================================================
# T-27.6.1
# All structured JSON files parse successfully
# ============================================================

@pytest.mark.parametrize(
    "filename",
    [
        "disease_kb.json",
        "treatment_db.json",
        "crop_db.json",
        "best_practices.json",
        "seasonal_calendar.json",
    ],
)
def test_structured_json_files_are_valid(filename):

    file_path = (
        data_loader.DATA_DIR
        / filename
    )

    assert file_path.exists()

    with open(
        file_path,
        "r",
        encoding="utf-8",
    ) as file:

        data = json.load(file)

    assert isinstance(data, dict)
    assert len(data) > 0


# ============================================================
# T-27.6.2
# Main loader return types
# ============================================================

def test_all_database_loaders_return_non_empty_dicts():

    databases = [
        load_disease_kb(),
        load_treatment_db(),
        load_crop_db(),
        load_best_practices(),
        load_seasonal_calendar(),
    ]

    for database in databases:

        assert isinstance(
            database,
            dict,
        )

        assert len(database) > 0


# ============================================================
# T-27.6.3
# Disease KB schema validity
# ============================================================

def test_disease_kb_schema():

    disease_kb = (
        load_disease_kb()
    )

    required_fields = {
        "name",
        "scientific_name",
        "crop",
        "symptoms",
        "severity",
        "region",
        "source",
    }

    for key, disease in (
        disease_kb.items()
    ):

        assert isinstance(
            key,
            str,
        )

        assert isinstance(
            disease,
            dict,
        )

        missing = (
            required_fields
            - set(
                disease.keys()
            )
        )

        assert not missing, (
            f"{key} is missing "
            f"fields: {missing}"
        )

        assert isinstance(
            disease["symptoms"],
            list,
        )

        assert len(
            disease["symptoms"]
        ) > 0

        assert isinstance(
            disease["region"],
            list,
        )


# ============================================================
# T-27.6.4
# Disease and crop coverage requirements
# ============================================================

def test_disease_kb_meets_minimum_coverage():

    disease_kb = (
        load_disease_kb()
    )

    assert len(
        disease_kb
    ) >= 12

    crops = {
        str(
            disease.get(
                "crop",
                "",
            )
        ).strip().lower()
        for disease
        in disease_kb.values()
        if disease.get("crop")
    }

    assert len(crops) >= 5


# ============================================================
# T-27.6.5
# Treatment DB schema
# ============================================================

def test_treatment_db_schema():

    treatment_db = (
        load_treatment_db()
    )

    required_fields = {
        "chemical",
        "organic",
        "cultural",
        "prevention",
    }

    for key, treatment in (
        treatment_db.items()
    ):

        assert isinstance(
            treatment,
            dict,
        )

        missing = (
            required_fields
            - set(
                treatment.keys()
            )
        )

        assert not missing, (
            f"{key} treatment "
            f"is missing: {missing}"
        )

        for field in (
            required_fields
        ):

            assert isinstance(
                treatment[field],
                list,
            )


# ============================================================
# T-27.6.6
# Crop DB schema
# ============================================================

def test_crop_db_schema():

    crop_db = load_crop_db()

    assert len(
        crop_db
    ) >= 5

    for crop_name, crop in (
        crop_db.items()
    ):

        assert isinstance(
            crop,
            dict,
        )

        assert (
            "varieties"
            in crop
        )

        assert isinstance(
            crop["varieties"],
            list,
        )

        for variety in (
            crop["varieties"]
        ):

            assert isinstance(
                variety,
                dict,
            )

            assert (
                "name"
                in variety
            )

            assert str(
                variety["name"]
            ).strip()


# ============================================================
# T-27.6.7
# Best-practices schema
# ============================================================

def test_best_practices_schema():

    best_practices = (
        load_best_practices()
    )

    required_categories = {
        "planting",
        "fertilizer",
        "irrigation",
        "pest_disease_management",
        "harvesting",
        "rotation",
        "sustainability",
    }

    for crop, practices in (
        best_practices.items()
    ):

        assert isinstance(
            practices,
            dict,
        )

        missing = (
            required_categories
            - set(
                practices.keys()
            )
        )

        assert not missing, (
            f"{crop} best practices "
            f"missing: {missing}"
        )

        for category in (
            required_categories
        ):

            assert isinstance(
                practices[category],
                list,
            )


# ============================================================
# T-27.6.8
# Seasonal calendar schema
# ============================================================

def test_seasonal_calendar_contains_maha_and_yala():

    calendar = (
        load_seasonal_calendar()
    )

    assert "maha" in calendar
    assert "yala" in calendar

    for season in (
        "maha",
        "yala",
    ):

        season_data = (
            calendar[season]
        )

        assert isinstance(
            season_data,
            dict,
        )

        assert (
            "crop_windows"
            in season_data
        )

        assert isinstance(
            season_data[
                "crop_windows"
            ],
            dict,
        )


# ============================================================
# T-27.6.9
# Disease helper
# ============================================================

def test_get_disease_returns_known_record():

    disease = get_disease(
        "rice_blast"
    )

    assert disease is not None

    assert (
        disease["crop"]
        .strip()
        .lower()
        == "rice"
    )

    assert (
        len(
            disease["symptoms"]
        )
        > 0
    )


# ============================================================
# T-27.6.10
# Disease filtering by crop
# ============================================================

def test_get_diseases_by_crop_returns_rice_diseases():

    diseases = (
        get_diseases_by_crop(
            "rice"
        )
    )

    assert len(diseases) > 0

    for disease in (
        diseases.values()
    ):

        assert (
            disease["crop"]
            .strip()
            .lower()
            == "rice"
        )


# ============================================================
# T-27.6.11
# Treatment helper
# ============================================================

def test_get_treatment_returns_known_record():

    treatment = (
        get_treatment(
            "rice_blast"
        )
    )

    assert treatment is not None

    assert (
        "chemical"
        in treatment
    )

    assert (
        "organic"
        in treatment
    )

    assert (
        "cultural"
        in treatment
    )

    assert (
        "prevention"
        in treatment
    )


# ============================================================
# T-27.6.12
# Crop variety helper
# ============================================================

def test_get_crop_varieties_returns_varieties():

    varieties = (
        get_crop_varieties(
            "maize"
        )
    )

    assert isinstance(
        varieties,
        list,
    )

    assert len(
        varieties
    ) > 0

    for variety in varieties:

        assert (
            "name"
            in variety
        )


# ============================================================
# T-27.6.13
# Seasonal planting-window helper
# ============================================================

def test_get_planting_window_returns_list():

    window = (
        get_planting_window(
            "maize",
            "maha",
        )
    )

    assert isinstance(
        window,
        list,
    )

    assert len(window) > 0


# ============================================================
# T-27.6.14
# Database summary matches actual data
# ============================================================

def test_database_summary_matches_loaded_data():

    summary = (
        get_database_summary()
    )

    assert (
        summary["diseases"]
        == len(
            load_disease_kb()
        )
    )

    assert (
        summary[
            "treatment_records"
        ]
        == len(
            load_treatment_db()
        )
    )

    assert (
        summary["crops"]
        == len(
            load_crop_db()
        )
    )

    assert (
        summary[
            "best_practice_crops"
        ]
        == len(
            load_best_practices()
        )
    )

    assert (
        summary[
            "season_groups"
        ]
        == len(
            load_seasonal_calendar()
        )
    )


# ============================================================
# T-27.6.15
# Missing file error handling
# ============================================================

def test_load_json_raises_file_not_found(
    monkeypatch,
    tmp_path,
):

    monkeypatch.setattr(
        data_loader,
        "DATA_DIR",
        tmp_path,
    )

    with pytest.raises(
        FileNotFoundError
    ):

        data_loader._load_json(
            "missing.json"
        )


# ============================================================
# T-27.6.16
# Invalid JSON error handling
# ============================================================

def test_load_json_rejects_invalid_json(
    monkeypatch,
    tmp_path,
):

    bad_file = (
        tmp_path
        / "invalid.json"
    )

    bad_file.write_text(
        "{this is invalid json",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        data_loader,
        "DATA_DIR",
        tmp_path,
    )

    with pytest.raises(
        ValueError
    ):

        data_loader._load_json(
            "invalid.json"
        )