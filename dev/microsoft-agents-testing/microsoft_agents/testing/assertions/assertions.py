from typing import Any

class Assertions:

    @staticmethod
    def expand(data: dict) -> dict:

        if not isinstance(data, dict):
            return data

        new_data = {}

        # flatten
        for key, value in data.items():
            if "." in key:
                index = key.index(".")
                root = key[:index]
                path = key[index + 1 :]

                if root in new_data and path in new_data[root]:
                    raise RuntimeError()
                elif root in new_data and not isinstance(new_data[root], (dict, list)):
                    raise RuntimeError()

                if root not in new_data:
                    new_data[root] = {}

                new_data[root][path] = value

            else:
                root = key
                if root in new_data:
                    raise RuntimeError()

                new_data[root] = value

        # expand
        for key, value in new_data.items():
            new_data[key] = Assertions.expand(value)

        return new_data

    @staticmethod
    def evaluate(actual: Any, baseline: Any) -> bool:
        return actual == baseline
        # if callable(word):
        #     sig = inspect.signature(word)

        #     num_args = len(sig.parameters)

        #     return word()
        # else:
        #     return word