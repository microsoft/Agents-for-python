# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
# pylint: disable=pointless-string-statement

from collections import namedtuple

import pytest

from microsoft_agents.hosting.core import (
    ConversationState,
    MemoryStorage,
    TurnContext,
    UserState,
)
from microsoft_agents.hosting.dialogs import (
    Dialog,
    DialogContext,
    DialogContainer,
    DialogInstance,
    DialogSet,
    DialogState,
    ObjectPath,
)
from microsoft_agents.hosting.dialogs.memory.scopes import (
    ClassMemoryScope,
    ConversationMemoryScope,
    DialogContextMemoryScope,
    DialogMemoryScope,
    UserMemoryScope,
    SettingsMemoryScope,
    ThisMemoryScope,
    TurnMemoryScope,
)
from microsoft_agents.activity import (
    Activity,
    ActivityTypes,
    ChannelAccount,
    ConversationAccount,
    Channels,
)
from tests.hosting_dialogs.helpers import DialogTestAdapter


class _TestDialog(Dialog):
    def __init__(self, id: str, message: str):
        super().__init__(id)

        def aux_try_get_value(state):  # pylint: disable=unused-argument
            return "resolved value"

        ExpressionObject = namedtuple("ExpressionObject", "try_get_value")
        self.message = message
        self.expression = ExpressionObject(aux_try_get_value)

    async def begin_dialog(self, dialog_context: DialogContext, options: object = None):
        dialog_context.active_dialog.state["is_dialog"] = True
        await dialog_context.context.send_activity(self.message)
        return Dialog.end_of_turn


class _TestContainer(DialogContainer):
    def __init__(self, id: str, child: Dialog = None):
        super().__init__(id)
        self.child_id = None
        if child:
            self.dialogs.add(child)
            self.child_id = child.id

    async def begin_dialog(self, dialog_context: DialogContext, options: object = None):
        state = dialog_context.active_dialog.state
        state["is_container"] = True
        if self.child_id:
            state["dialog"] = DialogState()
            child_dc = self.create_child_context(dialog_context)
            return await child_dc.begin_dialog(self.child_id, options)

        return Dialog.end_of_turn

    async def continue_dialog(self, dialog_context: DialogContext):
        child_dc = self.create_child_context(dialog_context)
        if child_dc:
            return await child_dc.continue_dialog()

        return Dialog.end_of_turn

    def create_child_context(self, dialog_context: DialogContext):
        state = dialog_context.active_dialog.state
        if state["dialog"] is not None:
            child_dc = DialogContext(
                self.dialogs, dialog_context.context, state["dialog"]
            )
            child_dc.parent = dialog_context
            return child_dc

        return None


_begin_message = Activity(
    text="begin",
    type=ActivityTypes.message,
    channel_id=Channels.test,
    service_url="https://test.com",
    from_property=ChannelAccount(id="user"),
    recipient=ChannelAccount(id="bot"),
    conversation=ConversationAccount(id="convo1"),
)


