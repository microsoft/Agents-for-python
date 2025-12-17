import pytest

from microsoft_agents.testing import Unset

def test_unset_init_error():
    with pytest.raises(Exception):
        Unset()

def test_unset_ops():
    val = Unset
    assert val is Unset
    assert val == Unset
    assert not val
    assert bool(val) is False
    assert str(val) == "Unset"

def test_unset_set():
    with pytest.raises(AttributeError):
        Unset.value = 1
    with pytest.raises(AttributeError):
        del Unset.value
    with pytest.raises(AttributeError):
        setattr(Unset, 'value', 1)
    with pytest.raises(AttributeError):
        delattr(Unset, "value")
    with pytest.raises(AttributeError):
        Unset["key"] = 1
    with pytest.raises(AttributeError):
        del Unset["key"]

def test_unset_get():
    val = Unset
    assert Unset.get("key", None) is Unset
    assert val.get("key", None) is Unset
    assert getattr(Unset, "key", 42) is Unset
    assert val["key"] is Unset