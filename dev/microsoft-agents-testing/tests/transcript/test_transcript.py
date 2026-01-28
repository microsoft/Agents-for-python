"""
Unit tests for the Transcript class.

This module tests:
- Transcript initialization
- record() method
- get_all() method
- get_new() method with cursor
- child() transcript propagation
"""

from microsoft_agents.testing.transcript import Transcript, ExchangeNode, Exchange
from microsoft_agents.activity import Activity, ActivityTypes


# =============================================================================
# Helper Functions
# =============================================================================

def create_test_exchange(text: str = "test") -> Exchange:
    """Create a test Exchange with a simple message response."""
    activity = Activity(type=ActivityTypes.message, text=text)
    return Exchange(responses=[activity])


def create_request_exchange(request_text: str, response_text: str) -> Exchange:
    """Create a test Exchange with request and response."""
    request = Activity(type=ActivityTypes.message, text=request_text)
    response = Activity(type=ActivityTypes.message, text=response_text)
    return Exchange(request=request, responses=[response])


# =============================================================================
# Transcript Initialization Tests
# =============================================================================

class TestTranscriptInit:
    """Test Transcript initialization."""
    
    def test_init_creates_empty_transcript(self):
        transcript = Transcript()
        assert transcript.get_all() == []
    
    def test_init_with_no_parent(self):
        transcript = Transcript()
        assert transcript._parent is None
    
    def test_init_cursor_at_zero(self):
        transcript = Transcript()
        assert transcript._cursor == 0


# =============================================================================
# Record Method Tests
# =============================================================================

class TestTranscriptRecord:
    """Test the record() method."""
    
    def test_record_single_exchange(self):
        transcript = Transcript()
        exchange = create_test_exchange("hello")
        
        transcript.record(exchange)
        
        assert len(transcript.get_all()) == 1
        assert transcript.get_all()[0] is exchange
    
    def test_record_multiple_exchanges(self):
        transcript = Transcript()
        exchange1 = create_test_exchange("first")
        exchange2 = create_test_exchange("second")
        exchange3 = create_test_exchange("third")
        
        transcript.record(exchange1)
        transcript.record(exchange2)
        transcript.record(exchange3)
        
        all_exchanges = transcript.get_all()
        assert len(all_exchanges) == 3
        assert all_exchanges[0] is exchange1
        assert all_exchanges[1] is exchange2
        assert all_exchanges[2] is exchange3
    
    def test_record_preserves_order(self):
        transcript = Transcript()
        
        for i in range(5):
            transcript.record(create_test_exchange(f"message_{i}"))
        
        all_exchanges = transcript.get_all()
        assert len(all_exchanges) == 5
        for i, exchange in enumerate(all_exchanges):
            assert exchange.responses[0].text == f"message_{i}"


# =============================================================================
# Get All Method Tests
# =============================================================================

class TestTranscriptGetAll:
    """Test the get_all() method."""
    
    def test_get_all_empty(self):
        transcript = Transcript()
        assert transcript.get_all() == []
    
    def test_get_all_returns_all_exchanges(self):
        transcript = Transcript()
        transcript.record(create_test_exchange("a"))
        transcript.record(create_test_exchange("b"))
        
        result = transcript.get_all()
        assert len(result) == 2
    
    def test_get_all_does_not_advance_cursor(self):
        transcript = Transcript()
        transcript.record(create_test_exchange("a"))
        
        transcript.get_all()
        transcript.get_all()
        
        # get_new should still return the exchange since cursor wasn't advanced
        new = transcript.get_new()
        assert len(new) == 1


# =============================================================================
# Get New Method Tests
# =============================================================================

class TestTranscriptGetNew:
    """Test the get_new() method with cursor."""
    
    def test_get_new_returns_all_on_first_call(self):
        transcript = Transcript()
        transcript.record(create_test_exchange("a"))
        transcript.record(create_test_exchange("b"))
        
        new = transcript.get_new()
        assert len(new) == 2
    
    def test_get_new_advances_cursor(self):
        transcript = Transcript()
        transcript.record(create_test_exchange("a"))
        
        first_call = transcript.get_new()
        assert len(first_call) == 1
        
        # Second call should return empty
        second_call = transcript.get_new()
        assert len(second_call) == 0
    
    def test_get_new_returns_only_new_exchanges(self):
        transcript = Transcript()
        transcript.record(create_test_exchange("a"))
        
        transcript.get_new()  # Advance cursor past "a"
        
        transcript.record(create_test_exchange("b"))
        transcript.record(create_test_exchange("c"))
        
        new = transcript.get_new()
        assert len(new) == 2
        assert new[0].responses[0].text == "b"
        assert new[1].responses[0].text == "c"
    
    def test_get_new_empty_when_no_new_exchanges(self):
        transcript = Transcript()
        transcript.record(create_test_exchange("a"))
        
        transcript.get_new()
        
        assert transcript.get_new() == []
        assert transcript.get_new() == []


# =============================================================================
# Child Transcript Tests
# =============================================================================

