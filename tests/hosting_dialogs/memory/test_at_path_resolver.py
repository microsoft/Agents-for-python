# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest

from microsoft_agents.hosting.dialogs.memory.path_resolvers import AtPathResolver

_PREFIX = "turn.recognized.entities."


class TestAtPathResolver:
    def setup_method(self):
        self.resolver = AtPathResolver()

    def test_simple_entity_no_suffix(self):
        """@foo → turn.recognized.entities.foo.first()"""
        assert self.resolver.transform_path("@foo") == f"{_PREFIX}foo.first()"

    def test_entity_with_dot_suffix(self):
        """@foo.bar → turn.recognized.entities.foo.first().bar"""
        assert self.resolver.transform_path("@foo.bar") == f"{_PREFIX}foo.first().bar"

    def test_entity_with_bracket_suffix(self):
        """@foo[0] → turn.recognized.entities.foo.first()[0]"""
        assert self.resolver.transform_path("@foo[0]") == f"{_PREFIX}foo.first()[0]"

    def test_entity_with_dot_and_bracket_suffix(self):
        """@foo.bar[0] — dot comes before bracket, entity name is still just 'foo'"""
        assert (
            self.resolver.transform_path("@foo.bar[0]")
            == f"{_PREFIX}foo.first().bar[0]"
        )

    def test_non_at_path_is_returned_unchanged(self):
        assert self.resolver.transform_path("turn.foo") == "turn.foo"
        assert self.resolver.transform_path("user.name") == "user.name"

    def test_empty_path_raises(self):
        with pytest.raises(TypeError):
            self.resolver.transform_path("")

    def test_at_sign_only_is_returned_unchanged(self):
        """A bare '@' has no subsequent path char so the branch is skipped."""
        assert self.resolver.transform_path("@") == "@"
