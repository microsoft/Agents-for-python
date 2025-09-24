from microsoft_agents.hosting.core import (
    TurnContext,
    TurnState,
    RouteList,
    Route,
    RouteRank
)

def selector(context: TurnContext) -> bool:
    return True

async def handler(context: TurnContext, state: TurnState) -> None:
    pass

class TestRouteList:

    def assert_priority_invariant(self, route_list: RouteList):
        
        # check priority invariant
        routes = route_list.get_routes()
        for i in range(1, len(routes)):
            assert not routes[i] < routes[i - 1]
        
    def has_contents(self, route_list: RouteList, should_contain: list[Route]):
        for route in should_contain:
            for existing in route_list.get_routes():
                if existing == route:
                    break
            else:
                return False
        return True

    def test_route_list_init(self):
        route_list = RouteList()
        assert route_list.get_routes() == []

    def test_route_list_add_and_order(self):

        route_list = RouteList()

        all_routes = [
            (selector, handler, is_invoke=False, rank=RouteRank.DEFAULT, auth_handlers=["a"]),
            (selector, handler, is_invoke=True, rank=RouteRank.LAST, auth_handlers=["a"]),
            (selector, handler, is_invoke=False, rank=RouteRank.FIRST),
            (selector, handler, is_invoke=True),
            (selector, handler),
            (selector, handler, is_invoke=True, rank=RouteRank.DEFAULT, auth_handlers=["slack"]),
            (selector, handler, is_invoke=False, rank=RouteRank.FIRST, auth_handlers=["a", "b"]),
            (selector, handler, is_invoke=True, rank=RouteRank.DEFAULT, auth_handlers=["c"]),
        ]
        added_routes = []

        for i, route in enumerate(all_routes):
            added_routes.append(Route(*route))
            route_list.add_route(*route)
            self.assert_priority_invariant(route_list)
            assert self.has_contents(route_list, added_routes)