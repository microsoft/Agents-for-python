# import pytest
# from typing import Optional
# from .agent_scenario.agent_client import AgentClient


# class AgentTestPlugin:
#     """Pytest plugin to capture agent conversation context for reporting."""
    
#     def __init__(self):
#         self.current_client: Optional[AgentClient] = None
#         self.conversations: dict[str, list] = {}  # test_id -> activities
    
#     @pytest.hookimpl(tryfirst=True)
#     def pytest_runtest_setup(self, item: pytest.Item):
#         """Called before each test runs."""
#         self.current_client = None
    
#     @pytest.hookimpl(trylast=True)
#     def pytest_runtest_teardown(self, item: pytest.Item):
#         """Called after each test runs - capture conversation."""
#         if self.current_client:
#             test_id = item.nodeid
#             self.conversations[test_id] = self.current_client.get_activities()
    
#     @pytest.hookimpl(hookwrapper=True)
#     def pytest_runtest_makereport(self, item: pytest.Item, call):
#         """Modify test report to include conversation transcript."""
#         outcome = yield
#         report = outcome.get_result()
        
#         if report.when == "call" and report.failed:
#             test_id = item.nodeid
#             if test_id in self.conversations:
#                 # Add conversation to the failure message
#                 transcript = self._format_transcript(self.conversations[test_id])
#                 report.longrepr = f"{report.longrepr}\n\nConversation Transcript:\n{transcript}"
    
#     def _format_transcript(self, activities: list) -> str:
#         lines = []
#         for act in activities:
#             sender = "Agent" if act.from_property and act.from_property.role == "bot" else "User"
#             lines.append(f"  [{sender}] {act.text or act.type}")
#         return "\n".join(lines)


# def pytest_configure(config):
#     """Register the plugin."""
#     config.pluginmanager.register(AgentTestPlugin(), "agent_test_plugin")