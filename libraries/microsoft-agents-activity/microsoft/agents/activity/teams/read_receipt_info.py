# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from ..agents_model import AgentsModel


class ReadReceiptInfo(AgentsModel):
    """General information about a read receipt.

    :param last_read_message_id: The id of the last read message.
    :type last_read_message_id: str
    """

    last_read_message_id: str = None

    @staticmethod
    def is_message_read(compare_message_id: str, last_read_message_id: str) -> bool:
        """
        Helper method useful for determining if a message has been read.
        This method converts the strings to integers. If the compare_message_id is
        less than or equal to the last_read_message_id, then the message has been read.

        :param compare_message_id: The id of the message to compare.
        :param last_read_message_id: The id of the last message read by the user.
        :return: True if the compare_message_id is less than or equal to the last_read_message_id.
        """
        if not compare_message_id or not last_read_message_id:
            return False

        try:
            compare_message_id_long = int(compare_message_id)
            last_read_message_id_long = int(last_read_message_id)
        except ValueError:
            return False

        return compare_message_id_long <= last_read_message_id_long

    def is_message_read_instance(self, compare_message_id: str) -> bool:
        """
        Helper method useful for determining if a message has been read.
        If the compare_message_id is less than or equal to the last_read_message_id,
        then the message has been read.

        :param compare_message_id: The id of the message to compare.
        :return: True if the compare_message_id is less than or equal to the last_read_message_id.
        """
        return self.is_message_read(compare_message_id, self.last_read_message_id)