class TestMemoryScopes:
    @pytest.mark.asyncio
    async def test_class_memory_scope_should_find_registered_dialog(self):
        # Create ConversationState with MemoryStorage and register the state as middleware.
        conversation_state = ConversationState(MemoryStorage())

        # Create a DialogState property, DialogSet and register the dialogs.
        dialog_state = conversation_state.create_property("dialogs")
        dialogs = DialogSet(dialog_state)
        dialog = _TestDialog("test", "test message")
        dialogs.add(dialog)

        # Create test context
        adapter = DialogTestAdapter()
        context = TurnContext(adapter, _begin_message)
        await dialog_state.set(
            context, DialogState(dialog_stack=[DialogInstance(id="test", state={})])
        )

        dialog_context = await dialogs.create_context(context)

        # Run test
        scope = ClassMemoryScope()
        memory = scope.get_memory(dialog_context)
        assert memory, "memory not returned"
        assert memory.message == "test message"
        assert memory.expression == "resolved value"

    @pytest.mark.asyncio
    async def test_class_memory_scope_should_not_allow_set_memory_call(self):
        # Create ConversationState with MemoryStorage and register the state as middleware.
        conversation_state = ConversationState(MemoryStorage())

        # Create a DialogState property, DialogSet and register the dialogs.
        dialog_state = conversation_state.create_property("dialogs")
        dialogs = DialogSet(dialog_state)
        dialog = _TestDialog("test", "test message")
        dialogs.add(dialog)

        # Create test context
        adapter = DialogTestAdapter()
        context = TurnContext(adapter, _begin_message)
        await dialog_state.set(
            context, DialogState(dialog_stack=[DialogInstance(id="test", state={})])
        )

        dialog_context = await dialogs.create_context(context)

        # Run test
        scope = ClassMemoryScope()
        with pytest.raises(Exception) as exc_info:
            scope.set_memory(dialog_context, {})

        assert "not supported" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_class_memory_scope_should_not_allow_load_and_save_changes_calls(
        self,
    ):
        # Create ConversationState with MemoryStorage and register the state as middleware.
        conversation_state = ConversationState(MemoryStorage())

        # Create a DialogState property, DialogSet and register the dialogs.
        dialog_state = conversation_state.create_property("dialogs")
        dialogs = DialogSet(dialog_state)
        dialog = _TestDialog("test", "test message")
        dialogs.add(dialog)

        # Create test context
        adapter = DialogTestAdapter()
        context = TurnContext(adapter, _begin_message)
        await dialog_state.set(
            context, DialogState(dialog_stack=[DialogInstance(id="test", state={})])
        )

        dialog_context = await dialogs.create_context(context)

        # Run test
        scope = ClassMemoryScope()
        await scope.load(dialog_context)
        memory = scope.get_memory(dialog_context)
        with pytest.raises(AttributeError) as exc_info:
            memory.message = "foo"

        assert "can't set attribute" in str(exc_info.value)
        await scope.save_changes(dialog_context)
        assert dialog.message == "test message"

    def test_class_memory_scope_has_unique_name(self):
        """ClassMemoryScope must use 'class', not 'settings', to avoid colliding with SettingsMemoryScope."""
        assert ClassMemoryScope().name == "class"
        assert ClassMemoryScope().name != SettingsMemoryScope().name

    @pytest.mark.asyncio
    async def test_conversation_memory_scope_should_return_conversation_state(self):
        # Create ConversationState with MemoryStorage and register the state as middleware.
        conversation_state = ConversationState(MemoryStorage())

        # Create a DialogState property, DialogSet and register the dialogs.
        dialog_state = conversation_state.create_property("dialogs")
        dialogs = DialogSet(dialog_state)
        dialog = _TestDialog("test", "test message")
        dialogs.add(dialog)

        # Create test context
        adapter = DialogTestAdapter()
        context = TurnContext(adapter, _begin_message)
        context.turn_state["ConversationState"] = conversation_state

        dialog_context = await dialogs.create_context(context)

        # Initialize conversation state
        foo_cls = namedtuple("TestObject", "foo")
        conversation_prop = conversation_state.create_property("conversation")
        await conversation_prop.set(context, foo_cls(foo="bar"))
        await conversation_state.save(context)

        # Run test
        scope = ConversationMemoryScope()
        memory = scope.get_memory(dialog_context)
        assert memory, "memory not returned"

        # TODO: Make get_path_value take conversation.foo
        test_obj = ObjectPath.get_path_value(memory, "conversation")
        assert test_obj.foo == "bar"

    @pytest.mark.asyncio
    async def test_user_memory_scope_should_not_return_state_if_not_loaded(self):
        # Initialize user state
        storage = MemoryStorage()
        adapter = DialogTestAdapter()
        context = TurnContext(adapter, _begin_message)
        user_state = UserState(storage)
        context.turn_state["UserState"] = user_state
        foo_cls = namedtuple("TestObject", "foo")
        user_prop = user_state.create_property("conversation")
        await user_prop.set(context, foo_cls(foo="bar"))
        await user_state.save(context)

        # Replace context and user_state with new instances
        context = TurnContext(adapter, _begin_message)
        user_state = UserState(storage)
        context.turn_state["UserState"] = user_state

        # Create a DialogState property, DialogSet and register the dialogs.
        conversation_state = ConversationState(storage)
        dialog_state = conversation_state.create_property("dialogs")
        dialogs = DialogSet(dialog_state)
        dialog = _TestDialog("test", "test message")
        dialogs.add(dialog)

        # Create test context
        dialog_context = await dialogs.create_context(context)

        # Run test
        scope = UserMemoryScope()
        memory = scope.get_memory(dialog_context)
        assert memory is None, "state returned"

    @pytest.mark.asyncio
    async def test_user_memory_scope_should_return_state_once_loaded(self):
        # Initialize user state
        storage = MemoryStorage()
        adapter = DialogTestAdapter()
        context = TurnContext(adapter, _begin_message)
        user_state = UserState(storage)
        context.turn_state["UserState"] = user_state
        foo_cls = namedtuple("TestObject", "foo")
        user_prop = user_state.create_property("conversation")
        await user_prop.set(context, foo_cls(foo="bar"))
        await user_state.save(context)

        # Replace context and conversation_state with instances
        context = TurnContext(adapter, _begin_message)
        user_state = UserState(storage)
        context.turn_state["UserState"] = user_state

        # Create a DialogState property, DialogSet and register the dialogs.
        conversation_state = ConversationState(storage)
        context.turn_state["ConversationState"] = conversation_state
        dialog_state = conversation_state.create_property("dialogs")
        dialogs = DialogSet(dialog_state)
        dialog = _TestDialog("test", "test message")
        dialogs.add(dialog)

        # Create test context
        dialog_context = await dialogs.create_context(context)

        # Run test
        scope = UserMemoryScope()
        memory = scope.get_memory(dialog_context)
        assert memory is None, "state returned"

        await scope.load(dialog_context)
        memory = scope.get_memory(dialog_context)
        assert memory is not None, "state not returned"

        # TODO: Make get_path_value take conversation.foo
        test_obj = ObjectPath.get_path_value(memory, "conversation")
        assert test_obj.foo == "bar"

    @pytest.mark.asyncio
    async def test_dialog_memory_scope_should_return_containers_state(self):
        # Create a DialogState property, DialogSet and register the dialogs.
        storage = MemoryStorage()
        conversation_state = ConversationState(storage)
        dialog_state = conversation_state.create_property("dialogs")
        dialogs = DialogSet(dialog_state)
        container = _TestContainer("container")
        dialogs.add(container)

        # Create test context
        adapter = DialogTestAdapter()
        context = TurnContext(adapter, _begin_message)
        dialog_context = await dialogs.create_context(context)

        # Run test
        scope = DialogMemoryScope()
        await dialog_context.begin_dialog("container")
        memory = scope.get_memory(dialog_context)
        assert memory is not None, "state not returned"
        assert memory["is_container"]

    @pytest.mark.asyncio
    async def test_dialog_memory_scope_should_return_parent_containers_state_for_children(
        self,
    ):
        # Create a DialogState property, DialogSet and register the dialogs.
        storage = MemoryStorage()
        conversation_state = ConversationState(storage)
        dialog_state = conversation_state.create_property("dialogs")
        dialogs = DialogSet(dialog_state)
        container = _TestContainer("container", _TestDialog("child", "test message"))
        dialogs.add(container)

        # Create test context
        adapter = DialogTestAdapter()
        context = TurnContext(adapter, _begin_message)
        dialog_context = await dialogs.create_context(context)

        # Run test
        scope = DialogMemoryScope()
        await dialog_context.begin_dialog("container")
        child_dc = dialog_context.child
        assert child_dc is not None, "No child DC"
        memory = scope.get_memory(child_dc)
        assert memory is not None, "state not returned"
        assert memory["is_container"]

    @pytest.mark.asyncio
    async def test_dialog_memory_scope_should_return_childs_state_when_no_parent(self):
        # Create a DialogState property, DialogSet and register the dialogs.
        storage = MemoryStorage()
        conversation_state = ConversationState(storage)
        dialog_state = conversation_state.create_property("dialogs")
        dialogs = DialogSet(dialog_state)
        dialog = _TestDialog("test", "test message")
        dialogs.add(dialog)

        # Create test context
        adapter = DialogTestAdapter()
        context = TurnContext(adapter, _begin_message)
        dialog_context = await dialogs.create_context(context)

        # Run test
        scope = DialogMemoryScope()
        await dialog_context.begin_dialog("test")
        memory = scope.get_memory(dialog_context)
        assert memory is not None, "state not returned"
        assert memory["is_dialog"]

    @pytest.mark.asyncio
    async def test_dialog_memory_scope_should_overwrite_parents_memory(self):
        # Create a DialogState property, DialogSet and register the dialogs.
        storage = MemoryStorage()
        conversation_state = ConversationState(storage)
        dialog_state = conversation_state.create_property("dialogs")
        dialogs = DialogSet(dialog_state)
        container = _TestContainer("container", _TestDialog("child", "test message"))
        dialogs.add(container)

        # Create test context
        adapter = DialogTestAdapter()
        context = TurnContext(adapter, _begin_message)
        dialog_context = await dialogs.create_context(context)

        # Run test
        scope = DialogMemoryScope()
        await dialog_context.begin_dialog("container")
        child_dc = dialog_context.child
        assert child_dc is not None, "No child DC"

        foo_cls = namedtuple("TestObject", "foo")
        scope.set_memory(child_dc, foo_cls("bar"))
        memory = scope.get_memory(child_dc)
        assert memory is not None, "state not returned"
        assert memory.foo == "bar"

    @pytest.mark.asyncio
    async def test_dialog_memory_scope_should_overwrite_active_dialogs_memory(self):
        # Create a DialogState property, DialogSet and register the dialogs.
        storage = MemoryStorage()
        conversation_state = ConversationState(storage)
        dialog_state = conversation_state.create_property("dialogs")
        dialogs = DialogSet(dialog_state)
        container = _TestContainer("container")
        dialogs.add(container)

        # Create test context
        adapter = DialogTestAdapter()
        context = TurnContext(adapter, _begin_message)
        dialog_context = await dialogs.create_context(context)

        # Run test
        scope = DialogMemoryScope()
        await dialog_context.begin_dialog("container")
        foo_cls = namedtuple("TestObject", "foo")
        scope.set_memory(dialog_context, foo_cls("bar"))
        memory = scope.get_memory(dialog_context)
        assert memory is not None, "state not returned"
        assert memory.foo == "bar"

    @pytest.mark.asyncio
    async def test_dialog_memory_scope_should_raise_error_if_set_memory_called_without_memory(
        self,
    ):
        # Create a DialogState property, DialogSet and register the dialogs.
        storage = MemoryStorage()
        conversation_state = ConversationState(storage)
        dialog_state = conversation_state.create_property("dialogs")
        dialogs = DialogSet(dialog_state)
        container = _TestContainer("container")
        dialogs.add(container)

        # Create test context
        adapter = DialogTestAdapter()
        context = TurnContext(adapter, _begin_message)
        dialog_context = await dialogs.create_context(context)

        # Run test
        with pytest.raises(Exception):
            scope = DialogMemoryScope()
            await dialog_context.begin_dialog("container")
            scope.set_memory(dialog_context, None)

    @pytest.mark.skip(reason="Requires test_settings module not available")
    @pytest.mark.asyncio
    async def test_settings_memory_scope_should_return_content_of_settings(self):
        # pylint: disable=import-outside-toplevel
        from tests.hosting_dialogs.memory.scopes.test_settings import DefaultConfig

        # Create a DialogState property, DialogSet and register the dialogs.
        conversation_state = ConversationState(MemoryStorage())
        dialog_state = conversation_state.create_property("dialogs")
        dialogs = DialogSet(dialog_state).add(_TestDialog("test", "test message"))

        # Create test context
        adapter = DialogTestAdapter()
        context = TurnContext(adapter, _begin_message)
        dialog_context = await dialogs.create_context(context)
        settings = DefaultConfig()
        dialog_context.context.turn_state["settings"] = settings

        # Run test
        scope = SettingsMemoryScope()
        memory = scope.get_memory(dialog_context)
        assert memory is not None
        assert memory.STRING == "test"
        assert memory.INT == 3
        assert memory.LIST[0] == "zero"
        assert memory.LIST[1] == "one"
        assert memory.LIST[2] == "two"
        assert memory.LIST[3] == "three"

    @pytest.mark.asyncio
    async def test_this_memory_scope_should_return_active_dialogs_state(self):
        # Create a DialogState property, DialogSet and register the dialogs.
        storage = MemoryStorage()
        conversation_state = ConversationState(storage)
        dialog_state = conversation_state.create_property("dialogs")
        dialogs = DialogSet(dialog_state)
        dialog = _TestDialog("test", "test message")
        dialogs.add(dialog)

        # Create test context
        adapter = DialogTestAdapter()
        context = TurnContext(adapter, _begin_message)
        dialog_context = await dialogs.create_context(context)

        # Run test
        scope = ThisMemoryScope()
        await dialog_context.begin_dialog("test")
        memory = scope.get_memory(dialog_context)
        assert memory is not None, "state not returned"
        assert memory["is_dialog"]

    @pytest.mark.asyncio
    async def test_this_memory_scope_should_overwrite_active_dialogs_memory(self):
        # Create a DialogState property, DialogSet and register the dialogs.
        storage = MemoryStorage()
        conversation_state = ConversationState(storage)
        dialog_state = conversation_state.create_property("dialogs")
        dialogs = DialogSet(dialog_state)
        container = _TestContainer("container")
        dialogs.add(container)

        # Create test context
        adapter = DialogTestAdapter()
        context = TurnContext(adapter, _begin_message)
        dialog_context = await dialogs.create_context(context)

        # Run test
        scope = ThisMemoryScope()
        await dialog_context.begin_dialog("container")
        foo_cls = namedtuple("TestObject", "foo")
        scope.set_memory(dialog_context, foo_cls("bar"))
        memory = scope.get_memory(dialog_context)
        assert memory is not None, "state not returned"
        assert memory.foo == "bar"

    @pytest.mark.asyncio
    async def test_this_memory_scope_should_raise_error_if_set_memory_called_without_memory(
        self,
    ):
        # Create a DialogState property, DialogSet and register the dialogs.
        storage = MemoryStorage()
        conversation_state = ConversationState(storage)
        dialog_state = conversation_state.create_property("dialogs")
        dialogs = DialogSet(dialog_state)
        container = _TestContainer("container")
        dialogs.add(container)

        # Create test context
        adapter = DialogTestAdapter()
        context = TurnContext(adapter, _begin_message)
        dialog_context = await dialogs.create_context(context)

        # Run test
        with pytest.raises(Exception):
            scope = ThisMemoryScope()
            await dialog_context.begin_dialog("container")
            scope.set_memory(dialog_context, None)

    @pytest.mark.asyncio
    async def test_this_memory_scope_should_raise_error_if_set_memory_called_without_active_dialog(
        self,
    ):
        # Create a DialogState property, DialogSet and register the dialogs.
        storage = MemoryStorage()
        conversation_state = ConversationState(storage)
        dialog_state = conversation_state.create_property("dialogs")
        dialogs = DialogSet(dialog_state)
        container = _TestContainer("container")
        dialogs.add(container)

        # Create test context
        adapter = DialogTestAdapter()
        context = TurnContext(adapter, _begin_message)
        dialog_context = await dialogs.create_context(context)

        # Run test
        with pytest.raises(Exception):
            scope = ThisMemoryScope()
            foo_cls = namedtuple("TestObject", "foo")
            scope.set_memory(dialog_context, foo_cls("bar"))

    @pytest.mark.asyncio
    async def test_turn_memory_scope_should_persist_changes_to_turn_state(self):
        # Create a DialogState property, DialogSet and register the dialogs.
        storage = MemoryStorage()
        conversation_state = ConversationState(storage)
        dialog_state = conversation_state.create_property("dialogs")
        dialogs = DialogSet(dialog_state)
        dialog = _TestDialog("test", "test message")
        dialogs.add(dialog)

        # Create test context
        adapter = DialogTestAdapter()
        context = TurnContext(adapter, _begin_message)
        dialog_context = await dialogs.create_context(context)

        # Run test
        scope = TurnMemoryScope()
        memory = scope.get_memory(dialog_context)
        assert memory is not None, "state not returned"
        memory["foo"] = "bar"
        memory = scope.get_memory(dialog_context)
        assert memory["foo"] == "bar"

    @pytest.mark.asyncio
    async def test_turn_memory_scope_should_overwrite_values_in_turn_state(self):
        # Create a DialogState property, DialogSet and register the dialogs.
        storage = MemoryStorage()
        conversation_state = ConversationState(storage)
        dialog_state = conversation_state.create_property("dialogs")
        dialogs = DialogSet(dialog_state)
        dialog = _TestDialog("test", "test message")
        dialogs.add(dialog)

        # Create test context
        adapter = DialogTestAdapter()
        context = TurnContext(adapter, _begin_message)
        dialog_context = await dialogs.create_context(context)

        # Run test
        scope = TurnMemoryScope()
        foo_cls = namedtuple("TestObject", "foo")
        scope.set_memory(dialog_context, foo_cls("bar"))
        memory = scope.get_memory(dialog_context)
        assert memory is not None, "state not returned"
        assert memory.foo == "bar"

    def test_dialog_context_memory_scope_has_unique_name(self):
        """DialogContextMemoryScope must not share its scope name with SettingsMemoryScope."""
        dc_scope = DialogContextMemoryScope()
        settings_scope = SettingsMemoryScope()
        assert dc_scope.name == "dialogContext"
        assert dc_scope.name != settings_scope.name
