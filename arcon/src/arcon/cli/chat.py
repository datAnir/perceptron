"""Interactive chat interface."""
import sys
import asyncio
from pathlib import Path
from typing import Optional
from datetime import datetime

from ..core.types import ProviderType, Message, Role
from ..providers import ProviderResolver
from ..core.session import Session
from ..storage import StorageManager
from ..agents import AgentRegistry, AgentLoader
from ..tools import get_global_registry


class ChatInterface:
    """Interactive chat interface."""
    
    def __init__(
        self,
        provider_type: ProviderType,
        model: Optional[str] = None,
        agent_name: Optional[str] = None,
        session_id: Optional[str] = None,
        use_storage: bool = True,
    ):
        """Initialize chat interface.
        
        Args:
            provider_type: LLM provider type
            model: Model name (optional)
            agent_name: Agent to use (optional)
            session_id: Existing session ID to resume
            use_storage: Whether to persist to database
        """
        self.provider_type = provider_type
        self.model = model
        self.agent_name = agent_name
        self.session_id = session_id
        self.use_storage = use_storage
        
        self.provider = None
        self.session = None
        self.storage = None
        self.agent = None
    
    def run(self) -> int:
        """Run the chat interface."""
        try:
            asyncio.run(self._run_async())
            return 0
        except Exception as e:
            print(f"\n❌ Error: {e}", file=sys.stderr)
            return 1
    
    async def _run_async(self):
        """Async chat loop."""
        # Initialize provider
        self.provider = ProviderResolver.get_provider(
            provider_type=self.provider_type,
            model=self.model,
        )
        
        # Initialize storage if enabled
        if self.use_storage:
            self.storage = StorageManager()
            
            # Resume or create session
            if self.session_id:
                stored_session = self.storage.get_session(self.session_id)
                if not stored_session:
                    print(f"❌ Session {self.session_id} not found")
                    return
                print(f"📂 Resuming session: {self.session_id}")
            else:
                # Create new session
                self.session_id = datetime.now().strftime("%Y%m%d-%H%M%S")
        
        # Create session
        working_dir = Path.cwd() / "workspace"
        working_dir.mkdir(exist_ok=True)
        
        self.session = Session(
            provider=self.provider,
            working_dir=str(working_dir),
        )
        
        # Load agent if specified
        if self.agent_name:
            agent_registry = AgentRegistry()
            # Try to load from agents directory
            agents_dir = Path("agents")
            if agents_dir.exists():
                loader = AgentLoader()
                for agent_file in agents_dir.glob("**/*.yaml"):
                    try:
                        agent = loader.load_agent(str(agent_file))
                        agent_registry.register(agent)
                    except:
                        pass
            
            self.agent = agent_registry.get(self.agent_name)
            if not self.agent:
                print(f"⚠️  Warning: Agent '{self.agent_name}' not found, continuing without agent")
        
        # Store session if using storage
        if self.use_storage and self.storage:
            self.storage.create_session(
                session_id=self.session_id,
                provider_type=self.provider_type,
                model=self.provider.config.model,
                temperature=self.provider.config.temperature,
                max_tokens=self.provider.config.max_tokens,
                working_dir=str(working_dir),
            )
        
        # Display welcome message
        self._display_welcome()
        
        # Load message history if resuming
        if self.use_storage and self.storage and self.session_id:
            messages = self.storage.get_messages(self.session_id)
            if messages:
                print(f"\n📜 Loading {len(messages)} previous messages...")
                for msg in messages:
                    # Add to session
                    self.session.messages.append(
                        Message(role=Role(msg.role), content=msg.content)
                    )
                print()
        
        # Chat loop
        await self._chat_loop()
    
    def _display_welcome(self):
        """Display welcome message."""
        print("\n" + "=" * 80)
        print("🚀 Arcon Interactive Chat")
        print("=" * 80)
        print(f"Provider: {self.provider_type.value}")
        print(f"Model: {self.provider.config.model}")
        if self.agent:
            print(f"Agent: {self.agent.metadata.name}")
        if self.session_id:
            print(f"Session: {self.session_id}")
        print("\nCommands:")
        print("  /help    - Show available commands")
        print("  /clear   - Clear conversation history")
        print("  /tokens  - Show token usage")
        print("  /quit    - Exit chat")
        print("\n" + "=" * 80 + "\n")
    
    async def _chat_loop(self):
        """Main chat loop."""
        while True:
            try:
                # Get user input
                user_input = input("You: ").strip()
                
                if not user_input:
                    continue
                
                # Handle commands
                if user_input.startswith("/"):
                    if await self._handle_command(user_input):
                        break
                    continue
                
                # Add user message
                self.session.add_message(Role.USER, user_input)
                
                # Store user message
                if self.use_storage and self.storage:
                    self.storage.add_message(
                        session_id=self.session_id,
                        role=Role.USER,
                        content=user_input,
                    )
                
                # Get response
                print("\nAssistant: ", end="", flush=True)
                
                response_content = []
                async for chunk in self.session.send_message(user_input):
                    if isinstance(chunk, dict):
                        if chunk.get("type") == "text":
                            text = chunk.get("content", "")
                            print(text, end="", flush=True)
                            response_content.append(text)
                    else:
                        print(chunk, end="", flush=True)
                        response_content.append(chunk)
                
                print("\n")
                
                # Store assistant message
                if self.use_storage and self.storage and response_content:
                    full_response = "".join(str(c) for c in response_content)
                    self.storage.add_message(
                        session_id=self.session_id,
                        role=Role.ASSISTANT,
                        content=full_response,
                    )
                
            except KeyboardInterrupt:
                print("\n")
                break
            except EOFError:
                print("\n")
                break
            except Exception as e:
                print(f"\n⚠️  Error: {e}\n")
    
    async def _handle_command(self, command: str) -> bool:
        """Handle special commands.
        
        Returns:
            True if should exit, False otherwise
        """
        cmd = command.lower().strip()
        
        if cmd == "/quit" or cmd == "/exit":
            print("\n👋 Goodbye!")
            return True
        
        elif cmd == "/help":
            print("\nAvailable commands:")
            print("  /help    - Show this help message")
            print("  /clear   - Clear conversation history")
            print("  /tokens  - Show token usage")
            print("  /quit    - Exit chat")
            print()
        
        elif cmd == "/clear":
            self.session.messages.clear()
            print("\n🗑️  Conversation history cleared\n")
        
        elif cmd == "/tokens":
            print(f"\nToken usage:")
            print(f"  Input tokens: {self.session.total_input_tokens:,}")
            print(f"  Output tokens: {self.session.total_output_tokens:,}")
            print(f"  Total cost: ${self.session.total_cost:.6f}")
            print()
        
        else:
            print(f"\n⚠️  Unknown command: {command}")
            print("   Type /help for available commands\n")
        
        return False
