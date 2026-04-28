# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest
from microsoft_agents.hosting.dialogs.prompts.prompt_culture_models import (
    PromptCultureModels,
)

SUPPORTED_CULTURES = [
    PromptCultureModels.Bulgarian,
    PromptCultureModels.Chinese,
    PromptCultureModels.Dutch,
    PromptCultureModels.English,
    PromptCultureModels.French,
    PromptCultureModels.German,
    PromptCultureModels.Hindi,
    PromptCultureModels.Italian,
    PromptCultureModels.Japanese,
    PromptCultureModels.Korean,
    PromptCultureModels.Portuguese,
    PromptCultureModels.Spanish,
    PromptCultureModels.Swedish,
    PromptCultureModels.Turkish,
]


def _locale_variations(culture):
    """Generate (input_variation, expected_locale) tuples for a culture."""
    locale = culture.locale  # e.g. "en-us"
    parts = locale.split("-")
    prefix = parts[0]
    suffix = parts[1] if len(parts) > 1 else ""
    return [
        (locale, locale),  # exact: "en-us"
        (f"{prefix}-{suffix.upper()}", locale),  # cap ending: "en-US"
        (f"{prefix.capitalize()}-{suffix.capitalize()}", locale),  # title: "En-Us"
        (prefix.upper(), locale),  # all-caps two-letter: "EN"
        (prefix, locale),  # lowercase two-letter: "en"
    ]


LOCALE_VARIATIONS = [
    variation
    for culture in SUPPORTED_CULTURES
    for variation in _locale_variations(culture)
]


@pytest.mark.parametrize("locale_variation,expected", LOCALE_VARIATIONS)
def test_map_to_nearest_language(locale_variation, expected):
    result = PromptCultureModels.map_to_nearest_language(locale_variation)
    assert result == expected


def test_null_locale_does_not_raise():
    result = PromptCultureModels.map_to_nearest_language(None)
    assert result is None


def test_get_supported_cultures_returns_all():
    expected_locales = {c.locale for c in SUPPORTED_CULTURES}
    actual_locales = {c.locale for c in PromptCultureModels.get_supported_cultures()}
    assert expected_locales == actual_locales


def test_supported_cultures_have_required_fields():
    for culture in PromptCultureModels.get_supported_cultures():
        assert culture.locale, f"Culture missing locale"
        assert culture.separator, f"Culture {culture.locale} missing separator"
        assert culture.inline_or, f"Culture {culture.locale} missing inline_or"
        assert (
            culture.yes_in_language
        ), f"Culture {culture.locale} missing yes_in_language"
        assert (
            culture.no_in_language
        ), f"Culture {culture.locale} missing no_in_language"
