# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Tests for predicate helper utilities."""

from typing import cast

import pytest
from microsoft_agents.activity import Activity, Attachment as SdkAttachment
from pydantic import BaseModel

from microsoft_agents.testing.core.fluent import Expect, Select
from microsoft_agents.testing.utils import contains
from microsoft_agents.testing.utils.contains import Contains


class Attachment(BaseModel):
    """Attachment-like model used by predicate helper tests."""

    content_type: str
    content: dict | None = None


class ActivityLike(BaseModel):
    """Activity-like model with nested data and attachments."""

    name: str
    channel_data: dict | None = None
    attachments: list[Attachment] | None = None


def is_hero_card(value):
    """Return true when a traversed value is a hero card content type."""
    return value == "application/vnd.microsoft.card.hero"


class TestContains:
    """Tests for the contains() predicate helper."""

    def test_matches_direct_model_property(self):
        """contains() can match a property on a Pydantic model."""
        activity = ActivityLike(name="message")

        assert contains(lambda value: value == "message")(activity)

    def test_matches_nested_dict_property(self):
        """contains() can match a property on a nested dictionary."""
        activity = ActivityLike(
            name="message",
            channel_data={"tenant": {"id": "tenant-1"}},
        )

        assert contains(lambda value: value == "tenant-1")(activity)

    def test_matches_nested_list_item_property(self):
        """contains() can match a property inside an item in a nested list."""
        activity = ActivityLike(
            name="message",
            attachments=[
                Attachment(content_type="application/vnd.microsoft.card.hero"),
            ],
        )

        assert contains(is_hero_card)(activity)

    def test_matches_nested_list_item_object(self):
        """contains() can match a nested list item object."""
        activity = ActivityLike(
            name="message",
            attachments=[
                Attachment(content_type="application/vnd.microsoft.card.hero"),
            ],
        )

        assert contains(
            lambda value: isinstance(value, Attachment)
            and value.content_type == "application/vnd.microsoft.card.hero"
        )(activity)

    def test_matches_nested_item_with_dict_filter(self):
        """contains() can match a nested object using dict criteria."""
        activity = ActivityLike(
            name="message",
            attachments=[
                Attachment(content_type="application/vnd.microsoft.card.hero"),
            ],
        )

        assert contains({"content_type": "application/vnd.microsoft.card.hero"})(
            activity
        )

    def test_matches_nested_item_with_kwargs(self):
        """contains() can match a nested object using keyword criteria."""
        activity = ActivityLike(
            name="message",
            attachments=[
                Attachment(content_type="application/vnd.microsoft.card.hero"),
            ],
        )

        assert contains(content_type="application/vnd.microsoft.card.hero")(activity)

    def test_matches_sdk_model_field_name_when_model_uses_alias(self):
        """contains() supports Python field names for SDK models with aliases."""
        activity = Activity(
            type="message",
            attachments=[
                SdkAttachment(content_type="application/vnd.microsoft.card.hero"),
            ],
        )

        assert contains(content_type="application/vnd.microsoft.card.hero")(activity)

    def test_expect_property_contains_matches_sdk_alias_dump(self):
        """contains() supports SDK field names after Expect dumps model aliases."""
        activity = Activity(
            type="message",
            attachments=[
                SdkAttachment(content_type="application/vnd.microsoft.card.hero"),
            ],
        )

        Expect([activity]).that_for_any(
            attachments=contains(content_type="application/vnd.microsoft.card.hero")
        )

    def test_contains_class_accepts_dict_filter(self):
        """Contains can be constructed with the same filter type as contains()."""
        activity = ActivityLike(
            name="message",
            attachments=[
                Attachment(content_type="application/vnd.microsoft.card.hero"),
            ],
        )

        assert Contains({"content_type": "application/vnd.microsoft.card.hero"})(
            activity
        )

    def test_contains_class_accepts_kwargs(self):
        """Contains can be constructed with keyword criteria."""
        activity = ActivityLike(
            name="message",
            attachments=[
                Attachment(content_type="application/vnd.microsoft.card.hero"),
            ],
        )

        assert Contains(content_type="application/vnd.microsoft.card.hero")(activity)

    def test_empty_dict_filter_can_be_combined_with_kwargs(self):
        """An empty dict is valid when keyword criteria provide the filter."""
        activity = ActivityLike(
            name="message",
            attachments=[
                Attachment(content_type="application/vnd.microsoft.card.hero"),
            ],
        )

        assert contains({}, content_type="application/vnd.microsoft.card.hero")(
            activity
        )

    def test_requires_filter_or_keyword_criteria(self):
        """contains() rejects the unfiltered case instead of matching everything."""
        with pytest.raises(ValueError, match="criteria"):
            contains()

        with pytest.raises(ValueError, match="criteria"):
            Contains()

        with pytest.raises(ValueError, match="criteria"):
            contains({})

        with pytest.raises(ValueError, match="criteria"):
            Contains({})

    def test_rejects_explicit_none_filter(self):
        """contains() does not accept None as a filter."""
        with pytest.raises(ValueError, match="cannot be None"):
            contains(None)

        with pytest.raises(ValueError, match="cannot be None"):
            Contains(None)

        with pytest.raises(ValueError, match="cannot be None"):
            contains(None, content_type="application/vnd.microsoft.card.hero")

    def test_rejects_invalid_filter_type(self):
        """contains() requires a callable or dict filter."""
        with pytest.raises(ValueError, match="dictionary or callable"):
            contains("application/vnd.microsoft.card.hero")

    def test_kwargs_override_dict_filter_values(self):
        """contains() merges kwargs into dict criteria like Select and Expect."""
        activity = ActivityLike(
            name="message",
            attachments=[
                Attachment(content_type="application/vnd.microsoft.card.hero"),
            ],
        )

        assert contains(
            {"content_type": "application/vnd.microsoft.card.thumbnail"},
            content_type="application/vnd.microsoft.card.hero",
        )(activity)

    def test_depth_limits_search_depth(self):
        """contains().depth() stops descending when depth is too shallow."""
        activity = ActivityLike(
            name="message",
            attachments=[
                Attachment(content_type="application/vnd.microsoft.card.hero"),
            ],
        )

        assert not contains(is_hero_card).depth(1)(activity)
        assert not contains(content_type="application/vnd.microsoft.card.hero").depth(
            1
        )(activity)

    def test_depth_returns_new_contains_instance(self):
        """contains().depth() returns a new predicate without mutating the original."""
        activity = ActivityLike(
            name="message",
            attachments=[
                Attachment(content_type="application/vnd.microsoft.card.hero"),
            ],
        )
        predicate = contains(is_hero_card)
        shallow_predicate = predicate.depth(1)

        assert predicate is not shallow_predicate
        assert predicate(activity)
        assert not shallow_predicate(activity)

    def test_depth_raises_for_negative_value(self):
        """contains().depth() raises ValueError for negative depth."""
        with pytest.raises(ValueError, match="non-negative"):
            contains(is_hero_card).depth(-1)

    def test_returns_false_for_non_container_source(self):
        """contains() returns false instead of raising for scalar source values."""
        assert not contains(lambda value: value == "expected")(
            "not a traversable source"
        )

    def test_select_where_filters_by_nested_list_item_property(self):
        """contains() works as a root callable for Select.where()."""
        activities = [
            ActivityLike(
                name="hero",
                attachments=[
                    Attachment(content_type="application/vnd.microsoft.card.hero"),
                ],
            ),
            ActivityLike(
                name="thumbnail",
                attachments=[
                    Attachment(content_type="application/vnd.microsoft.card.thumbnail"),
                ],
            ),
            ActivityLike(name="empty", attachments=[]),
        ]

        selected = Select(activities).where(contains(is_hero_card)).get()

        assert [cast(ActivityLike, activity).name for activity in selected] == ["hero"]

    def test_select_where_filters_by_nested_list_item_kwargs(self):
        """contains() supports Select.where() with keyword criteria."""
        activities = [
            ActivityLike(
                name="hero",
                attachments=[
                    Attachment(content_type="application/vnd.microsoft.card.hero"),
                ],
            ),
            ActivityLike(
                name="thumbnail",
                attachments=[
                    Attachment(content_type="application/vnd.microsoft.card.thumbnail"),
                ],
            ),
            ActivityLike(name="empty", attachments=[]),
        ]

        selected = (
            Select(activities)
            .where(contains(content_type="application/vnd.microsoft.card.hero"))
            .get()
        )

        assert [cast(ActivityLike, activity).name for activity in selected] == ["hero"]

    def test_expect_that_accepts_contains_as_root_callable(self):
        """contains() works as a root callable for Expect.that()."""
        activities = [
            ActivityLike(
                name="hero",
                attachments=[
                    Attachment(content_type="application/vnd.microsoft.card.hero"),
                ],
            )
        ]

        Expect(activities).that(contains(is_hero_card))

    def test_expect_that_accepts_contains_as_property_callable(self):
        """contains() works as a property callable for Expect.that()."""
        activities = [
            ActivityLike(
                name="hero",
                attachments=[
                    Attachment(content_type="application/vnd.microsoft.card.hero"),
                ],
            )
        ]

        Expect(activities).that(attachments=contains(is_hero_card))

    def test_expect_that_accepts_contains_with_kwargs(self):
        """contains() supports Expect.that() with keyword criteria."""
        activities = [
            ActivityLike(
                name="hero",
                attachments=[
                    Attachment(content_type="application/vnd.microsoft.card.hero"),
                ],
            )
        ]

        Expect(activities).that(
            contains(content_type="application/vnd.microsoft.card.hero")
        )

    def test_expect_that_fails_when_nested_property_not_found(self):
        """Expect.that() fails when contains() does not find a matching value."""
        activities = [
            ActivityLike(
                name="thumbnail",
                attachments=[
                    Attachment(content_type="application/vnd.microsoft.card.thumbnail"),
                ],
            )
        ]

        with pytest.raises(AssertionError):
            Expect(activities).that(contains(is_hero_card))
