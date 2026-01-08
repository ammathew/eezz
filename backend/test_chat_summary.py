#!/usr/bin/env python
"""
Test script for iterating on chat summary prompts.

Usage:
    python test_chat_summary.py
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from api.models import Conversation
from api.gemini_service import GeminiService
import json
import re


def create_chat_summary_v1(conversation):
    """
    OLD VERSION: Focus on AI interpretation
    """
    messages = conversation.messages.all().order_by('created_at')

    chat_text = ""
    for msg in messages:
        role = "User" if msg.role == 'user' else "AI"
        chat_text += f"{role}: {msg.content}\n\n"

    prompt = f"""You are summarizing a dream interpretation conversation. Extract the key insights and themes.

Conversation:
{chat_text}

Provide a JSON response with:
{{
    "summary": "Brief 2-3 sentence summary of what the interpretation revealed",
    "key_themes": ["theme1", "theme2", "theme3"],
    "user_resonance": "What the user seemed to connect with or push back on"
}}

Keep it concise and focused on what matters for future context."""

    return prompt, "v1_interpretation_focused"


def create_chat_summary_v2(conversation):
    """
    NEW VERSION: Focus on user's dream and their reaction
    """
    messages = conversation.messages.all().order_by('created_at')

    # Separate user messages from AI messages
    user_messages = []
    ai_messages = []

    for msg in messages:
        if msg.role == 'user':
            user_messages.append(msg.content)
        else:
            ai_messages.append(msg.content)

    # Build conversation with labels
    chat_text = ""
    for msg in messages:
        role = "User" if msg.role == 'user' else "AI"
        chat_text += f"{role}: {msg.content}\n\n"

    prompt = f"""You are creating a concise summary of a dream conversation.

IMPORTANT: Focus on what the USER shared, not what the AI said.

Conversation:
{chat_text}



Focus on:
- What the USER dreamed about
- What the USER said in response (if anything beyond initial dream)
- NOT what the AI interpreted

Keep it concise."""

    return prompt, "v2_user_focused"


def create_chat_summary_v3(conversation):
    """
    VERSION 3: Ultra-concise, story-focused
    """
    messages = conversation.messages.all().order_by('created_at')

    chat_text = ""
    for msg in messages:
        role = "User" if msg.role == 'user' else "AI"
        chat_text += f"{role}: {msg.content}\n\n"

    prompt = f"""Summarize this dream conversation focusing ONLY on what the user shared.

Conversation:
{chat_text}

Provide a JSON response with:
{{
    "dream": "What the user dreamed (1 sentence)",
    "user_said": "Anything the user said beyond the initial dream (their thoughts, connections, questions). Empty string if they only shared the dream.",
    "symbols": ["key", "dream", "symbols"]
}}

DO NOT summarize what the AI said. Only capture what the USER experienced and shared."""

    return prompt, "v3_ultra_concise"


def test_summary_prompt(conversation_id, version_func):
    """Test a summary prompt on a specific conversation"""
    try:
        conversation = Conversation.objects.get(id=conversation_id)
        print(f"\n{'='*80}")
        print(f"Testing Conversation {conversation_id}")
        print(f"User: {conversation.user.email}")
        print(f"Messages: {conversation.messages.count()}")
        print(f"{'='*80}")

        # Show the conversation
        print("\n📝 CONVERSATION:")
        print("-" * 80)
        for msg in conversation.messages.all().order_by('created_at'):
            role = "👤 User" if msg.role == 'user' else "🤖 AI"
            content = msg.content[:200] + "..." if len(msg.content) > 200 else msg.content
            print(f"\n{role}:")
            print(f"  {content}")

        # Generate prompt
        prompt, version_name = version_func(conversation)

        print(f"\n\n🔧 PROMPT ({version_name}):")
        print("-" * 80)
        print(prompt)

        # Get AI response
        print(f"\n\n🤖 GENERATING SUMMARY...")
        gemini = GeminiService()
        response = gemini.generate_simple_response(prompt)

        print(f"\n✅ AI RESPONSE:")
        print("-" * 80)
        print(response)

        # For v2 and v3 (plain text), just return the response
        if version_name in ['v2_user_focused', 'v3_ultra_concise']:
            print(f"\n📊 SUMMARY (Plain Text):")
            print("-" * 80)
            print(response.strip())
            return {'summary': response.strip()}

        # For v1 (JSON), try to parse
        try:
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                summary_data = json.loads(json_match.group(1))
            else:
                summary_data = json.loads(response)

            print(f"\n📊 PARSED SUMMARY:")
            print("-" * 80)
            print(json.dumps(summary_data, indent=2))

            return summary_data

        except Exception as e:
            print(f"\n❌ Failed to parse JSON: {e}")
            print(f"\n📊 USING AS PLAIN TEXT:")
            print("-" * 80)
            print(response.strip())
            return {'summary': response.strip()}

    except Conversation.DoesNotExist:
        print(f"❌ Conversation {conversation_id} not found")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def compare_all_versions(conversation_id):
    """Compare all prompt versions side-by-side"""
    print(f"\n{'='*80}")
    print(f"COMPARING ALL VERSIONS FOR CONVERSATION {conversation_id}")
    print(f"{'='*80}")

    versions = [
        ("v1: Interpretation Focused", create_chat_summary_v1),
        ("v2: User Focused", create_chat_summary_v2),
        ("v3: Ultra Concise", create_chat_summary_v3),
    ]

    results = {}

    for name, func in versions:
        print(f"\n\n{'#'*80}")
        print(f"# {name}")
        print(f"{'#'*80}")
        result = test_summary_prompt(conversation_id, func)
        results[name] = result

    return results


def main():
    """Main test runner"""
    print("""
╔═══════════════════════════════════════════════════════════════════════════╗
║                   CHAT SUMMARY PROMPT TESTER                              ║
╚═══════════════════════════════════════════════════════════════════════════╝

This script helps you test different summary prompt versions.
    """)

    # Find some test conversations
    print("Finding test conversations...")
    conversations = Conversation.objects.filter(
        messages__isnull=False
    ).distinct()[:5]

    if not conversations.exists():
        print("❌ No conversations found")
        return

    print(f"\n✅ Found {conversations.count()} conversations:")
    for i, conv in enumerate(conversations, 1):
        msg_count = conv.messages.count()
        print(f"  {i}. ID {conv.id}: {conv.user.email} ({msg_count} messages)")

    # Ask user to select
    print("\nOptions:")
    print("  - Enter a conversation ID to test")
    print("  - Enter 'compare <id>' to compare all versions")
    print("  - Enter 'quit' to exit")

    while True:
        try:
            choice = input("\n> ").strip().lower()

            if choice == 'quit':
                break

            if choice.startswith('compare '):
                conv_id = int(choice.split()[1])
                compare_all_versions(conv_id)
            else:
                conv_id = int(choice)

                print("\nSelect version:")
                print("  1. v1: Interpretation Focused (OLD)")
                print("  2. v2: User Focused (NEW)")
                print("  3. v3: Ultra Concise")

                version = input("Version (1-3): ").strip()

                version_map = {
                    '1': create_chat_summary_v1,
                    '2': create_chat_summary_v2,
                    '3': create_chat_summary_v3,
                }

                if version in version_map:
                    test_summary_prompt(conv_id, version_map[version])
                else:
                    print("Invalid version")

        except ValueError:
            print("Invalid input. Please enter a number or 'quit'")
        except KeyboardInterrupt:
            print("\n\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == '__main__':
    main()
