from .type_defs import FieldAssertionTypes

def check_field(baseline_value: Any, target_value: Any, assertion_type: FieldAssertionType) -> bool:
    return False