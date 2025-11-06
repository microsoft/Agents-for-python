from microsoft_agents.testing import DataDrivenTester

class TestBasics(DataDrivenTester):
    _input_dir = "./data_driven_tests"

    def test(self):
        self._run_data_driven_test("input_file.json")