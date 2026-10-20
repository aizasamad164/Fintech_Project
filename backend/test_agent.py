# backend/test_agent.py
import asyncio
import os
import time
import warnings
from dotenv import load_dotenv

# Permanently suppress sklearn/numpy feature validation warnings in CLI runner
warnings.filterwarnings("ignore")

load_dotenv()

from app.llm.agent import run_investment_agent

async def main():
    if not os.getenv("GROQ_API_KEY"):
        print("❌ ERROR: GROQ_API_KEY is not set in backend/.env file.")
        return

    print("==================================================")
    print("      AI INVESTMENT AGENT INTERACTIVE TEST        ")
    print("==================================================\n")

    # 1. Interactive Inputs
    try:
        amount_input = input("1. Enter Portfolio Amount ($) [Default 10000]: ").strip()
        portfolio_amount = float(amount_input) if amount_input else 10000.0

        print("\nSectors: Technology | Healthcare | Pharmaceuticals | Renewable_Energy | General | All")
        sector_input = input("2. Enter Target Sector [Default 'All']: ").strip()
        target_sector = sector_input if sector_input else "All"

        print("\nApproaches: Conservative Risk-Managed | Aggressive Growth | High Conviction ML | Balanced")
        approach_input = input("3. Enter Investment Approach [Default 'Balanced']: ").strip()
        approach = approach_input if approach_input else "Balanced"

    except ValueError:
        print("⚠️ Invalid numerical amount entered. Defaulting to $10,000.")
        portfolio_amount = 10000.0
        target_sector = "All"
        approach = "Balanced"

    # 2. Dynamic Prompt Construction
    user_prompt = (
        f"I want to allocate a ${portfolio_amount:,.2f} portfolio. "
        f"Target Sector Focus: '{target_sector}'. "
        f"Investment Strategy / Approach: '{approach}'. "
        f"Please perform portfolio rebalancing/optimization for this amount and explain the results. "
        f"Justify why this specific allocation fits my chosen strategy, referencing the ML model "
        f"signals, risk caps, and market metrics."
    )

    print("\n--------------------------------------------------")
    print(f"🤖 Constructed Prompt:\n\"{user_prompt}\"")
    print("--------------------------------------------------")
    print("-> Executing AI agent reasoning loop...\n")

    session_id = f"cli_test_session_{int(time.time())}"

    start_time = time.time()
    response = await run_investment_agent(
        session_id=session_id,
        user_message=user_prompt
    )
    elapsed = round(time.time() - start_time, 2)

    # 3. Log Tool Execution Summary
    print(f"--- Tools Executed ({len(response.get('tool_calls_executed', []))}) [Execution Time: {elapsed}s] ---")
    if response.get("tool_calls_executed"):
        for tool in response["tool_calls_executed"]:
            print(f"  • Function: {tool['tool_name']}")
            print(f"    Args:     {tool['arguments']}")
            print(f"    Output:   {str(tool['result'])[:160]}...\n")
    else:
        print("  • No tools executed.\n")

    # 4. Display Agent Response & Justification
    print("--- Agent Response & Justification Strategy ---")
    print(response.get("content", "No response generated."))
    print("\n" + "="*50 + "\n")

if __name__ == "__main__":
    asyncio.run(main())