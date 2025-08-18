#!/bin/bash

# Test CLI functionality by running the langchain agent directly
echo "🧪 Testing LangChain CLI Integration"
echo "===================================="

# Set up environment
export OPENAI_API_KEY="${OPENAI_API_KEY}"
export MONGODB_URI="${MONGODB_URI:-mongodb://localhost:27017/ecommerce_assistant}"

echo "✅ Environment configured"
echo "✅ Testing LangChain Agent with direct message..."

# Test the agent with a simple message
cd "$(dirname "$0")"

python3 -c "
import asyncio
import sys
import os
sys.path.append('.')

from langchain_agent import EcommerceAgent

async def test_agent():
    try:
        # Create agent
        agent = EcommerceAgent(os.getenv('OPENAI_API_KEY'))
        print('✅ Agent created successfully')
        
        # Test with a simple message
        print('🔍 Testing product search...')
        response = await agent.chat('Find me electronics', 'test_user')
        print(f'🤖 Agent Response: {response}')
        
        print('✅ CLI integration test completed successfully!')
        
    except Exception as e:
        print(f'❌ Error: {e}')
        return False
    
    return True

# Run the test
success = asyncio.run(test_agent())
exit(0 if success else 1)
"

echo "🎉 CLI Test Completed!"
