class CosmosDBPartitionsFilter:

    def __init__(self, )

class CosmosDBPartitions:

    def __init__(self, partition_keys: list[str], item: JSON):
        self._partition_keys = partition_keys
        self.item = item

    def validate(self, disallowed_keys: list[str] = None) -> None:
        if not self._partition_keys or len(self._partition_keys) == 0:
            raise ValueError("CosmosDBPartitions: At least one partition key is required.")
        if len(self._partition_keys) > 3:
            raise ValueError("CosmosDBPartitions: A maximum of three partition keys are allowed.")
        if disallowed_keys:
            for pk in self._partition_keys:
                if pk in disallowed_keys:
                    raise ValueError(f"CosmosDBPartitions: Partition key '{pk}' is disallowed.")

DEFAULT_PARTITIONS: list[CosmosDBPartition] = CosmosDBPartitions("/key")