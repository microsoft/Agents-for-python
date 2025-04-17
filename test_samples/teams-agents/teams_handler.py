from microsoft.agents.builder import MessageFactory, TurnContext
from microsoft.agents.hosting.teams import TeamsActivityHandler, TeamsInfo
from microsoft.agents.core.models import ChannelAccount, ConversationParameters


class TeamsHandler(TeamsActivityHandler):
    async def on_members_added_activity(
        self, members_added: list[ChannelAccount], turn_context: TurnContext
    ):
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity("Hello from Python Teams handler!")

    async def on_message_activity(self, turn_context: TurnContext):
        text = turn_context.activity.text.strip()

        if "getMember" in text:
            member = await TeamsInfo.get_member(
                turn_context, turn_context.activity.from_property.id
            )
            await turn_context.send_activity(
                MessageFactory.text(f"You mentioned me! {member}")
            )
        elif "getPagedMembers" in text:
            members = await TeamsInfo.get_paged_members(turn_context, 2)
            member_emails = [m.email for m in members.members if m.email]
            await turn_context.send_activity(
                MessageFactory.text(f"members: {member_emails}")
            )
        elif "getTeamChannels" in text:
            channels = await TeamsInfo.get_team_channels(turn_context)
            await turn_context.send_activity(
                MessageFactory.text(f"list channels: {channels}")
            )
        elif "getTeamDetails" in text:
            team_details = await TeamsInfo.get_team_details(turn_context)
            await turn_context.send_activity(
                MessageFactory.text(f"Team details: {team_details}")
            )
        elif "getMeetingInfo" in text:
            meeting_info = await TeamsInfo.get_meeting_info(turn_context)
            await turn_context.send_activity(
                MessageFactory.text(f"Meeting Info: {meeting_info}")
            )
        elif "msg all_members" in text:
            await self.message_all_members(turn_context)
        else:
            await turn_context.send_activities(
                [
                    MessageFactory.text("Welcome to Python Teams handler!"),
                    MessageFactory.text(
                        "Options: getMember, getPagedMembers, getTeamChannels, getTeamDetails, getMeetingInfo, msg all_members"
                    ),
                ]
            )

    async def message_all_members(self, turn_context: TurnContext):
        author = await TeamsInfo.get_member(
            turn_context, turn_context.activity.from_property.id
        )
        members_result = await TeamsInfo.get_paged_members(turn_context, 2)

        for member in members_result.members:
            message = MessageFactory.text(
                f"Hello {member.given_name} {member.surname}. I'm a Teams conversation agent from {author.email}"
            )

            convo_params = ConversationParameters(
                members=[{"id": member.id}],
                is_group=False,
                agent=turn_context.activity.recipient,
                tenant_id=turn_context.activity.conversation.tenant_id,
                activity=message,
                channel_data=turn_context.activity.channel_data,
            )

            async def conversation_callback(inner_context: TurnContext):
                ref = inner_context.activity.get_conversation_reference()

                async def continue_callback(ctx: TurnContext):
                    await ctx.send_activity(message)

                await inner_context.adapter.continue_conversation(
                    ref, continue_callback
                )

            await turn_context.adapter.create_conversation(
                turn_context.adapter.auth_config.client_id,
                turn_context.activity.channel_id,
                turn_context.activity.service_url,
                "https://api.botframework.com",
                convo_params,
                conversation_callback,
            )

        await turn_context.send_activity(
            MessageFactory.text("All messages have been sent.")
        )
