import asyncio
import sys

from dotenv import load_dotenv
from langchain_groq import ChatGroq

from mcp_use import MCPAgent, MCPClient
import os
import logging

logging.basicConfig(level=logging.INFO)

async def run_demo_queries():
    """Run some demo queries to test the MCP fraud detection server."""
    # Load environment variables for API keys
    load_dotenv()
    os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")

    # Config file path - use relative path to fraud.json in same directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_file = os.path.join(script_dir, "fraud.json")

    logging.info("🏦 MCP Banking Fraud Detection Demo")
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
            "Check if transaction txn001 is fraudulent",
            "Analyze the fraud risk for transaction txn001 and explain the reasoning",
            "What's the fraud score for transaction txn001?",
            "Is transaction nonexistent_txn suspicious?"
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

    # Config file path - use relative path to fraud.json in same directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_file = os.path.join(script_dir, "fraud.json")

    logging.info("🏦 MCP Banking Fraud Interactive Chat")
    logging.info("=" * 40)

    try:
        # Create MCP client and agent with memory enabled
        logging.info("Initializing fraud detection chat...")
        client = MCPClient.from_config_file(config_file)
        llm = ChatGroq(model="llama-3.1-8b-instant")

        # Create agent with memory_enabled=True
        agent = MCPAgent(
            llm=llm,
            client=client,
            max_steps=15,
            memory_enabled=True,  # Enable built-in conversation memory
        )

        logging.info("\n===== Interactive MCP Fraud Detection Chat =====")
        logging.info("Available commands:")
        logging.info("• 'exit' or 'quit' - End the conversation")
        logging.info("• 'clear' - Clear conversation history")
        logging.info("• 'demo' - Run demo queries")
        logging.info("• 'help' - Show fraud detection capabilities")
        logging.info("\nExample queries:")
        logging.info("• Check transaction txn001 for fraud")
        logging.info("• What's the fraud score for txn001?")
        logging.info("• Analyze the risk factors for this transaction")
        logging.info("• Is transaction ID abc123 suspicious?")
        logging.info("=" * 49)

        # Main chat loop
        while True:
            # Get user input
            user_input = input("\n🏦 You: ")

            # Check for exit command
            if user_input.lower() in ["exit", "quit"]:
                logging.info("👋 Ending fraud detection session...")
                break

            # Check for clear history command
            if user_input.lower() == "clear":
                agent.clear_conversation_history()
                logging.info("🧹 Conversation history cleared.")
                continue

            # Check for demo command
            if user_input.lower() == "demo":
                logging.info("\n🎬 Running fraud detection demo...")
                await run_demo_queries()
                continue

            # Check for help command
            if user_input.lower() == "help":
                logging.info("\n📚 MCP Banking Fraud Detection Capabilities:")
                logging.info("🛠️  Tools:")
                logging.info("  • check_fraud(txn_id) - Analyze transaction for fraud")
                logging.info("\n📊 Available Data:")
                logging.info("  • Customer profiles with risk scores")
                logging.info("  • Transaction history and patterns")
                logging.info("  • Location-based risk analysis")
                logging.info("  • Amount-based risk scoring")
                logging.info("\n🔍 Risk Factors:")
                logging.info("  • High transaction amounts (>$3000)")
                logging.info("  • Unfamiliar transaction locations")
                logging.info("  • Customer historical risk profile")
                logging.info("\n💡 Sample Transaction IDs to test:")
                logging.info("  • txn001 (Known high-risk transaction)")
                continue

            # Get response from agent
            print("🤖 Fraud Analyst: ", end="", flush=True)

            try:
                # Run the agent with the user input
                response = await agent.run(user_input)
                print(response)

            except Exception as e:
                logging.error(f"\n❌ Error: {e}")

    except Exception as e:
        logging.error(f"❌ Failed to initialize fraud detection chat: {e}")

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
