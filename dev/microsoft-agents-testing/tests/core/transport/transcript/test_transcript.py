# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Tests for the Transcript class."""

from microsoft_agents.activity import Activity, ActivityTypes
from microsoft_agents.testing.core.transport.transcript import (
    Exchange,
    Transcript,
)


class TestTranscriptInitialization:
    """Tests for Transcript initialization."""

    def test_transcript_default_initialization(self):
        """Transcript should initialize with empty history and no parent."""
        transcript = Transcript()
        
        assert transcript._parent is None
        assert transcript._children == []
        assert transcript._history == []
        assert transcript.history() == []

    def test_transcript_with_parent(self):
        """Transcript should accept a parent transcript."""
        parent = Transcript()
        child = Transcript(parent=parent)
        
        assert child._parent is parent


class TestTranscriptHistory:
    """Tests for Transcript history management."""

    def test_history_returns_copy(self):
        """history() should return a copy of the internal list."""
        transcript = Transcript()
        exchange = Exchange(request=Activity(type=ActivityTypes.message, text="Hello"))
        transcript.record(exchange)
        
        history = transcript.history()
        history.append(Exchange())  # Modify the returned list
        
        # Internal history should not be affected
        assert len(transcript.history()) == 1

    def test_clear_removes_all_history(self):
        """clear() should remove all exchanges from history."""
        transcript = Transcript()
        exchange1 = Exchange(request=Activity(type=ActivityTypes.message, text="Hello"))
        exchange2 = Exchange(request=Activity(type=ActivityTypes.message, text="World"))
        
        transcript.record(exchange1)
        transcript.record(exchange2)
        assert len(transcript.history()) == 2
        
        transcript.clear()
        assert transcript.history() == []


class TestTranscriptRecord:
    """Tests for recording exchanges."""

    def test_record_adds_to_history(self):
        """record() should add an exchange to the transcript."""
        transcript = Transcript()
        exchange = Exchange(request=Activity(type=ActivityTypes.message, text="Hello"))
        
        transcript.record(exchange)
        
        assert len(transcript.history()) == 1
        assert transcript.history()[0] == exchange

    def test_record_multiple_exchanges(self):
        """record() should maintain order of exchanges."""
        transcript = Transcript()
        exchange1 = Exchange(request=Activity(type=ActivityTypes.message, text="First"))
        exchange2 = Exchange(request=Activity(type=ActivityTypes.message, text="Second"))
        exchange3 = Exchange(request=Activity(type=ActivityTypes.message, text="Third"))
        
        transcript.record(exchange1)
        transcript.record(exchange2)
        transcript.record(exchange3)
        
        history = transcript.history()
        assert len(history) == 3
        assert history[0].request.text == "First"
        assert history[1].request.text == "Second"
        assert history[2].request.text == "Third"


class TestTranscriptPropagation:
    """Tests for exchange propagation between transcripts."""

    def test_propagate_up_to_parent(self):
        """Exchanges should propagate up to parent transcript."""
        parent = Transcript()
        child = Transcript(parent=parent)
        
        exchange = Exchange(request=Activity(type=ActivityTypes.message, text="Hello"))
        child.record(exchange)
        
        # Exchange should be in both child and parent
        assert len(child.history()) == 1
        assert len(parent.history()) == 1
        assert parent.history()[0] == exchange

    def test_propagate_up_multiple_levels(self):
        """Exchanges should propagate up through multiple parent levels."""
        grandparent = Transcript()
        parent = Transcript(parent=grandparent)
        child = Transcript(parent=parent)
        
        exchange = Exchange(request=Activity(type=ActivityTypes.message, text="Hello"))
        child.record(exchange)
        
        # Exchange should be in all transcripts
        assert len(child.history()) == 1
        assert len(parent.history()) == 1
        assert len(grandparent.history()) == 1

    def test_propagate_down_to_children(self):
        """Exchanges should propagate down to child transcripts."""
        parent = Transcript()
        child1 = Transcript(parent=parent)
        child2 = Transcript(parent=parent)
        
        # Need to register children with parent
        parent._children.append(child1)
        parent._children.append(child2)
        
        exchange = Exchange(request=Activity(type=ActivityTypes.message, text="Hello"))
        parent.record(exchange)
        
        # Exchange should be in parent and both children
        assert len(parent.history()) == 1
        assert len(child1.history()) == 1
        assert len(child2.history()) == 1

    def test_propagate_down_multiple_levels(self):
        """Exchanges should propagate down through multiple child levels."""
        grandparent = Transcript()
        parent = Transcript()
        child = Transcript()
        
        grandparent._children.append(parent)
        parent._children.append(child)
        
        exchange = Exchange(request=Activity(type=ActivityTypes.message, text="Hello"))
        grandparent.record(exchange)
        
        # Exchange should be in all transcripts
        assert len(grandparent.history()) == 1
        assert len(parent.history()) == 1
        assert len(child.history()) == 1

    def test_child_does_not_propagate_to_siblings(self):
        """Exchanges from one child should not propagate to siblings directly."""
        parent = Transcript()
        child1 = Transcript(parent=parent)
        child2 = Transcript(parent=parent)
        
        # Only add children for downward propagation test
        # child1 and child2 have parent set for upward propagation
        
        exchange = Exchange(request=Activity(type=ActivityTypes.message, text="Hello"))
        child1.record(exchange)
        
        # Exchange should be in child1 and parent only
        assert len(child1.history()) == 1
        assert len(parent.history()) == 1
        # child2 should not have the exchange (not connected via parent._children)
        assert len(child2.history()) == 0


