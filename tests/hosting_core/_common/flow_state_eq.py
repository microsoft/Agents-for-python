from typing import Optional

from microsoft_agents.hosting.core import FlowState

from tests._common import approx_eq

# 100 ms tolerance
def flow_state_eq(fs1: Optional[FlowState], fs2: Optional[FlowState], tol: float=0.1) -> bool:

    if fs1 is None and fs2 is None:
        return True
    elif fs1 is None or fs2 is None:
        return False

    eq = False

    if approx_eq(fs1.expiration, fs2.expiration, tol=tol):
        old_exp1 = fs1.expiration
        old_exp2 = fs2.expiration

        eq = fs1 == fs2

        fs1.expiration = old_exp1
        fs2.expiration = old_exp2

    return eq