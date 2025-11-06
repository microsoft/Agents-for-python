from microsoft_agents.activity import (
    Activity,
)

from microsoft_agents.testing.utils import (
    normalize_activity_data
)

from .check_field import check_field
from .type_defs import _UNSET_FIELD, FieldAssertionTypes

def assert_activity(activity: Activity, baseline: Activity | dict) -> None:
    
    baseline = normalize_activity_data(baseline)

    for key in baseline.keys():

        assertion_type = FieldAssertionTypes.EQUALS
        assertion_info = baseline[key]
        if isinstance(assertion_info, dict) and "assertion_type" in assertion_info:
            assertion_type = assertion_info["assertion_type"]
            baseline_value = assertion_info["value"]
        else:
            baseline_value = assertion_info

        target_value = getattr(activity, key, _UNSET_FIELD)

        assert check_field(
            baseline_value,
            target_value,
            assertion_type
        )