from typing import Annotated
from pydantic import StringConstraints


NonEmptyString = Annotated[str, StringConstraints(min_length=1)]
