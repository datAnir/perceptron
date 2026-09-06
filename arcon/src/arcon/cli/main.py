"""Command-line interface for Arcon."""
import sys
import argparse
from pathlib import Path
from typing import Optional

from ..config import load_config, get_api_key
from ..core.types import ProviderType
from .chat import ChatInterface
from .sessions import SessionManager
from .config_cmd import ConfigManager


def create_parser() -> argparse.ArgumentParser:
    """Create CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="arcon",
        description="Arcon - Advanced AI Coding Assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Chat command
    chat_parser = subparsers.add_parser("chat", help="Start interactive chat session")
    chat_parser.add_argument(
        "--provider",
        choices=["anthropic", "openai", "ollama"],
        help="LLM provider to use (default: from config)",
    )
    chat_parser.add_argument(
        "--model",
        help="Model to use (default: from config)",
    )
    chat_parser.add_argument(
        "--agent",
        help="Agent to use (optional)",
    )
    chat_parser.add_argument(
        "--session",
        help="Resume existing session by ID",
    )
    chat_parser.add_argument(
        "--no-storage",
        action="store_true",
        help="Don't persist session to database",
    )
    
    # Session management
    session_parser = subparsers.add_parser("sessions", help="Manage chat sessions")
    session_subparsers = session_parser.add_subparsers(dest="session_command")
    
    session_subparsers.add_parser("list", help="List all sessions")
    
    show_parser = session_subparsers.add_parser("show", help="Show session details")
    show_parser.add_argument("session_id", help="Session ID")
    
    delete_parser = session_subparsers.add_parser("delete", help="Delete a session")
    delete_parser.add_argument("session_id", help="Session ID")
    
    session_subparsers.add_parser("stats", help="Show database statistics")
    
    # Config management
    config_parser = subparsers.add_parser("config", help="Manage configuration")
    config_subparsers = config_parser.add_subparsers(dest="config_command")
    
    config_subparsers.add_parser("show", help="Show current configuration")
    
    set_parser = config_subparsers.add_parser("set", help="Set configuration value")
    set_parser.add_argument("key", help="Configuration key")
    set_parser.add_argument("value", help="Configuration value")
    
    config_subparsers.add_parser("init", help="Initialize .env file")
    
    # Agent management
    agent_parser = subparsers.add_parser("agents", help="List available agents")
    agent_parser.add_argument(
        "--type",
        help="Filter by agent type",
    )
    
    # Skill management
    skill_parser = subparsers.add_parser("skills", help="List available skills")
    skill_parser.add_argument(
        "--category",
        help="Filter by category",
    )
    
    # Version
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0",
    )
    
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args(argv)
    
    # Load configuration
    load_config()
    
    # Route to appropriate handler
    try:
        if args.command == "chat":
            return handle_chat(args)
        elif args.command == "sessions":
            return handle_sessions(args)
        elif args.command == "config":
            return handle_config(args)
        elif args.command == "agents":
            return handle_agents(args)
        elif args.command == "skills":
            return handle_skills(args)
        else:
            parser.print_help()
            return 0
    except KeyboardInterrupt:
        print("\n\n✋ Interrupted by user")
        return 130
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        return 1


def handle_chat(args) -> int:
    """Handle chat command."""
    # Validate provider
    provider_type = None
    if args.provider:
        provider_type = ProviderType(args.provider)
    else:
        # Default to anthropic if not specified
        provider_type = ProviderType.ANTHROPIC
    
    # Check API key
    if not get_api_key(provider_type):
        print(f"❌ Error: No API key found for {provider_type.value}")
        print("   Please set it in your .env file:")
        print(f"   {provider_type.value.upper()}_API_KEY=your-key-here")
        return 1
    
    # Start chat interface
    interface = ChatInterface(
        provider_type=provider_type,
        model=args.model,
        agent_name=args.agent,
        session_id=args.session,
        use_storage=not args.no_storage,
    )
    
    return interface.run()


def handle_sessions(args) -> int:
    """Handle sessions command."""
    manager = SessionManager()
    
    if args.session_command == "list":
        manager.list_sessions()
    elif args.session_command == "show":
        manager.show_session(args.session_id)
    elif args.session_command == "delete":
        manager.delete_session(args.session_id)
    elif args.session_command == "stats":
        manager.show_stats()
    else:
        print("Usage: arcon sessions {list|show|delete|stats}")
        return 1
    
    return 0


def handle_config(args) -> int:
    """Handle config command."""
    manager = ConfigManager()
    
    if args.config_command == "show":
        manager.show_config()
    elif args.config_command == "set":
        manager.set_config(args.key, args.value)
    elif args.config_command == "init":
        manager.init_env()
    else:
        print("Usage: arcon config {show|set|init}")
        return 1
    
    return 0


def handle_agents(args) -> int:
    """Handle agents command."""
    from ..agents import AgentRegistry
    
    registry = AgentRegistry()
    
    # Load agents from directory if it exists
    agents_dir = Path("agents")
    if agents_dir.exists():
        from ..agents import AgentLoader
        loader = AgentLoader()
        for agent_file in agents_dir.glob("**/*.yaml"):
            try:
                agent = loader.load_agent(agent_file)
                registry.register(agent)
            except Exception as e:
                print(f"Warning: Failed to load {agent_file}: {e}", file=sys.stderr)
    
    # Filter and display
    if args.type:
        agents = registry.get_by_type(args.type)
    else:
        agents = registry.list_all()
    
    if not agents:
        print("No agents found.")
        return 0
    
    print(f"\n📋 Available Agents ({len(agents)}):")
    print("=" * 80)
    
    for agent in agents:
        metadata = agent.metadata
        print(f"\n🤖 {metadata.name}")
        print(f"   Type: {metadata.agent_type}")
        if metadata.specialization:
            print(f"   Specialization: {metadata.specialization}")
        print(f"   Description: {metadata.description}")
        if metadata.tags:
            print(f"   Tags: {', '.join(metadata.tags)}")
    
    print()
    return 0


def handle_skills(args) -> int:
    """Handle skills command."""
    from ..skills import SkillRegistry
    
    registry = SkillRegistry()
    
    # Load skills from directory if it exists
    skills_dir = Path("skills")
    if skills_dir.exists():
        from ..skills import SkillLoader
        loader = SkillLoader()
        for skill_file in skills_dir.glob("**/*.md"):
            try:
                skill = loader.load_skill(skill_file)
                registry.register(skill)
            except Exception as e:
                print(f"Warning: Failed to load {skill_file}: {e}", file=sys.stderr)
    
    # Filter and display
    if args.category:
        skills = registry.get_by_category(args.category)
    else:
        skills = registry.list_all()
    
    if not skills:
        print("No skills found.")
        return 0
    
    print(f"\n📚 Available Skills ({len(skills)}):")
    print("=" * 80)
    
    # Group by category
    by_category: dict[str, list] = {}
    for skill in skills:
        cat = skill.metadata.category
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(skill)
    
    for category, cat_skills in sorted(by_category.items()):
        print(f"\n📂 {category} ({len(cat_skills)})")
        for skill in cat_skills:
            metadata = skill.metadata
            print(f"   • {metadata.name}: {metadata.description}")
    
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
