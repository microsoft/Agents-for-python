from microsoft.agents.hosting.core import MessageFactory, TurnContext
from microsoft.agents.hosting.teams import TeamsActivityHandler, TeamsInfo
from microsoft.agents.activity import ChannelAccount, ConversationParameters
from microsoft.agents.activity.teams import MeetingNotification


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
        elif "getMeetingParticipant" in text:
            meeting_participant = await TeamsInfo.get_meeting_participant(turn_context)
            await turn_context.send_activity(
                MessageFactory.text(f"Meeting participant: {meeting_participant}")
            )
        elif "getPagedTeamMembers" in text:
            members = await TeamsInfo.get_paged_team_members(turn_context, None, 2)
            member_emails = [m.email for m in members.members if m.email]
            await turn_context.send_activity(
                MessageFactory.text(f"team members: {member_emails}")
            )
        elif "getTeamMember" in text:
            teams_channel_data = turn_context.activity.channel_data
            team_id = teams_channel_data.get("team", {}).get("id")
            if not team_id:
                await turn_context.send_activity(
                    MessageFactory.text("Team ID not found")
                )
                return

            member = await TeamsInfo.get_team_member(
                turn_context, team_id, turn_context.activity.from_property.id
            )
            await turn_context.send_activity(
                MessageFactory.text(f"team member: {member}")
            )
        elif "sendMessageToTeamsChannel" in text:
            teams_channel_data = turn_context.activity.channel_data
            channel_id = teams_channel_data.get("channel", {}).get("id")
            if not channel_id:
                await turn_context.send_activity(
                    MessageFactory.text("Channel ID not found")
                )
                return

            client_id = (
                turn_context.turn_state[turn_context.adapter.AGENT_IDENTITY_KEY].claims[
                    "aud"
                ],
            )
            sent_result = await TeamsInfo.send_message_to_teams_channel(
                turn_context,
                MessageFactory.text("message from agent to channel"),
                channel_id,
                client_id,
            )
            await turn_context.send_activity(
                MessageFactory.text(f"sent: {sent_result}")
            )
        elif "sendMeetingNotification" in text:
            teams_channel_data: dict = turn_context.activity.channel_data
            meeting_id = teams_channel_data.get("meeting", {}).get("id")
            if not meeting_id:
                await turn_context.send_activity(
                    MessageFactory.text("Meeting ID not found")
                )
                return

            notification = MeetingNotification(
                type="targetedMeetingNotification",
                value={"recipients": ["rido"], "surfaces": []},
            )
            resp = await TeamsInfo.send_meeting_notification(
                turn_context, notification, meeting_id
            )
            await turn_context.send_activity(
                MessageFactory.text(f"sendMeetingNotification: {resp}")
            )
        elif "sendMessageToListOfUsers" in text:
            members = await TeamsInfo.get_paged_members(turn_context, 2)
            users = [{"id": m.id} for m in members.members if m.email]

            tenant_id = turn_context.activity.conversation.tenant_id
            await TeamsInfo.send_message_to_list_of_users(
                turn_context,
                MessageFactory.text("message from agent to list of users"),
                tenant_id,
                users,
            )
            await turn_context.send_activity(
                MessageFactory.text("Messages sent to list of users")
            )
        elif "sendMessageToAllUsersInTenant" in text:
            tenant_id = turn_context.activity.conversation.tenant_id
            batch_resp = await TeamsInfo.send_message_to_all_users_in_tenant(
                turn_context,
                MessageFactory.text("message from agent to all users"),
                tenant_id,
            )
            await turn_context.send_activity(
                MessageFactory.text(f"Operation ID: {batch_resp.operation_id}")
            )
        elif "sendMessageToAllUsersInTeam" in text:
            teams_channel_data = turn_context.activity.channel_data
            team_id = teams_channel_data.get("team", {}).get("id")
            if not team_id:
                await turn_context.send_activity(
                    MessageFactory.text("Team ID not found")
                )
                return

            tenant_id = turn_context.activity.conversation.tenant_id
            batch_resp = await TeamsInfo.send_message_to_all_users_in_team(
                turn_context,
                MessageFactory.text("message from agent to all users in team"),
                tenant_id,
                team_id,
            )
            await turn_context.send_activity(
                MessageFactory.text(f"Operation ID: {batch_resp.operation_id}")
            )
        elif "sendMessageToListOfChannels" in text:
            members = await TeamsInfo.get_paged_members(turn_context, 2)
            users = [{"id": m.id} for m in members.members if m.email]

            tenant_id = turn_context.activity.conversation.tenant_id
            await TeamsInfo.send_message_to_list_of_channels(
                turn_context,
                MessageFactory.text("message from agent to list of channels"),
                tenant_id,
                users,
            )
            await turn_context.send_activity(
                MessageFactory.text("Messages sent to list of channels")
            )
        elif "msg all_members" in text:
            await self.message_all_members(turn_context)
        else:
            await turn_context.send_activities(
                [
                    MessageFactory.text("Welcome to Python Teams handler!"),
                    MessageFactory.text(
                        "Options: getMember, getPagedMembers, getTeamChannels, getTeamDetails, getMeetingInfo, "
                        "getMeetingParticipant, getPagedTeamMembers, getTeamMember, sendMessageToTeamsChannel, "
                        "sendMeetingNotification, sendMessageToListOfUsers, sendMessageToAllUsersInTenant, "
                        "sendMessageToAllUsersInTeam, sendMessageToListOfChannels, msg all_members"
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
                    inner_context.turn_state[
                        turn_context.adapter.AGENT_IDENTITY_KEY
                    ].claims["aud"],
                    ref,
                    continue_callback,
                )

            await turn_context.adapter.create_conversation(
                turn_context.turn_state[turn_context.adapter.AGENT_IDENTITY_KEY].claims[
                    "aud"
                ],
                turn_context.activity.channel_id,
                turn_context.activity.service_url,
                "https://api.botframework.com",
                convo_params,
                conversation_callback,
            )

        await turn_context.send_activity(
            MessageFactory.text("All messages have been sent.")
        )
