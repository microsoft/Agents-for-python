import asyncio
import json
import sys
import threading
import uuid
from io import StringIO
from typing import Dict, List, Optional
from threading import Lock
from collections import defaultdict

from aiohttp import web, ClientSession
from aiohttp.web import Request, Response
import aiohttp_security
from microsoft_agents.core.models import Activity, EntityTypes, ActivityTypes, StreamInfo, StreamTypes
from microsoft_agents.core.serialization import ProtocolJsonSerializer

class BotResponse:
    """Python equivalent of the C# BotResponse class using aiohttp web framework."""
    
    def __init__(self):
        self._app: Optional[web.Application] = None
        self._runner: Optional[web.AppRunner] = None
        self._site: Optional[web.TCPSite] = None
        self._multiple_activities: Dict[str, List[Activity]] = defaultdict(list)
        self._activity_locks: Dict[str, Lock] = defaultdict(Lock)
        self.test_id: str = str(uuid.uuid4())
        self.service_endpoint: str = "http://localhost:9873"
        
        # Suppress console output (equivalent to Console.SetOut(TextWriter.Null))
        sys.stdout = StringIO()
        
        # Initialize the web application
        self._setup_app()
    
    def _setup_app(self):
        """Setup the aiohttp web application with routes and middleware."""
        self._app = web.Application()
        
        # Add JWT authentication middleware (placeholder - would need proper implementation)
        # self._app.middlewares.append(self._auth_middleware)
        
        # Add routes
        self._app.router.add_post('/v3/conversations/{path:.*}', self._handle_conversation)
        
    async def _auth_middleware(self, request: Request, handler):
        """JWT authentication middleware (placeholder implementation)."""
        # TODO: Implement proper JWT authentication
        return await handler(request)
    
    async def _handle_conversation(self, request: Request) -> Response:
        """Handle POST requests to /v3/conversations/{*text}."""
        try:
            # Read request body
            body = await request.text()
            act = ProtocolJsonSerializer.to_object(body, Activity)
            cid = act.conversation.id if act.conversation else None
            
            if not cid:
                return web.Response(status=400, text="Missing conversation ID")
            
            # Add activity to the list (thread-safe)
            with self._activity_locks[cid]:
                self._multiple_activities[cid].append(act)
            
            # Create response
            response_data = {
                "Id": str(uuid.uuid4())
            }
            
            # Check if the activity is a streamed activity
            if (act.entities and 
                any(e.type == EntityTypes.STREAM_INFO for e in act.entities)):
                
                entities_json = ProtocolJsonSerializer.to_json(act.entities[0])
                sact = ProtocolJsonSerializer.to_object(entities_json, StreamInfo)
                
                handled = self._handle_streamed_activity(act, sact, cid)
                
                response = web.Response(
                    status=200,
                    content_type="application/json",
                    text=json.dumps(response_data)
                )
                
                # Handle task completion (would need BotClient implementation)
                if handled:
                    await self._complete_streaming_task(cid)
                
                return response
            else:
                # Handle non-streamed activities
                if act.type != ActivityTypes.TYPING:
                    # Start background task with 5-second delay
                    asyncio.create_task(self._delayed_task_completion(cid))
                
                return web.Response(
                    status=200,
                    content_type="application/json",
                    text=json.dumps(response_data)
                )
                
        except Exception as e:
            return web.Response(status=500, text=str(e))
    
    def _handle_streamed_activity(self, act: Activity, sact: StreamInfo, cid: str) -> bool:
        """Handle streamed activity logic."""
        
        # Check if activity is the final message
        if sact.stream_type == StreamTypes.FINAL:
            if act.type == ActivityTypes.MESSAGE:
                return True
            else:
                raise Exception("final streamed activity should be type message")
        
        # Handler for streaming types which allows us to verify later if the text length has increased
        elif sact.stream_type == StreamTypes.STREAMING:
            if sact.stream_sequence <= 0 and act.type == ActivityTypes.TYPING:
                raise Exception("streamed activity's stream sequence should be a positive number")
        
        # Activity is being streamed but isn't the final message
        return False
    
    async def _complete_streaming_task(self, cid: str):
        """Complete streaming task (placeholder for BotClient.TaskList logic)."""
        # TODO: Implement BotClient.TaskList equivalent
        # This would require the BotClient class to be implemented
        if cid in self._multiple_activities:
            activities = self._multiple_activities[cid].copy()
            # Complete the task with activities
            # BotClient.complete_task(cid, activities)
            # Clean up
            del self._multiple_activities[cid]
            if cid in self._activity_locks:
                del self._activity_locks[cid]
    
    async def _delayed_task_completion(self, cid: str):
        """Handle delayed task completion after 5 seconds."""
        await asyncio.sleep(5.0)
        # TODO: Implement BotClient.TaskList equivalent
        # if BotClient.has_task(cid):
        #     activities = self._multiple_activities.get(cid, [])
        #     BotClient.complete_task(cid, activities)
    
    async def start(self):
        """Start the web server."""
        self._runner = web.AppRunner(self._app)
        await self._runner.setup()
        
        # Extract port from service_endpoint
        port = int(self.service_endpoint.split(':')[-1])
        self._site = web.TCPSite(self._runner, 'localhost', port)
        await self._site.start()
        
        print(f"Bot server started at {self.service_endpoint}")
    
    async def dispose(self):
        """Cleanup resources (equivalent to DisposeAsync)."""
        if self._site:
            await self._site.stop()
        if self._runner:
            await self._runner.cleanup()
        
        # Restore stdout
        sys.stdout = sys.__stdout__


# Example usage
async def main():
    bot_response = BotResponse()
    try:
        await bot_response.start()
        # Keep the server running
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        await bot_response.dispose()


if __name__ == "__main__":
    asyncio.run(main())