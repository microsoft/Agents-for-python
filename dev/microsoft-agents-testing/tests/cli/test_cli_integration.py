# # Copyright (c) Microsoft Corporation. All rights reserved.
# # Licensed under the MIT License.

# """
# Integration tests for CLI commands with real agent scenarios.

# These tests verify that CLI commands work correctly by running them
# against real in-process agents using AiohttpScenario. No mocking of
# the agent behavior - we test the full stack.

# Test Approach:
# - Define real agents using AgentApplication handlers
# - Use AiohttpScenario to host agents in-process
# - Use the pytest plugin fixtures for agent testing
# - Verify actual agent interactions occur
# """

# from pathlib import Path

# import pytest
# from click.testing import CliRunner

# from microsoft_agents.activity import Activity, ActivityTypes
# from microsoft_agents.hosting.core import TurnContext, TurnState

# from microsoft_agents.testing.aiohttp_scenario import AiohttpScenario, AgentEnvironment


# # ============================================================================
# # Test Agents - Real agents used for integration testing
# # ============================================================================


# async def init_echo_agent(env: AgentEnvironment) -> None:
#     """Initialize a simple echo agent that echoes back messages."""
#     @env.agent_application.activity("message")
#     async def on_message(context: TurnContext, state: TurnState):
#         await context.send_activity(f"Echo: {context.activity.text}")


# async def init_greeting_agent(env: AgentEnvironment) -> None:
#     """Initialize an agent that greets users by name."""
#     @env.agent_application.activity("message")
#     async def on_message(context: TurnContext, state: TurnState):
#         text = context.activity.text or ""
#         if text.lower().startswith("hello"):
#             name = text[5:].strip() or "friend"
#             await context.send_activity(f"Hello, {name}! Nice to meet you.")
#         else:
#             await context.send_activity("Say 'hello <name>' to get a greeting!")


# async def init_multi_response_agent(env: AgentEnvironment) -> None:
#     """Initialize an agent that sends multiple responses."""
#     @env.agent_application.activity("message")
#     async def on_message(context: TurnContext, state: TurnState):
#         await context.send_activity("Processing your request...")
#         await context.send_activity("Still working on it...")
#         await context.send_activity("Done! Here's your answer.")


# # ============================================================================
# # Reusable Scenarios for pytest plugin tests
# # ============================================================================

# echo_scenario = AiohttpScenario(
#     init_agent=init_echo_agent,
#     use_jwt_middleware=False,
# )

# greeting_scenario = AiohttpScenario(
#     init_agent=init_greeting_agent,
#     use_jwt_middleware=False,
# )

# multi_response_scenario = AiohttpScenario(
#     init_agent=init_multi_response_agent,
#     use_jwt_middleware=False,
# )


# # ============================================================================
# # Integration Tests: Chat Command Behavior with Real Agents
# # ============================================================================


# @pytest.mark.agent_test(echo_scenario)
# class TestChatCommandBehavior:
#     """
#     Integration tests simulating chat command behavior.
    
#     These tests use real agents to verify the chat functionality works
#     correctly - sending messages and receiving responses.
#     """

#     @pytest.mark.asyncio
#     async def test_chat_single_message_exchange(self, agent_client):
#         """Verify single message exchange like chat command does."""
#         await agent_client.send("Hello agent!", wait=0.2)
        
#         # Verify the agent responded
#         agent_client.expect().that_for_any(text="Echo: Hello agent!")

#     @pytest.mark.asyncio
#     async def test_chat_multiple_turns(self, agent_client):
#         """Verify multiple conversation turns like chat command does."""
#         await agent_client.send("First message", wait=0.1)
#         await agent_client.send("Second message", wait=0.1)
#         await agent_client.send("Third message", wait=0.2)
        
#         # All messages should have been echoed
#         agent_client.expect().that_for_any(text="Echo: First message")
#         agent_client.expect().that_for_any(text="Echo: Second message")
#         agent_client.expect().that_for_any(text="Echo: Third message")

#     @pytest.mark.asyncio
#     async def test_chat_preserves_transcript(self, agent_client):
#         """Verify transcript is preserved across conversation turns."""
#         await agent_client.send("Message 1", wait=0.1)
#         await agent_client.send("Message 2", wait=0.1)
#         await agent_client.send("Message 3", wait=0.2)
        
