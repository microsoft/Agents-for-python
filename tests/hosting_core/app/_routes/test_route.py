import pytest

from microsoft_agents.hosting.core import (
    TurnContext,
    _Route,
    RouteRank,
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

        route = _Route(
            selector=selector,
            handler=handler,
            is_invoke=True,
            rank=RouteRank.LAST,
            auth_handlers=["auth1", "auth2"],
        )

        assert route.selector == selector
        assert route.handler == handler
        assert route.is_invoke is True
        assert route.rank == RouteRank.LAST
        assert route.auth_handlers == ["auth1", "auth2"]

    def test_init_defaults(self):

        route = _Route(selector=selector, handler=handler)

        assert route.selector == selector
        assert route.handler == handler
        assert route.is_invoke is False
        assert route.rank == RouteRank.DEFAULT
        assert route.auth_handlers == []

    @pytest.mark.parametrize(
        "rank, is_error",
        [
            [RouteRank.FIRST, False],
            [RouteRank.LAST, False],
            [RouteRank.DEFAULT, False],
            [1, False],
            [-1, True],
            [RouteRank.LAST + 1, True],
        ],
    )
    def test_init_error(self, rank, is_error):
        if is_error:
            with pytest.raises(ValueError):
                _Route(selector=selector, handler=handler, rank=rank)
        else:
            route = _Route(selector=selector, handler=handler, rank=rank)
            assert route.rank == rank

    def test_priority(self):

        route_a = _Route(
            selector=selector,
            handler=handler,
            is_invoke=True,
            rank=RouteRank.FIRST,
            auth_handlers=["auth1"],
        )
        route_b = _Route(
            selector=selector,
            handler=handler,
            is_invoke=False,
            rank=RouteRank.LAST,
            auth_handlers=["auth2"],
            is_agentic=True,
        )
        route_c = _Route(
            selector=selector,
            handler=handler,
            is_invoke=False,
            rank=RouteRank.DEFAULT,
            auth_handlers=["auth2"],
            is_agentic=False,
        )
        route_d = _Route(
            selector=selector,
            handler=handler,
            is_invoke=False,
            rank=23,
            auth_handlers=["auth2"],
            is_agentic=False,
        )

        assert route_a.priority == [0, 1, RouteRank.FIRST]
        assert route_b.priority == [1, 0, RouteRank.LAST]
        assert route_c.priority == [1, 1, RouteRank.DEFAULT]
        assert route_d.priority == [1, 1, 23]

    @pytest.fixture(params=[None, [], ["authA1", "authA2"], ["github"]])
    def auth_handlers_a(self, request):
        return request.param

    @pytest.fixture(params=[None, [], ["authB1", "authB2"], ["github"]])
    def auth_handlers_b(self, request):
        return request.param

    @pytest.mark.parametrize(
        "is_agentic_a, rank_a, is_invoke_a, is_agentic_b, rank_b, is_invoke_b, expected_result",
        [
            # Same agentic status (both False)
            [
                False,
                RouteRank.DEFAULT,
                False,
                False,
                RouteRank.DEFAULT,
                False,
                False,
            ],  # [1,1,DEFAULT] vs [1,1,DEFAULT]
            [
                False,
                RouteRank.DEFAULT,
                False,
                False,
                RouteRank.LAST,
                False,
                True,
            ],  # [1,1,DEFAULT] vs [1,1,LAST]
            [
                False,
                RouteRank.LAST,
                False,
                False,
                RouteRank.DEFAULT,
                False,
                False,
            ],  # [1,1,LAST] vs [1,1,DEFAULT]
            [
                False,
                RouteRank.DEFAULT,
                False,
                True,
                RouteRank.DEFAULT,
                False,
                False,
            ],  # [1,1,DEFAULT] vs [1,0,DEFAULT]
            [
                True,
                RouteRank.DEFAULT,
                False,
                False,
                RouteRank.DEFAULT,
                False,
                True,
            ],  # [1,0,DEFAULT] vs [1,1,DEFAULT]
            [
                True,
                RouteRank.DEFAULT,
                False,
                True,
                RouteRank.DEFAULT,
                False,
                False,
            ],  # [1,0,DEFAULT] vs [1,0,DEFAULT]
            [
                True,
                RouteRank.LAST,
                False,
                True,
                RouteRank.DEFAULT,
                False,
                False,
            ],  # [1,0,LAST] vs [1,0,DEFAULT]
            [
                True,
                RouteRank.DEFAULT,
                False,
                True,
                RouteRank.LAST,
                False,
                True,
            ],  # [1,0,DEFAULT] vs [1,0,LAST]
            [
                False,
                RouteRank.FIRST,
                False,
                True,
                RouteRank.DEFAULT,
                False,
                False,
            ],  # [1,1,FIRST] vs [1,0,DEFAULT]
            [
                True,
                RouteRank.DEFAULT,
                False,
                False,
                RouteRank.LAST,
                False,
                True,
            ],  # [1,0,DEFAULT] vs [1,1,LAST]
            [
                False,
                RouteRank.LAST,
                False,
                True,
                RouteRank.FIRST,
                False,
                False,
            ],  # [1,1,LAST] vs [1,0,FIRST]
            [
                True,
                RouteRank.FIRST,
                False,
                False,
                RouteRank.LAST,
                False,
                True,
            ],  # [1,0,FIRST] vs [1,1,LAST]
            [
                False,
                RouteRank.FIRST,
                False,
                False,
                RouteRank.LAST,
                False,
                True,
            ],  # [1,1,FIRST] vs [1,1,LAST]
            [
                True,
                RouteRank.FIRST,
                False,
                True,
                RouteRank.LAST,
                False,
                True,
            ],  # [1,0,FIRST] vs [1,0,LAST]
            # Same agentic status (both True)
            [
                False,
                RouteRank.DEFAULT,
                True,
                False,
                RouteRank.DEFAULT,
                True,
                False,
            ],  # [0,1,DEFAULT] vs [0,1,DEFAULT]
            [
                False,
                RouteRank.DEFAULT,
                True,
                False,
                RouteRank.LAST,
                True,
                True,
            ],  # [0,1,DEFAULT] vs [0,1,LAST]
            [
                False,
                RouteRank.LAST,
                True,
                False,
                RouteRank.DEFAULT,
                True,
                False,
            ],  # [0,1,LAST] vs [0,1,DEFAULT]
            [
                False,
                RouteRank.DEFAULT,
                True,
                True,
                RouteRank.DEFAULT,
                True,
                False,
            ],  # [0,1,DEFAULT] vs [0,0,DEFAULT]
            [
                True,
                RouteRank.DEFAULT,
                True,
                False,
                RouteRank.DEFAULT,
                True,
                True,
            ],  # [0,0,DEFAULT] vs [0,1,DEFAULT]
            [
                True,
                RouteRank.DEFAULT,
                True,
                True,
                RouteRank.DEFAULT,
                True,
                False,
            ],  # [0,0,DEFAULT] vs [0,0,DEFAULT]
            [
                True,
                RouteRank.LAST,
                True,
                True,
                RouteRank.DEFAULT,
                True,
                False,
            ],  # [0,0,LAST] vs [0,0,DEFAULT]
            [
                True,
                RouteRank.DEFAULT,
                True,
                True,
                RouteRank.LAST,
                True,
                True,
            ],  # [0,0,DEFAULT] vs [0,0,LAST]
            [
                False,
                RouteRank.FIRST,
                True,
                True,
                RouteRank.DEFAULT,
                True,
                False,
            ],  # [0,1,FIRST] vs [0,0,DEFAULT]
            [
                True,
                RouteRank.DEFAULT,
                True,
                False,
                RouteRank.LAST,
                True,
                True,
            ],  # [0,0,DEFAULT] vs [0,1,LAST]
            [
                False,
                RouteRank.LAST,
                True,
                True,
                RouteRank.FIRST,
                True,
                False,
            ],  # [0,1,LAST] vs [0,0,FIRST]
            [
                True,
                RouteRank.FIRST,
                True,
                False,
                RouteRank.LAST,
                True,
                True,
            ],  # [0,0,FIRST] vs [0,1,LAST]
            [
                False,
                RouteRank.FIRST,
                True,
                False,
                RouteRank.LAST,
                True,
                True,
            ],  # [0,1,FIRST] vs [0,1,LAST]
            [
                True,
                RouteRank.FIRST,
                True,
                True,
                RouteRank.LAST,
                True,
                True,
            ],  # [0,0,FIRST] vs [0,0,LAST]
            # Different agentic status - agentic (True) has higher priority than non-agentic (False)
            [
                False,
                RouteRank.DEFAULT,
                True,
                False,
                RouteRank.DEFAULT,
                False,
                True,
            ],  # [0,1,DEFAULT] vs [1,1,DEFAULT]
            [
                False,
                RouteRank.DEFAULT,
                False,
                False,
                RouteRank.DEFAULT,
                True,
                False,
            ],  # [1,1,DEFAULT] vs [0,1,DEFAULT]
            [
                True,
                RouteRank.DEFAULT,
                True,
                True,
                RouteRank.DEFAULT,
                False,
                True,
            ],  # [0,0,DEFAULT] vs [1,0,DEFAULT]
            [
                True,
                RouteRank.DEFAULT,
                False,
                True,
                RouteRank.DEFAULT,
                True,
                False,
            ],  # [1,0,DEFAULT] vs [0,0,DEFAULT]
            [
                False,
                RouteRank.LAST,
                True,
                False,
                RouteRank.FIRST,
                False,
                True,
            ],  # [0,1,LAST] vs [1,1,FIRST]
            [
                False,
                RouteRank.FIRST,
                False,
                False,
                RouteRank.LAST,
                True,
                False,
            ],  # [1,1,FIRST] vs [0,1,LAST]
            [
                True,
                RouteRank.LAST,
                True,
                True,
                RouteRank.FIRST,
                False,
                True,
            ],  # [0,0,LAST] vs [1,0,FIRST]
            [
                True,
                RouteRank.FIRST,
                False,
                True,
                RouteRank.LAST,
                True,
                False,
            ],  # [1,0,FIRST] vs [0,0,LAST]
            [
                False,
                RouteRank.LAST,
                True,
                True,
                RouteRank.FIRST,
                False,
                True,
            ],  # [0,1,LAST] vs [1,0,FIRST]
            [
                True,
                RouteRank.LAST,
                False,
                False,
                RouteRank.FIRST,
                True,
                False,
            ],  # [1,0,LAST] vs [0,1,FIRST]
        ],
    )
    def test_lt_with_agentic(
        self,
        is_invoke_a,
        rank_a,
        is_agentic_a,
        is_invoke_b,
        rank_b,
        is_agentic_b,
        expected_result,
        auth_handlers_a,
        auth_handlers_b,
    ):

        route_a = _Route(
            selector,
            handler,
            is_invoke=is_invoke_a,
            rank=rank_a,
            is_agentic=is_agentic_a,
            auth_handlers=auth_handlers_a,
        )
        route_b = _Route(
            selector,
            handler,
            is_invoke=is_invoke_b,
            rank=rank_b,
            is_agentic=is_agentic_b,
            auth_handlers=auth_handlers_b,
        )

        assert (route_a < route_b) == expected_result
