#!/usr/bin/env python3
"""
Test script to simulate the !ask command functionality
"""
import asyncio
import aiohttp
import logging
import re

# Set up logging like in the IRC client
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
LOG = logging.getLogger(__name__)

def strip_markdown(text: str) -> str:
    """Remove markdown formatting for Twitch chat compatibility."""
    
    # Remove bold/italic markers
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # **bold**
    text = re.sub(r'\*([^*]+)\*', r'\1', text)      # *italic*
    text = re.sub(r'__([^_]+)__', r'\1', text)      # __bold__
    text = re.sub(r'_([^_]+)_', r'\1', text)        # _italic_
    
    # Remove code blocks and inline code
    text = re.sub(r'```[^`]*```', '', text)         # ```code blocks```
    text = re.sub(r'`([^`]+)`', r'\1', text)        # `inline code`
    
    # Remove links but keep the text
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)  # [text](url)
    text = re.sub(r'<([^>]+)>', r'\1', text)              # <url>
    
    # Remove headers
    text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
    
    # Remove bullet points and numbering
    text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)
    
    # Clean up extra whitespace
    text = re.sub(r'\n\s*\n', ' ', text)  # Multiple newlines to single space
    text = re.sub(r'\s+', ' ', text)      # Multiple spaces to single space
    
    return text.strip()

async def simulate_ask_command(message: str, username: str = "testuser"):
    """Simulate the !ask command processing"""
    print(f"Input message: '{message}'")
    
    # Test the message parsing logic from _cmd_ask
    question = message[4:].strip() if len(message) > 4 else ""
    print(f"Extracted question: '{question}'")
    
    if not question:
        print("❌ Please provide a question after !ask")
        return
    
    # Test the async chat request (similar to _handle_chat_request)
    print(f"Making API request for user: {username}")
    await test_chat_request(question, username)

async def test_chat_request(question: str, username: str):
    """Test the chat API request"""
    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "message": question,
                "search_mode": "hybrid",
                "n_results": 3
            }
            print(f"API payload: {payload}")
            
            async with session.post(
                "http://localhost:8000/chat",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                print(f"API response status: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    raw_answer = data.get("response", "No response received")
                    print(f"Raw API response: {raw_answer}")
                    # Strip markdown formatting for Twitch chat compatibility
                    answer = strip_markdown(raw_answer)
                    print(f"Cleaned response: {answer}")
                    # This would be sent to Twitch chat
                    chat_message = f"@{username} {answer}"
                    print(f"Would send to chat: {chat_message}")
                else:
                    error_msg = f"@{username} ❌ API error: {response.status}"
                    print(f"Would send error to chat: {error_msg}")
                    
    except aiohttp.ClientError as e:
        error_msg = f"Chat API request failed: {e}"
        LOG.error(error_msg)
        print(f"Would send to chat: @{username} ❌ Failed to connect to chat API")
    except Exception as e:
        error_msg = f"Unexpected error in chat request: {e}"
        LOG.error(error_msg)
        print(f"Would send to chat: @{username} ❌ An error occurred")

def test_markdown_stripping():
    """Test markdown stripping functionality"""
    print("=== Testing Markdown Stripping ===\n")
    
    test_cases = [
        "**Achilles** is a *warrior* god in Smite2.",
        "His ultimate ability is `Shield of Achilles`.",
        "Here's a [link](https://example.com) to more info.",
        "## God Abilities\n- Ultimate: Shield of Achilles\n- Basic: Spear Thrust",
        "```python\nprint('hello')\n``` Use this `code` for testing.",
        "1. First ability\n2. Second ability\n\n3. Third ability",
        "_Italic text_ and __bold text__ here.",
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}:")
        print(f"  Original: {repr(test_case)}")
        stripped = strip_markdown(test_case)
        print(f"  Stripped: {repr(stripped)}")
        print()

async def main():
    """Test various !ask command scenarios"""
    # First test markdown stripping
    test_markdown_stripping()
    
    print("=== Testing !ask command scenarios ===\n")
    
    # Test cases
    test_cases = [
        "!ask What is Achilles ultimate ability?",
        "!ask",  # Empty question
        "!ask Who is the best Smite god?",
        "!askWhat happens without space?",  # Edge case
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"--- Test Case {i} ---")
        await simulate_ask_command(test_case)
        print()

if __name__ == "__main__":
    asyncio.run(main())