#         # Transcript should have all exchanges
#         transcript = agent_client.transcript
#         assert transcript is not None
        
#         # Should have at least 3 exchanges (one per message)
#         history = transcript.history()
#         assert len(history) >= 3


# @pytest.mark.agent_test(greeting_scenario)
# class TestChatWithGreetingAgent:
#     """Integration tests for chat with a greeting agent."""

#     @pytest.mark.asyncio
#     async def test_greeting_agent_responds_to_hello(self, agent_client):
#         """Greeting agent responds with personalized greeting."""
#         await agent_client.send("hello Alice", wait=0.2)
        
#         agent_client.expect().that_for_any(text="Hello, Alice! Nice to meet you.")

#     @pytest.mark.asyncio
#     async def test_greeting_agent_prompts_for_hello(self, agent_client):
#         """Greeting agent prompts user if they don't say hello."""
#         await agent_client.send("something else", wait=0.2)
        
#         agent_client.expect().that_for_any(text="Say 'hello <name>' to get a greeting!")


# @pytest.mark.agent_test(multi_response_scenario)
# class TestChatWithMultiResponseAgent:
#     """Integration tests for chat with an agent that sends multiple responses."""

#     @pytest.mark.asyncio
#     async def test_receives_all_responses(self, agent_client):
#         """Verify all multiple responses from agent are received."""
#         await agent_client.send("Do something", wait=0.3)
        
#         # All three responses should come through
#         agent_client.expect().that_for_any(text="Processing your request...")
#         agent_client.expect().that_for_any(text="Still working on it...")
#         agent_client.expect().that_for_any(text="Done! Here's your answer.")


# # ============================================================================
# # Integration Tests: Post Command Behavior with Real Agents
# # ============================================================================


# @pytest.mark.agent_test(echo_scenario)
# class TestPostCommandBehavior:
#     """
#     Integration tests simulating post command behavior.
    
#     Tests sending payloads to agents like the post command does.
#     """

#     @pytest.mark.asyncio
#     async def test_post_simple_text_message(self, agent_client):
#         """Verify posting a simple text message works like --message option."""
#         await agent_client.send("Simple message", wait=0.2)
        
#         agent_client.expect().that_for_any(text="Echo: Simple message")

#     @pytest.mark.asyncio
#     async def test_post_activity_object(self, agent_client):
#         """Verify posting a custom Activity works like posting a JSON file."""
#         activity = Activity(
#             type=ActivityTypes.message,
#             text="Custom payload message",
#         )
        
#         await agent_client.send(activity, wait=0.2)
        
#         agent_client.expect().that_for_any(text="Echo: Custom payload message")

#     @pytest.mark.asyncio
#     async def test_post_multiple_payloads(self, agent_client):
#         """Verify multiple posts work in sequence."""
#         await agent_client.send("First payload", wait=0.1)
#         await agent_client.send("Second payload", wait=0.2)
        
#         agent_client.expect().that_for_any(text="Echo: First payload")
#         agent_client.expect().that_for_any(text="Echo: Second payload")


# # ============================================================================
# # Integration Tests: Agent Environment Access
# # ============================================================================


# @pytest.mark.agent_test(echo_scenario)
# class TestAgentEnvironmentAccess:
#     """Tests verifying we can access the running agent environment."""

#     def test_agent_environment_provides_agent_application(self, agent_environment):
#         """Verify agent_environment provides access to AgentApplication."""
#         app = agent_environment.agent_application
#         assert app is not None

#     def test_agent_environment_provides_storage(self, agent_environment):
#         """Verify agent_environment provides access to storage."""
#         storage = agent_environment.storage
#         assert storage is not None

#     def test_agent_environment_provides_adapter(self, agent_environment):
#         """Verify agent_environment provides access to adapter."""
#         adapter = agent_environment.adapter
#         assert adapter is not None


# # ============================================================================
# # Integration Tests: Validate Command with CLI Runner
# # ============================================================================


# class TestValidateCommandIntegration:
#     """Integration tests for validate command using CliRunner."""

#     def test_validate_with_complete_config(self, tmp_path: Path):
#         """Validate command succeeds with complete configuration."""
#         from microsoft_agents.testing.cli.main import cli
        
#         runner = CliRunner()
        
