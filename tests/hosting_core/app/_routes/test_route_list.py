from microsoft_agents.hosting.core import (
    TurnContext,
    TurnState,
    _RouteList,
    _Route,
    RouteRank,
)


def selector(context: TurnContext) -> bool:
    return True


async def handler(context: TurnContext, state: TurnState) -> None:
    pass

def route_eq(route1: _Route, route2: _Route) -> bool:
    return (
        route1.selector == route2.selector
        and route1.handler == route2.handler
        and route1.is_invoke == route2.is_invoke
        and route1.rank == route2.rank
        and route1.auth_handlers == route2.auth_handlers
        and route1.is_agentic == route2.is_agentic
    )

class Test_RouteList:

    def assert_priority_invariant(self, route_list: _RouteList):

        # check priority invariant
        routes = list(route_list)
        for i in range(1, len(routes)):
            assert not routes[i] < routes[i - 1]

    def has_contents(self, route_list: _RouteList, should_contain: list[_Route]):
        for route in should_contain:
            for existing in list(route_list):
                if route_eq(existing, route):
                    break
            else:
                return False
        return True

    def test_route_list_init(self):
        route_list = _RouteList()
        assert list(route_list) == []

    def test_route_list_add_and_order(self):

        route_list = _RouteList()

        all_routes = [
            (selector, handler, False, RouteRank.DEFAULT, ["a"], False),
            (selector, handler, True, RouteRank.LAST, ["a"], False),
            (selector, handler, False, RouteRank.FIRST, [], True),
            (selector, handler, True, RouteRank.DEFAULT, [], True),
            (selector, handler, False, RouteRank.DEFAULT, [], False),
            (selector, handler, True, RouteRank.DEFAULT, ["slack"], True),
            (selector, handler, False, RouteRank.FIRST, ["a", "b"], False),
            (selector, handler, True, RouteRank.DEFAULT, ["c"], True),
        ]
        all_routes = [
            {
                "selector": route[0],
                "handler": route[1],
                "is_invoke": route[2],
                "rank": route[3],
                "auth_handlers": route[4],
                "is_agentic": route[5],
            }
            for route in all_routes
        ]
        added_routes = []

        for i, kwargs in enumerate(all_routes):
            added_routes.append(_Route(**kwargs))
            route_list.add_route(_Route(**kwargs))
            self.assert_priority_invariant(route_list)
            assert self.has_contents(route_list, added_routes)
