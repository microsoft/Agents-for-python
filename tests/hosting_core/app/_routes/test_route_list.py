from microsoft_agents.hosting.core import (
    TurnContext,
    TurnState,
    _RouteList,
    _Route,
    RouteRank
)

def selector(context: TurnContext) -> bool:
    return True

async def handler(context: TurnContext, state: TurnState) -> None:
    pass

class Test_RouteList:

    def assert_priority_invariant(self, route_list: _RouteList):
        
        # check priority invariant
        routes = list(route_list)
        for i in range(1, len(routes)):
            assert not routes[i] < routes[i - 1]
        
    def has_contents(self, route_list: _RouteList, should_contain: list[_Route]):
        for route in should_contain:
            for existing in list(route_list):
                if existing == route:
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
            (selector, handler, False, RouteRank.DEFAULT, ["a"]),
            (selector, handler, True, RouteRank.LAST, ["a"]),
            (selector, handler, False, RouteRank.FIRST),
            (selector, handler, True),
            (selector, handler),
            (selector, handler, True, RouteRank.DEFAULT, ["slack"]),
            (selector, handler, False, RouteRank.FIRST, ["a", "b"]),
            (selector, handler, True, RouteRank.DEFAULT, ["c"]),
        ]
        all_routes = [
            {
                "selector": route[0],
                "handler": route[1],
                "is_invoke": route[2],
                "rank": route[3],
                "auth_handlers": route[4] if len(route) > 4 else None
            } for route in all_routes
        ]
        added_routes = []

        for i, route in enumerate(all_routes):
            added_routes.append(_Route(**route))
            route_list.add_route(**route)
            self.assert_priority_invariant(route_list)
            assert self.has_contents(route_list, added_routes)