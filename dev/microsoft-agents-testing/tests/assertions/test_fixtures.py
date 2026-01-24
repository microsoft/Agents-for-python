from microsoft_agents.testing import (
    Assertions,
    Fixtures
)

def test_actual():

    Assertions.validate(
        {
            "key": 42
        },
        {
            "key": Fixtures.actual == 42
        }
    )