class TestTranscriptChild:
    """Test the child() method and parent propagation."""
    
    def test_child_creates_new_transcript(self):
        parent = Transcript()
        child = parent.child()
        
        assert child is not parent
        assert isinstance(child, Transcript)
    
    def test_child_has_parent_reference(self):
        parent = Transcript()
        child = parent.child()
        
        assert child._parent is parent
    
    def test_child_record_propagates_to_parent(self):
        parent = Transcript()
        child = parent.child()
        
        exchange = create_test_exchange("from_child")
        child.record(exchange)
        
        # Both should have the exchange
        assert len(child.get_all()) == 1
        assert len(parent.get_all()) == 1
        assert parent.get_all()[0] is exchange
    
    def test_parent_record_does_not_propagate_to_child(self):
        parent = Transcript()
        child = parent.child()
        
        exchange = create_test_exchange("from_parent")
        parent.record(exchange)
        
        # Only parent should have it
        assert len(parent.get_all()) == 1
        assert len(child.get_all()) == 0
    
    def test_nested_children_propagate_to_root(self):
        root = Transcript()
        level1 = root.child()
        level2 = level1.child()
        
        exchange = create_test_exchange("deep")
        level2.record(exchange)
        
        # All ancestors should have the exchange
        assert len(level2.get_all()) == 1
        assert len(level1.get_all()) == 1
        assert len(root.get_all()) == 1
    
    def test_child_has_independent_cursor(self):
        parent = Transcript()
        child = parent.child()
        
        child.record(create_test_exchange("a"))
        
        # Advance parent cursor
        parent.get_new()
        
        # Child cursor should still be at 0
        child_new = child.get_new()
        assert len(child_new) == 1


# =============================================================================
# ExchangeNode Tests
# =============================================================================

class TestExchangeNode:
    """Test the ExchangeNode class."""
    
    def test_node_has_exchange_and_source(self):
        transcript = Transcript()
        exchange = create_test_exchange("test")
        
        transcript.record(exchange)
        
        # Access internal nodes
        assert len(transcript._nodes) == 1
        node = transcript._nodes[0]
        assert node.exchange is exchange
        assert node.source is transcript
# =============================================================================
# Additional Edge Case Tests
# =============================================================================

class TestTranscriptEdgeCases:
    """Test edge cases and additional scenarios."""
    
    def test_sibling_children_have_independent_nodes(self):
        """Two children of the same parent should have independent node lists."""
        parent = Transcript()
        child1 = parent.child()
        child2 = parent.child()
        
        exchange1 = create_test_exchange("from_child1")
        exchange2 = create_test_exchange("from_child2")
        
        child1.record(exchange1)
        child2.record(exchange2)
        
        # Parent has both
        assert len(parent.get_all()) == 2
        # Each child only has its own
        assert len(child1.get_all()) == 1
        assert child1.get_all()[0] is exchange1
        assert len(child2.get_all()) == 1
        assert child2.get_all()[0] is exchange2
    
    def test_get_new_after_multiple_records(self):
        """Test cursor behavior with interleaved record and get_new calls."""
        transcript = Transcript()
        
        transcript.record(create_test_exchange("a"))
        assert len(transcript.get_new()) == 1
        
        transcript.record(create_test_exchange("b"))
        transcript.record(create_test_exchange("c"))
        assert len(transcript.get_new()) == 2
        
        assert len(transcript.get_new()) == 0
        
        transcript.record(create_test_exchange("d"))
        new = transcript.get_new()
        assert len(new) == 1
        assert new[0].responses[0].text == "d"
    
    def test_get_all_returns_copy_of_exchanges(self):
        """Verify get_all returns exchange objects, not the internal list."""
        transcript = Transcript()
        exchange = create_test_exchange("test")
        transcript.record(exchange)
        
        all1 = transcript.get_all()
        all2 = transcript.get_all()
        
        # Should be different list instances
        assert all1 is not all2
        # But contain the same exchange
        assert all1[0] is all2[0]
    
    def test_child_node_tracks_correct_source(self):
        """Verify ExchangeNode.source correctly identifies originating transcript."""
        parent = Transcript()
        child = parent.child()
        
        exchange = create_test_exchange("test")
        child.record(exchange)
        
        # Both have the node, but source should point to child
        parent_node = parent._nodes[0]
        child_node = child._nodes[0]
        
        assert parent_node.source is child
        assert child_node.source is child
    
    def test_empty_transcript_get_new(self):
        """Test get_new on empty transcript."""
        transcript = Transcript()
        assert transcript.get_new() == []
        assert transcript._cursor == 0


class TestExchangeNodeDataclass:
    """Test ExchangeNode dataclass behavior."""
    
    def test_node_equality(self):
        """ExchangeNodes with same exchange and source should be equal."""
        transcript = Transcript()
        exchange = create_test_exchange("test")
        
        node1 = ExchangeNode(exchange=exchange, source=transcript)
        node2 = ExchangeNode(exchange=exchange, source=transcript)
        
        assert node1 == node2
    
    def test_node_inequality_different_exchange(self):
        """ExchangeNodes with different exchanges should not be equal."""
        transcript = Transcript()
        exchange1 = create_test_exchange("test1")
        exchange2 = create_test_exchange("test2")
        
        node1 = ExchangeNode(exchange=exchange1, source=transcript)
        node2 = ExchangeNode(exchange=exchange2, source=transcript)
        
        assert node1 != node2
    
    def test_node_inequality_different_source(self):
        """ExchangeNodes with different sources should not be equal."""
        transcript1 = Transcript()
        transcript2 = Transcript()
        exchange = create_test_exchange("test")
        
        node1 = ExchangeNode(exchange=exchange, source=transcript1)
        node2 = ExchangeNode(exchange=exchange, source=transcript2)
        
        assert node1 != node2