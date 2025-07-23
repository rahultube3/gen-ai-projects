import asyncio
import sys

from dotenv import load_dotenv
from langchain_groq import ChatGroq

from mcp_use import MCPAgent, MCPClient
import os
import logging

logging.basicConfig(level=logging.INFO)

async def run_demo_queries():
    """Run some demo queries to test the MCP weather server."""
    # Load environment variables for API keys
    load_dotenv()
    os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")

    # Config file path
    config_file = "weather.json"

    logging.info("🌦️  MCP Weather Server Demo")
    logging.info("=" * 40)

    try:
        # Create MCP client and agent
        logging.info("Initializing MCP client...")
        client = MCPClient.from_config_file(config_file)
        llm = ChatGroq(model="llama-3.1-8b-instant")
        agent = MCPAgent(
            llm=llm,
            client=client,
            max_steps=10,
            memory_enabled=True,
        )

        # Demo queries
        demo_queries = [
            "What are the current weather alerts for California?",
            "What's the weather forecast for San Francisco? Use coordinates 37.7749, -122.4194",
            "Show me the cached weather report for New York",
            "What weather risks should I know about for Texas?"
        ]

        for i, query in enumerate(demo_queries, 1):
            logging.info(f"\n--- Demo Query {i} ---")
            logging.info(f"Question: {query}")
            print("Answer: ", end="", flush=True)

            try:
                response = await agent.run(query)
                print(response)
            except Exception as e:
                logging.error(f"Error: {e}")
            
            # Small delay between queries
            await asyncio.sleep(1)

        logging.info("\n🎉 Demo completed successfully!")
        return True

    except Exception as e:
        logging.error(f"❌ Demo failed: {e}")
        return False

    finally:
        # Clean up
        if 'client' in locals() and client and hasattr(client, 'sessions'):
            try:
                await client.close_all_sessions()
            except:
                pass

async def run_interactive_chat():
    """Run an interactive chat using MCPAgent's built-in conversation memory."""
    # Load environment variables for API keys
    load_dotenv()
    os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")

    # Config file path
    config_file = "weather.json"

    logging.info("🌦️  MCP Weather Interactive Chat")
    logging.info("=" * 40)

    try:
        # Create MCP client and agent with memory enabled
        logging.info("Initializing chat...")
        client = MCPClient.from_config_file(config_file)
        llm = ChatGroq(model="llama-3.1-8b-instant")

        # Create agent with memory_enabled=True
        agent = MCPAgent(
            llm=llm,
            client=client,
            max_steps=15,
            memory_enabled=True,  # Enable built-in conversation memory
        )

        logging.info("\n===== Interactive MCP Weather Chat =====")
        logging.info("Available commands:")
        logging.info("• 'exit' or 'quit' - End the conversation")
        logging.info("• 'clear' - Clear conversation history")
        logging.info("• 'demo' - Run demo queries")
        logging.info("• 'help' - Show weather capabilities")
        logging.info("\nExample queries:")
        logging.info("• What are the weather alerts for Florida?")
        logging.info("• Get forecast for Miami (25.7617, -80.1918)")
        logging.info("• Show weather report for Chicago")
        logging.info("=" * 43)

        # Main chat loop
        while True:
            # Get user input
            user_input = input("\n🌦️  You: ")

            # Check for exit command
            if user_input.lower() in ["exit", "quit"]:
                logging.info("👋 Ending conversation...")
                break

            # Check for clear history command
            if user_input.lower() == "clear":
                agent.clear_conversation_history()
                logging.info("🧹 Conversation history cleared.")
                continue

            # Check for demo command
            if user_input.lower() == "demo":
                logging.info("\n🎬 Running demo queries...")
                await run_demo_queries()
                continue

            # Check for help command
            if user_input.lower() == "help":
                logging.info("\n📚 MCP Weather Server Capabilities:")
                logging.info("🛠️  Tools:")
                logging.info("  • get_alerts(state) - Get active weather alerts")
                logging.info("  • get_forecast(lat, lon) - Get weather forecast")
                logging.info("📚 Resources:")
                logging.info("  • weather://reports/san-francisco")
                logging.info("  • weather://reports/new-york")
                logging.info("  • weather://reports/chicago")
                logging.info("  • weather://alerts/ca, ny, fl, tx, il")
                logging.info("💭 Prompts:")
                logging.info("  • weather-alert-analysis")
                logging.info("  • weather-safety-guide")
                continue

            # Get response from agent
            print("🤖 Assistant: ", end="", flush=True)

            try:
                # Run the agent with the user input
                response = await agent.run(user_input)
                print(response)

            except Exception as e:
                logging.error(f"\n❌ Error: {e}")

    except Exception as e:
        logging.error(f"❌ Failed to initialize chat: {e}")

    finally:
        # Clean up
        if 'client' in locals() and client and hasattr(client, 'sessions'):
            try:
                await client.close_all_sessions()
            except:
                pass

async def main():
    """Main function to choose between demo and interactive mode."""
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        await run_demo_queries()
    else:
        await run_interactive_chat()

if __name__ == "__main__":
    asyncio.run(main())