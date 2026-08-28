from app.core.vocabulary import (
    INCOME_SOURCE_CATEGORY_DEFAULT_RELIABILITY,
    IncomeSourceCategory,
)


def test_every_income_source_category_has_a_cold_start_default():
    for category in IncomeSourceCategory:
        assert category in INCOME_SOURCE_CATEGORY_DEFAULT_RELIABILITY


def test_cold_start_defaults_match_spec_examples():
    # spec 4.3: "freelance client" = 55%, "salaried employer" = 90%
    assert INCOME_SOURCE_CATEGORY_DEFAULT_RELIABILITY[
        IncomeSourceCategory.FREELANCE_CLIENT
    ] == 0.55
    assert INCOME_SOURCE_CATEGORY_DEFAULT_RELIABILITY[
        IncomeSourceCategory.SALARIED_EMPLOYER
    ] == 0.90


def test_all_default_reliabilities_are_valid_probabilities():
    for value in INCOME_SOURCE_CATEGORY_DEFAULT_RELIABILITY.values():
        assert 0.0 <= value <= 1.0
