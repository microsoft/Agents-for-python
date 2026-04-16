# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from dataclasses import dataclass

from microsoft_agents.activity import Activity


@dataclass
class BeginSkillDialogOptions:

    activity: Activity

    @staticmethod
    def from_object(obj: object) -> BeginSkillDialogOptions | None:
        if isinstance(obj, dict) and "activity" in obj:
            return BeginSkillDialogOptions(obj["activity"])
        if hasattr(obj, "activity"):
            return BeginSkillDialogOptions(getattr(obj, "activity"))
        return None
