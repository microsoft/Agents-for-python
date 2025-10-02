import pytest

from microsoft_agents.hosting.core import (
    TurnContext,
    RouteSelector,
    RouteHandler,
    Route,
    RouteRank,
    StateT,
    TurnState,
)

from microsoft_agents.hosting.core.app._type_defs import (
    RouteHandler,
    RouteSelector,
    StateT,
)


def selector(context: TurnContext) -> bool:
    return True


async def handler(context: TurnContext, state: TurnState) -> None:
    pass


class TestRoute:

    def test_init(self):

        route = Route(
            selector=selector,
            handler=handler,
            is_invoke=True,
            rank=RouteRank.HIGH,
            auth_handlers=["auth1", "auth2"],
        )

        assert route.selector == self.selector
        assert route.handler == self.handler
        assert route.is_invoke is True
        assert route.rank == RouteRank.HIGH
        assert route.auth_handlers == ["auth1", "auth2"]

    def test_init_defaults(self):

        route = Route(selector=selector, handler=handler)

        assert route.selector == selector
        assert route.handler == handler
        assert route.is_invoke is False
        assert route.rank == RouteRank.DEFAULT
        assert route.auth_handlers == []

    @pytest.fixture(params=[None, [], ["authA1", "authA2"], ["github"]])
    def auth_handlers_a(self, request):
        return request.param

    @pytest.fixture(params=[None, [], ["authB1", "authB2"], ["github"]])
    def auth_handlers_b(self, request):
        return request.param

    @pytest.mark.parametrize(
        "is_invoke_a, rank_a, is_invoke_b, rank_b, expected_result",
        [
            [False, RouteRank.DEFAULT, False, RouteRank.DEFAULT, False],
            [False, RouteRank.DEFAULT, False, RouteRank.LAST, True],
            [False, RouteRank.LAST, False, RouteRank.DEFAULT, False],
            [False, RouteRank.DEFAULT, True, RouteRank.DEFAULT, True],
            [True, RouteRank.DEFAULT, False, RouteRank.DEFAULT, True],
            [True, RouteRank.DEFAULT, True, RouteRank.DEFAULT, False],
            [True, RouteRank.LAST, True, RouteRank.DEFAULT, False],
            [True, RouteRank.DEFAULT, True, RouteRank.LAST, True],
            [False, RouteRank.FIRST, True, RouteRank.DEFAULT, True],
            [True, RouteRank.DEFAULT, False, RouteRank.LAST, True],
            [False, RouteRank.LAST, True, RouteRank.FIRST, False],
            [True, RouteRank.FIRST, False, RouteRank.LAST, True],
            [False, RouteRank.FIRST, False, RouteRank.LAST, True],
            [True, RouteRank.FIRST, True, RouteRank.LAST, True],
        ],
    )
    def test_lt(
        self,
        is_invoke_a,
        rank_a,
        is_invoke_b,
        rank_b,
        expected_result,
        auth_handlers_a,
        auth_handlers_b,
    ):

        route_a = Route(
            selector,
            handler,
            is_invoke=is_invoke_a,
            rank=rank_a,
            auth_handlers=auth_handlers_a,
        )
        route_b = Route(
            selector,
            handler,
            is_invoke=is_invoke_b,
            rank=rank_b,
            auth_handlers=auth_handlers_b,
        )

        assert (route_a < route_b) == expected_result
