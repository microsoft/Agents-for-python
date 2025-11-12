# from typing import Callable, TypeVar

# from .core import Integration

# async def run_data_driven_test(input_file: str) -> None:
#     """
#     Run data-driven tests based on the provided input file.
#     """
#     pass

# T = TypeVar("T", bound=Integration)

# def factory(tests_path: str = "./") -> Callable[T, T]:

#     # for file in file

#     files = []

#     def decorator(test_cls: T) -> T:

#         for file_name in files:

#             test_case_name = f"test_data_driven__{file_name}"

#             def func(self, agent_client, response_client) -> None:
                
                

#             setattr(test_cls, test_case_name, func)

#         return test_cls
    
#     return decorator