#         # Create a complete env file
#         env_file = tmp_path / ".env"
#         env_file.write_text("""
# AGENT_URL=http://localhost:3978/api/messages
# SERVICE_URL=http://localhost:3979
# CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID=test-client-id
# CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTSECRET=test-secret
# CONNECTIONS__SERVICE_CONNECTION__SETTINGS__TENANTID=test-tenant
# """)
        
#         result = runner.invoke(cli, ["--env", str(env_file), "validate"])
        
#         assert result.exit_code == 0
#         assert "Configuration Validation" in result.output
#         assert "All configuration checks passed" in result.output

#     def test_validate_shows_missing_values(self, tmp_path: Path):
#         """Validate command shows warnings for missing config values."""
#         from microsoft_agents.testing.cli.main import cli
        
#         runner = CliRunner()
        
#         # Create a partial env file
#         env_file = tmp_path / ".env"
#         env_file.write_text("AGENT_URL=http://localhost:3978")
        
#         result = runner.invoke(cli, ["--env", str(env_file), "validate"])
        
#         assert result.exit_code == 0
#         assert "Not configured" in result.output

#     def test_validate_masks_credentials(self, tmp_path: Path):
#         """Validate command masks sensitive credentials in output."""
#         from microsoft_agents.testing.cli.main import cli
        
#         runner = CliRunner()
        
#         env_file = tmp_path / ".env"
#         env_file.write_text("""
# CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID=abcdefghijklmnop
# CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTSECRET=super-secret-password
# """)
        
#         result = runner.invoke(cli, ["--env", str(env_file), "validate"])
        
#         # App ID should be partially masked
#         assert "abcdefgh..." in result.output
#         # Full values should NOT appear
#         assert "abcdefghijklmnop" not in result.output
#         assert "super-secret-password" not in result.output
#         # Secret should show as masked
#         assert "********" in result.output


# # ============================================================================
# # Integration Tests: Post Command Help
# # ============================================================================


# class TestPostCommandHelp:
#     """Tests for post command help and argument validation."""

#     def test_post_shows_usage_help(self):
#         """Post command displays usage information."""
#         from microsoft_agents.testing.cli.main import cli
        
#         runner = CliRunner()
#         result = runner.invoke(cli, ["post", "--help"])
        
#         assert result.exit_code == 0
#         assert "Send a payload to an agent" in result.output
#         assert "--message" in result.output
#         assert "--url" in result.output

#     def test_post_requires_payload_or_message(self, tmp_path: Path):
#         """Post command requires either payload file or --message."""
#         from microsoft_agents.testing.cli.main import cli
        
#         runner = CliRunner()
        
#         with runner.isolated_filesystem(temp_dir=tmp_path):
#             Path(".env").write_text("AGENT_URL=http://localhost:3978")
#             result = runner.invoke(cli, ["post"])
        
#         # Should error about missing payload
#         assert "No payload specified" in result.output or result.exit_code != 0


# # ============================================================================
# # Integration Tests: Run Command
# # ============================================================================


# class TestRunCommandIntegration:
#     """Tests for run command scenario validation."""

#     def test_run_shows_help(self):
#         """Run command displays help information."""
#         from microsoft_agents.testing.cli.main import cli
        
#         runner = CliRunner()
#         result = runner.invoke(cli, ["run", "--help"])
        
#         assert result.exit_code == 0
#         assert "--scenario" in result.output

#     def test_run_rejects_invalid_scenario(self, tmp_path: Path):
#         """Run command rejects invalid scenario names."""
#         from microsoft_agents.testing.cli.main import cli
        
#         runner = CliRunner()
        
#         with runner.isolated_filesystem(temp_dir=tmp_path):
#             Path(".env").write_text("AGENT_URL=http://localhost:3978")
#             result = runner.invoke(cli, ["run", "--scenario", "nonexistent"])
        
#         # Should abort with error about invalid scenario
#         assert result.exit_code != 0 or "Invalid" in result.output or "Aborted" in result.output


# # ============================================================================
# # Integration Tests: Chat Command Help
# # ============================================================================


# class TestChatCommandHelp:
#     """Tests for chat command help."""

#     def test_chat_shows_help(self):
#         """Chat command displays help information."""
#         from microsoft_agents.testing.cli.main import cli
        
#         runner = CliRunner()
#         result = runner.invoke(cli, ["chat", "--help"])
        
#         assert result.exit_code == 0
#         assert "--url" in result.output
