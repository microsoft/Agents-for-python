# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from dataclasses import dataclass

from .find_values_options import FindValuesOptions


@dataclass
class FindChoicesOptions(FindValuesOptions):
    """Contains options to control how input is matched against a list of choices
    
    no_value: If `True`, the choices `value` field will NOT be search over. Defaults to `False`.

    no_action: If `True`, the choices `action.title` field will NOT be searched over.
        Defaults to `False`.

    recognize_numbers: Indicates whether the recognizer should check for Numbers using the
    NumberRecognizer's NumberModel.

    recognize_ordinals: Indicates whether the recognizer should check for Ordinal Numbers using
    the NumberRecognizer's OrdinalModel.
    """

    no_value: bool = False
    no_action: bool = False
    recognize_numbers: bool = True
    recognize_ordinals: bool = True