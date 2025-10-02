# import pytest

# from tests._integration.common.testing_environment import (
#     TestingEnvironment,
#     MockTestingEnvironment,
# )
# from tests._integration.scenarios.quickstart import main


# class _TestQuickstart:
#     @pytest.fixture
#     def testenv(self, mocker) -> TestingEnvironment:
#         raise NotImplementedError()

#     # @pytest.fixture
#     # def client(self, testenv) -> TestClient:
#     #     return TestClient(testenv.adapter)

#     @pytest.mark.asyncio
#     async def test_quickstart(self, testenv):
#         main(testenv)
#         # testenv.adapter.send_activity("Hello World")


# # class TestQuickstartMultipleEnvs(_TestQuickstart):

# #     @pytest.fixture(
# #         params=[MockTestingEnvironment, SampleEnvironment],
# #     )
# #     def testenv(self, mocker, request) -> TestingEnvironment:
# #         return request.param(mocker)


# class TestQuickstartMockEnv(_TestQuickstart):
#     @pytest.fixture
#     def testenv(self, mocker) -> TestingEnvironment:
#         return MockTestingEnvironment(mocker)
