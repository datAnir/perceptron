#!/usr/bin/env python3
"""
Example demonstrating Arcon with Anthropic Claude.

This example shows how to:
1. Initialize an Anthropic provider with automatic .env loading
2. Create a session
3. Send messages and get streaming responses
4. Track token usage and costs

Note: API key is automatically loaded from .env file
"""

import asyncio
from pathlib import Path
from arcon.core.types import ProviderType
from arcon.providers import ProviderResolver
from arcon.core.session import Session
from arcon.config import load_config, get_api_key


async def main():
    """Main example function."""
    
    print("=" * 80)
    print("Arcon - Anthropic Claude Example")
    print("=" * 80)
    
    # Load config from .env file
    load_config()
    
    # Check if API key is available
    if not get_api_key(ProviderType.ANTHROPIC):
        print("\n❌ Error: ANTHROPIC_API_KEY not found")
        print("   Please set it in your .env file:")
        print("   ANTHROPIC_API_KEY=sk-ant-api03-your-key-here")
        return
    
    print("\n✅ API key loaded from .env file")
    
    # Create provider - API key is automatically loaded from .env
    print("\n📦 Initializing Anthropic Provider")
    print("   (API key automatically loaded from .env)")
    
    provider = ProviderResolver.get_provider(
        provider_type=ProviderType.ANTHROPIC,
        # No need to pass api_key - it's loaded from .env!
        model="claude-opus-4-20250514",  # Claude Opus 4.6
        temperature=0.7,
        max_tokens=2048
    )
    
    # List available models
    print(f"\n🤖 Available Anthropic Models:")
    models = await provider.list_models()
    for model in models:
        print(f"   - {model.name}: {model.context_window:,} tokens")
    
    # Create a session
    working_dir = Path(__file__).parent / "workspace"
    working_dir.mkdir(exist_ok=True)
    
    session = Session(
        provider=provider,
        working_dir=str(working_dir)
    )
    
    print(f"\n🗣️  Session ID: {session.id}")
    print(f"📁 Working Directory: {working_dir}")
    
    # Example 1: Simple query with streaming
    print("\n" + "=" * 80)
    print("Example 1: Simple Query with Streaming")
    print("=" * 80)
    
    query = "What are the three most important principles of clean code? Keep it concise."
    print(f"\n💬 Query: {query}\n")
    print("🤖 Response: ", end="", flush=True)
    
    async for chunk in session.invoke(query):
        if chunk.get("type") == "text":
            print(chunk.get("content", ""), end="", flush=True)
    
    print("\n")
    
    # Show token usage
    print(f"\n📊 Token Usage:")
    print(f"   - Input tokens: {session._total_input_tokens:,}")
    print(f"   - Output tokens: {session._total_output_tokens:,}")
    print(f"   - Total cost: ${session._total_cost_usd:.4f}")
    
    # Example 2: Follow-up question (using conversation context)
    print("\n" + "=" * 80)
    print("Example 2: Follow-up Question (Context-Aware)")
    print("=" * 80)
    
    query2 = "Can you elaborate on the first principle?"
    print(f"\n💬 Query: {query2}\n")
    print("🤖 Response: ", end="", flush=True)
    
    async for chunk in session.invoke(query2):
        if chunk.get("type") == "text":
            print(chunk.get("content", ""), end="", flush=True)
    
    print("\n")
    
    # Show updated token usage
    print(f"\n📊 Updated Token Usage:")
    print(f"   - Input tokens: {session._total_input_tokens:,}")
    print(f"   - Output tokens: {session._total_output_tokens:,}")
    print(f"   - Total cost: ${session._total_cost_usd:.4f}")
    
    # Show conversation context
    print(f"\n📝 Conversation History:")
    context = session.get_context()
    for i, msg in enumerate(context, 1):
        role_emoji = "👤" if msg.role.value == "user" else "🤖"
        content_preview = msg.content[:60] + "..." if len(msg.content) > 60 else msg.content
        print(f"   {i}. {role_emoji} {msg.role.value}: {content_preview}")
    
    # Example 3: Using system prompt
    print("\n" + "=" * 80)
    print("Example 3: Using System Prompt")
    print("=" * 80)
    
    system_prompt = "You are a helpful Python programming tutor. Always provide code examples."
    query3 = "How do I read a JSON file in Python?"
    
    print(f"\n🎯 System Prompt: {system_prompt}")
    print(f"💬 Query: {query3}\n")
    print("🤖 Response: ", end="", flush=True)
    
    async for chunk in session.invoke(query3, system_prompt=system_prompt):
        if chunk.get("type") == "text":
            print(chunk.get("content", ""), end="", flush=True)
    
    print("\n")
    
    # Final statistics
    print("\n" + "=" * 80)
    print("Final Statistics")
    print("=" * 80)
    print(f"   - Total messages: {len(session.messages)}")
    print(f"   - Input tokens: {session._total_input_tokens:,}")
    print(f"   - Output tokens: {session._total_output_tokens:,}")
    print(f"   - Total cost: ${session._total_cost_usd:.4f}")
    print(f"   - Model: {provider.config.model}")
    
    # Get cost per token for reference
    input_cost, output_cost = provider.get_cost_per_token(provider.config.model)
    print(f"\n💰 Pricing (per 1M tokens):")
    print(f"   - Input: ${input_cost:.2f}")
    print(f"   - Output: ${output_cost:.2f}")
    
    print("\n✅ Example completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
