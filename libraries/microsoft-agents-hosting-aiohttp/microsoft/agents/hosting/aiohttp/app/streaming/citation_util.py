# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import re
from typing import List, Optional

from microsoft.agents.activity import ClientCitation


class CitationUtil:
    """Utility functions for manipulating text and citations."""

    @staticmethod
    def snippet(text: str, max_length: int) -> str:
        """
        Clips the text to a maximum length in case it exceeds the limit.

        Args:
            text: The text to clip.
            max_length: The maximum length of the text to return, cutting off the last whole word.

        Returns:
            The modified text
        """
        if len(text) <= max_length:
            return text

        snippet = text[:max_length]
        snippet = snippet[: min(len(snippet), snippet.rfind(" "))]
        snippet += "..."
        return snippet

    @staticmethod
    def format_citations_response(text: str) -> str:
        """
        Convert citation tags `[doc(s)n]` to `[n]` where n is a number.

        Args:
            text: The text to format.

        Returns:
            The formatted text.
        """
        return re.sub(r"\[docs?(\d+)\]", r"[\1]", text, flags=re.IGNORECASE)

    @staticmethod
    def get_used_citations(
        text: str, citations: List[ClientCitation]
    ) -> Optional[List[ClientCitation]]:
        """
        Get the citations used in the text. This will remove any citations that are
        included in the citations array from the response but not referenced in the text.

        Args:
            text: The text to search for citation references, i.e. [1], [2], etc.
            citations: The list of citations to search for.

        Returns:
            The list of citations used in the text.
        """
        regex = re.compile(r"\[(\d+)\]", re.IGNORECASE)
        matches = regex.findall(text)

        if not matches:
            return None

        # Remove duplicates
        filtered_matches = set(matches)

        # Add citations
        used_citations = []
        for match in filtered_matches:
            citation_ref = f"[{match}]"
            found = next(
                (
                    citation
                    for citation in citations
                    if f"[{citation.position}]" == citation_ref
                ),
                None,
            )
            if found:
                used_citations.append(found)

        return used_citations if used_citations else None
