from microsoft_agents.activity import AgentsModel

class ReadReceiptInfo(AgentsModel):

    last_read_message_id: str

    @staticmethod
    def is_message_read(compare_message_id: str, last_read_message_id: str) -> bool:
        try:
            compare_message_id_int = int(compare_message_id)
            last_read_message_id_int = int(last_read_message_id)
        except ValueError:
            return False
        
        return compare_message_id_int <= last_read_message_id_int
    
    def is_message_read(self, compare_message_id: str) -> bool:
        return ReadReceiptInfo.is_message_read(compare_message_id, self.last_read_message_id)