class TestTranscriptGetRoot:
    """Tests for get_root() method."""

    def test_get_root_returns_self_when_no_parent(self):
        """get_root() should return self when there is no parent."""
        transcript = Transcript()
        
        assert transcript.get_root() is transcript

    def test_get_root_returns_parent_when_one_level(self):
        """get_root() should return parent when one level deep."""
        parent = Transcript()
        child = Transcript(parent=parent)
        
        assert child.get_root() is parent

    def test_get_root_returns_grandparent_when_two_levels(self):
        """get_root() should return grandparent when two levels deep."""
        grandparent = Transcript()
        parent = Transcript(parent=grandparent)
        child = Transcript(parent=parent)
        
        assert child.get_root() is grandparent
        assert parent.get_root() is grandparent

    def test_get_root_returns_topmost_ancestor(self):
        """get_root() should return the topmost ancestor."""
        root = Transcript()
        level1 = Transcript(parent=root)
        level2 = Transcript(parent=level1)
        level3 = Transcript(parent=level2)
        level4 = Transcript(parent=level3)
        
        assert level4.get_root() is root
        assert level3.get_root() is root
        assert level2.get_root() is root
        assert level1.get_root() is root


class TestTranscriptChild:
    """Tests for child() method."""

    def test_child_creates_new_transcript(self):
        """child() should create a new Transcript instance."""
        parent = Transcript()
        child = parent.child()
        
        assert isinstance(child, Transcript)
        assert child is not parent

    def test_child_has_correct_parent(self):
        """child() should set the parent reference correctly."""
        parent = Transcript()
        child = parent.child()
        
        assert child._parent is parent

    def test_child_is_independent_initially(self):
        """Child transcript should start with empty history."""
        parent = Transcript()
        parent.record(Exchange(request=Activity(type=ActivityTypes.message, text="Before")))
        
        child = parent.child()
        
        # Child should have empty history initially
        assert child.history() == []

    def test_child_propagates_to_parent(self):
        """Exchanges recorded in child should propagate to parent."""
        parent = Transcript()
        child = parent.child()
        
        exchange = Exchange(request=Activity(type=ActivityTypes.message, text="Hello"))
        child.record(exchange)
        
        assert len(child.history()) == 1
        assert len(parent.history()) == 1

    def test_nested_children(self):
        """Multiple levels of children should work correctly."""
        root = Transcript()
        level1 = root.child()
        level2 = level1.child()
        level3 = level2.child()
        
        exchange = Exchange(request=Activity(type=ActivityTypes.message, text="Deep"))
        level3.record(exchange)
        
        # All ancestors should have the exchange
        assert len(level3.history()) == 1
        assert len(level2.history()) == 1
        assert len(level1.history()) == 1
        assert len(root.history()) == 1


class TestTranscriptIntegration:
    """Integration tests for Transcript operations."""

    def test_complex_hierarchy_propagation(self):
        """Test propagation in a complex hierarchy."""
        #     root
        #    /    \
        #   a      b
        #  / \      \
        # c   d      e
        
        root = Transcript()
        a = Transcript(parent=root)
        b = Transcript(parent=root)
        c = Transcript(parent=a)
        d = Transcript(parent=a)
        e = Transcript(parent=b)
        
        # Record in leaf node 'c'
        exchange = Exchange(request=Activity(type=ActivityTypes.message, text="From C"))
        c.record(exchange)
        
        # Should propagate to c, a, root
        assert len(c.history()) == 1
        assert len(a.history()) == 1
        assert len(root.history()) == 1
        
        # Should NOT propagate to siblings or other branches
        assert len(d.history()) == 0
        assert len(b.history()) == 0
        assert len(e.history()) == 0

    def test_multiple_exchanges_maintain_order(self):
        """Multiple exchanges should maintain order in history."""
        root = Transcript()
        child = Transcript(parent=root)
        
        for i in range(5):
            exchange = Exchange(
                request=Activity(type=ActivityTypes.message, text=f"Message {i}")
            )
            child.record(exchange)
        
        # Both should have same order
        for i, ex in enumerate(child.history()):
            assert ex.request.text == f"Message {i}"
        
        for i, ex in enumerate(root.history()):
            assert ex.request.text == f"Message {i}"

    def test_clear_does_not_affect_parent(self):
        """Clearing child history should not affect parent."""
        root = Transcript()
        child = Transcript(parent=root)
        
        exchange = Exchange(request=Activity(type=ActivityTypes.message, text="Test"))
        child.record(exchange)
        
        child.clear()
        
        assert len(child.history()) == 0
        assert len(root.history()) == 1
