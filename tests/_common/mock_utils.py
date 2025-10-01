def mock_instance(mocker, cls, methods={}, default_mock_type=None, **kwargs):
    """Create a mock instance of a class with specified methods mocked."""
    if not default_mock_type:
        default_mock_type = mocker.AsyncMock
    instance = mocker.Mock(spec=cls, **kwargs)
    for method_name, return_value in methods.items():
        if not isinstance(return_value, mocker.Mock) and not isinstance(
            return_value, mocker.AsyncMock
        ):
            return_value = default_mock_type(return_value=return_value)
        setattr(instance, method_name, return_value)
    return instance


def mock_class(mocker, cls, instance):
    """Replace a class with a mock instance."""
    mocker.patch.object(cls, new=instance)
