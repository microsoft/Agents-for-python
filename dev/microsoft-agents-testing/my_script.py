#!/usr/bin/env python
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
Demo script showcasing TranscriptLogger implementations.

This script sets up real agents using the testing framework,
interacts with them, and demonstrates the different TranscriptLogger
implementations with various detail levels.

Run with: python my_script.py
"""

import asyncio

from microsoft_agents.activity import Activity, ActivityTypes
from microsoft_agents.hosting.core import TurnContext, TurnState

from microsoft_agents.testing.aiohttp_scenario import AiohttpScenario, AgentEnvironment
from microsoft_agents.testing.transcript_logger import (
    ActivityLogger,
    ConversationLogger,
    DetailLevel,
    TimeFormat,
    print_conversation,
    print_activities,
    DEFAULT_ACTIVITY_FIELDS,
    EXTENDED_ACTIVITY_FIELDS,
)


# ============================================================================
# Agent Definitions - Real agents with different behaviors
# ============================================================================


async def init_echo_agent(env: AgentEnvironment) -> None:
    """A simple echo agent that repeats back what you say."""
    @env.agent_application.activity("message")
    async def on_message(context: TurnContext, state: TurnState):
        user_text = context.activity.text or "(no text)"
        await context.send_activity(f"Echo: {user_text}")


async def init_helpful_agent(env: AgentEnvironment) -> None:
    """A more conversational agent with multiple response types."""
    @env.agent_application.activity("message")
    async def on_message(context: TurnContext, state: TurnState):
        text = (context.activity.text or "").lower().strip()
        
        if text.startswith("hello"):
            name = text[5:].strip() or "there"
            await context.send_activity(f"Hello, {name}!")
            await context.send_activity("How can I help you today?")
        
        elif "help" in text:
            await context.send_activity("I can help you with:")
            await context.send_activity("- Answering questions")
            await context.send_activity("- Providing information")
            await context.send_activity("- Just chatting!")
        
        elif "bye" in text or "goodbye" in text:
            await context.send_activity("Goodbye! Have a great day!")
        
        else:
            await context.send_activity(f"You said: {context.activity.text}")
            await context.send_activity("Type 'help' to see what I can do!")


async def init_multi_type_agent(env: AgentEnvironment) -> None:
    """An agent that responds with different activity types."""
    @env.agent_application.activity("message")
    async def on_message(context: TurnContext, state: TurnState):
        text = (context.activity.text or "").lower()
        
        # Always send a typing indicator first (non-message activity)
        await context.send_activity(Activity(type=ActivityTypes.typing))
        
        if "card" in text:
            # Send a simple card-like message
            await context.send_activity(
                Activity(
                    type=ActivityTypes.message,
                    text="Here's some information:",
                    attachments=[],  # Would have card attachments in real scenario
                )
            )
        else:
            await context.send_activity(f"Got your message: {context.activity.text}")


# ============================================================================
# Demo Functions
# ============================================================================


async def demo_echo_agent():
    """Demo the echo agent with ConversationLogger."""
    print("\n" + "=" * 60)
    print("DEMO 1: Echo Agent with ConversationLogger")
    print("=" * 60)
    
    scenario = AiohttpScenario(
        init_agent=init_echo_agent,
        use_jwt_middleware=False,
    )
    
    async with scenario.client() as client:
        # Have a simple conversation
        await client.send("Hello, Agent!", wait=0.2)
        await client.send("How are you?", wait=0.2)
        await client.send("Tell me a joke", wait=0.2)
        
        transcript = client.transcript
        
        # Show with different detail levels
        print("\n--- MINIMAL detail ---")
        logger = ConversationLogger(detail=DetailLevel.MINIMAL)
        logger.print(transcript)
        
        print("\n--- STANDARD detail (default) ---")
        logger = ConversationLogger(detail=DetailLevel.STANDARD)
        logger.print(transcript)
        
        print("\n--- DETAILED (with latency) ---")
        logger = ConversationLogger(detail=DetailLevel.DETAILED)
        logger.print(transcript)
        
        print("\n--- FULL (with timeline) ---")
        logger = ConversationLogger(detail=DetailLevel.FULL)
        logger.print(transcript)


async def demo_helpful_agent():
    """Demo the helpful agent with ConversationLogger custom labels."""
    print("\n" + "=" * 60)
    print("DEMO 2: Helpful Agent with Multi-Response")
    print("=" * 60)
    
    scenario = AiohttpScenario(
        init_agent=init_helpful_agent,
        use_jwt_middleware=False,
    )
    
    async with scenario.client() as client:
        await client.send("Hello Alice", wait=0.2)
        await client.send("I need help", wait=0.2)
        await client.send("goodbye", wait=0.2)
        
        transcript = client.transcript
        
        print("\n--- Custom labels (User/Bot) ---")
        logger = ConversationLogger(
            user_label="User",
            agent_label="Bot",
            detail=DetailLevel.STANDARD,
        )
        logger.print(transcript)
        
        print("\n--- With timing info ---")
        logger = ConversationLogger(
            user_label="[User]",
            agent_label="[Bot]",
            detail=DetailLevel.DETAILED,
        )
        logger.print(transcript)


async def demo_activity_logger():
    """Demo the ActivityLogger with selectable fields."""
    print("\n" + "=" * 60)
    print("DEMO 3: ActivityLogger with Selectable Fields")
    print("=" * 60)
    
    scenario = AiohttpScenario(
        init_agent=init_echo_agent,
        use_jwt_middleware=False,
    )
    
    async with scenario.client() as client:
        await client.send("Test message 1", wait=0.2)
        await client.send("Test message 2", wait=0.2)
        
        transcript = client.transcript
        
        print("\n--- Default fields ---")
        print(f"Fields: {DEFAULT_ACTIVITY_FIELDS}")
        logger = ActivityLogger()
        logger.print(transcript)
        
        print("\n--- Minimal fields (just type and text) ---")
        logger = ActivityLogger(fields=["type", "text"])
        logger.print(transcript)
        
        print("\n--- Extended fields with timing ---")
        print(f"Fields: {EXTENDED_ACTIVITY_FIELDS}")
        logger = ActivityLogger(
            fields=EXTENDED_ACTIVITY_FIELDS,
            detail=DetailLevel.DETAILED,
        )
        logger.print(transcript)


async def demo_multi_type_agent():
    """Demo agent with multiple activity types."""
    print("\n" + "=" * 60)
    print("DEMO 4: Agent with Multiple Activity Types")
    print("=" * 60)
    
    scenario = AiohttpScenario(
        init_agent=init_multi_type_agent,
        use_jwt_middleware=False,
    )
    
    async with scenario.client() as client:
        await client.send("Hello there", wait=0.2)
        await client.send("Show me a card", wait=0.2)
        
        transcript = client.transcript
        
        print("\n--- ConversationLogger (messages only) ---")
        logger = ConversationLogger(show_other_types=False)
        logger.print(transcript)
        
        print("\n--- ConversationLogger (showing other types) ---")
        logger = ConversationLogger(show_other_types=True)
        logger.print(transcript)
        
        print("\n--- ActivityLogger (shows everything) ---")
        logger = ActivityLogger(detail=DetailLevel.DETAILED)
        logger.print(transcript)


async def demo_convenience_functions():
    """Demo the convenience functions."""
    print("\n" + "=" * 60)
    print("DEMO 5: Convenience Functions")
    print("=" * 60)
    
    scenario = AiohttpScenario(
        init_agent=init_echo_agent,
        use_jwt_middleware=False,
    )
    
    async with scenario.client() as client:
        await client.send("Quick test", wait=0.2)
        
        transcript = client.transcript
        
        print("\n--- print_conversation() ---")
        print_conversation(transcript)
        
        print("\n--- print_conversation() with detail ---")
        print_conversation(transcript, detail=DetailLevel.DETAILED)
        
        print("\n--- print_activities() ---")
        print_activities(transcript)
        
        print("\n--- print_activities() with custom fields ---")
        print_activities(transcript, fields=["type", "text", "id"])


async def demo_two_agents():
    """Demo interacting with two different agents."""
    print("\n" + "=" * 60)
    print("DEMO 6: Two Different Agents Side by Side")
    print("=" * 60)
    
    echo_scenario = AiohttpScenario(
        init_agent=init_echo_agent,
        use_jwt_middleware=False,
    )
    
    helpful_scenario = AiohttpScenario(
        init_agent=init_helpful_agent,
        use_jwt_middleware=False,
    )
    
    # Interact with echo agent
    async with echo_scenario.client() as echo_client:
        await echo_client.send("Hello from user", wait=0.2)
        echo_transcript = echo_client.transcript
    
    # Interact with helpful agent
    async with helpful_scenario.client() as helpful_client:
        await helpful_client.send("Hello from user", wait=0.2)
        helpful_transcript = helpful_client.transcript
    
    print("\n--- Echo Agent Conversation ---")
    ConversationLogger(
        user_label="User",
        agent_label="Echo",
    ).print(echo_transcript)
    
    print("\n--- Helpful Agent Conversation ---")
    ConversationLogger(
        user_label="User", 
        agent_label="Helper",
    ).print(helpful_transcript)


async def demo_time_formats():
    """Demonstrate all TimeFormat options."""
    print("\n" + "-" * 60)
    print("Demo: Time Formats")
    print("-" * 60)
    
    scenario = AiohttpScenario(
        init_agent=init_echo_agent,
        use_jwt_middleware=False,
    )
    
    async with scenario.client() as client:
        await client.send("First message", wait=0.3)
        await client.send("Second message", wait=0.3)
        await client.send("Third message", wait=0.3)
        transcript = client.transcript
    
    print("\n--- TimeFormat.CLOCK (default: HH:MM:SS.mmm) ---")
    ConversationLogger(time_format=TimeFormat.CLOCK, detail=DetailLevel.DETAILED).print(transcript)
    
    print("\n--- TimeFormat.RELATIVE (prefixed with +) ---")
    ConversationLogger(time_format=TimeFormat.RELATIVE, detail=DetailLevel.DETAILED).print(transcript)
    
    print("\n--- TimeFormat.ELAPSED (seconds from start) ---")
    ConversationLogger(time_format=TimeFormat.ELAPSED, detail=DetailLevel.DETAILED).print(transcript)
    
    print("\n--- ActivityLogger with TimeFormat.ELAPSED ---")
    ActivityLogger(
        fields=["type", "text"],
        detail=DetailLevel.DETAILED,
        time_format=TimeFormat.ELAPSED,
    ).print(transcript)


async def main():
    """Run all demos."""
    print("=" * 60)
    print("     TranscriptLogger Demonstration Script                ")
    print("     Testing with Real Agents (No Mocking!)               ")
    print("=" * 60)
    
    await demo_echo_agent()
    await demo_helpful_agent()
    await demo_activity_logger()
    await demo_multi_type_agent()
    await demo_convenience_functions()
    await demo_two_agents()
    await demo_time_formats()
    
    print("\n" + "=" * 60)
    print("All demos completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
