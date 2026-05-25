"""Main CLI entry point for the AI Agent Debate System.

Usage:
    uv run python src/main.py --topic "Is AI good for humanity?"
    uv run python src/main.py --topic "..." --rounds 5
    uv run python src/main.py --topic "..." --config path/to/config/
"""

from __future__ import annotations

import argparse
import sys

from dotenv import load_dotenv


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Run an AI agent debate on a given topic."
    )
    parser.add_argument(
        "--topic",
        type=str,
        required=True,
        help="The debate topic (e.g., 'Is AI good for humanity?')",
    )
    parser.add_argument(
        "--rounds",
        type=int,
        default=None,
        help="Number of debate rounds (default: from config)",
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config",
        help="Path to config directory (default: config/)",
    )
    return parser.parse_args()


def main() -> int:
    """Run the debate and print the verdict."""
    load_dotenv()
    args = parse_args()

    try:
        from debate.sdk.sdk import DebateSDK

        sdk = DebateSDK(config_path=args.config)
        verdict = sdk.run_debate(topic=args.topic, rounds=args.rounds)

        print("\n" + "=" * 60)
        print("DEBATE VERDICT")
        print("=" * 60)
        print(f"Topic:  {args.topic}")
        print(f"Winner: {verdict['winner'].upper()}")
        print(f"Score:  Pro {verdict['score']['pro']} — Con {verdict['score']['con']}")
        print(f"\nReasoning:\n{verdict['reasoning']}")
        print("=" * 60)

        cost = sdk.get_cost_report()
        print("\nCOST REPORT")
        print("-" * 40)
        print(f"Input tokens:     {cost['total_input_tokens']:,}")
        print(f"Output tokens:    {cost['total_output_tokens']:,}")
        print(f"Total cost:       ${cost['total_cost_usd']:.4f}")
        print(f"Budget remaining: ${cost['budget_remaining_usd']:.4f}")
        print(f"Log file:         {sdk.get_log_path()}")

        sdk.close()
        return 0

    except KeyboardInterrupt:
        print("\nDebate interrupted by user.")
        return 1
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
