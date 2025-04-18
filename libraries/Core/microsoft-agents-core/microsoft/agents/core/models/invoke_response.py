from .agents_model import AgentsModel


class InvokeResponse(AgentsModel):
    """
    Tuple class containing an HTTP Status Code and a JSON serializable
    object. The HTTP Status code is, in the invoke activity scenario, what will
    be set in the resulting POST. The Body of the resulting POST will be
    JSON serialized content.

    The body content is defined by the producer.  The caller must know what
    the content is and deserialize as needed.
    """

    status: int = None
    body: object = None

    def is_successful_status_code(self) -> bool:
        """
        Gets a value indicating whether the invoke response was successful.
        :return: A value that indicates if the HTTP response was successful. true if status is in
        the Successful range (200-299); otherwise false.
        """
        return 200 <= self.status <= 299
