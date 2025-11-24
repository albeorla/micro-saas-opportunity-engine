"""
Micro‑SaaS Opportunity Engine CLI
=================================

This module wires the OpportunityEngine into a small command‑line
interface with two subcommands:

* ``run`` (default): generate and score opportunities.
* ``rate``: list the top ideas and capture 0–5 user ratings that are
  persisted to a feedback file.
"""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from src.engine import (
    OpportunityEngine,
    export_ranked_ideas_csv,
    export_ranked_ideas_markdown,
    format_ranked_table,
)


DEFAULT_FEEDBACK_PATH = "data/user_feedback.json"


def _add_common_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "theme",
        help=(
            "A high level theme or domain for the search (currently unused, "
            "but required for forward compatibility)."
        ),
    )
    parser.add_argument(
        "--feedback",
        dest="feedback_path",
        help=(
            "Path to a JSON file mapping idea titles to user ratings (0–5). "
            "These ratings adjust the total scores during ranking."
        ),
        default=DEFAULT_FEEDBACK_PATH,
    )
    parser.add_argument(
        "--dataset",
        dest="dataset_path",
        help=(
            "Optional path to a JSON file containing an array of idea objects. "
            "If not provided, a built‑in sample dataset is used."
        ),
        default=None,
    )
    parser.add_argument(
        "--urls",
        dest="urls",
        help="Optional comma-separated list of URLs to scrape for ideas.",
        default=None,
    )
    parser.add_argument(
        "--config",
        dest="config_path",
        help=(
            "Optional JSON/YAML file for the Researcher (supports source_urls and min_credibility). "
            "Falls back to built-in defaults when omitted."
        ),
        default=None,
    )
    parser.add_argument(
        "--min-credibility",
        dest="min_credibility",
        help="Minimum credibility label (low|medium|high) to include scraped ideas.",
        default=None,
    )


def _build_engine(args: argparse.Namespace) -> OpportunityEngine:
    urls_list: Optional[List[str]] = args.urls.split(",") if args.urls else None
    return OpportunityEngine(
        theme=args.theme,
        dataset_path=args.dataset_path,
        feedback_path=args.feedback_path,
        urls=urls_list,
        config_path=args.config_path,
        min_credibility=args.min_credibility,
    )


def rate_ideas(args: argparse.Namespace) -> None:
    engine = _build_engine(args)
    print("Running engine to generate ideas for rating...")
    ideas = engine.generate_opportunities()
    ideas.sort(key=lambda i: i.final_total, reverse=True)

    top_n = getattr(args, "top", 5)
    _prompt_for_ratings(engine, ideas, top_n, args.feedback_path)
    print("Re-run the engine to see adjusted rankings.")


def _prompt_for_ratings(
    engine: OpportunityEngine, ideas: List, top_n: int, feedback_path: str
) -> None:
    updated = False
    print(f"\nTop {min(top_n, len(ideas))} ideas to rate (scores include existing feedback):")
    for i, idea in enumerate(ideas[:top_n]):
        print(f"\n{i+1}. {idea.title}")
        print(f"   Solution: {idea.solution}")
        print(f"   Current Adjusted Score: {int(round(idea.final_total))}/{idea.scores.total.max}")
        while True:
            rating_input = input("   Rate this idea (0-5) or [Enter] to skip: ").strip()
            if not rating_input:
                break
            try:
                rating = float(rating_input)
                if 0 <= rating <= 5:
                    engine.feedback_manager.add_rating(idea.title, rating)
                    updated = True
                    print(f"   Recorded rating: {rating}")
                    break
                else:
                    print("   Please enter a number between 0 and 5.")
            except ValueError:
                print("   Invalid input.")

    if updated:
        engine.feedback_manager.save_feedback(feedback_path)
        print(f"\nFeedback saved to {feedback_path}")


def _parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the micro‑SaaS opportunity engine")
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run", help="Generate and score opportunities (default)")
    _add_common_arguments(run_parser)
    run_parser.add_argument(
        "--rate-top",
        type=int,
        default=5,
        help="Rate the top N ideas inline after running (default: 5). Use 0 to skip rating prompts.",
    )
    run_parser.add_argument(
        "--export-csv",
        dest="export_csv",
        default=None,
        help="Optional path to export ranked ideas as CSV.",
    )
    run_parser.add_argument(
        "--export-md",
        dest="export_md",
        default=None,
        help="Optional path to export ranked ideas as a Markdown table.",
    )

    rate_parser = subparsers.add_parser("rate", help="List top ideas and capture user ratings")
    _add_common_arguments(rate_parser)
    rate_parser.add_argument(
        "--top",
        type=int,
        default=5,
        help="Number of ideas to show for rating (default: 5)",
    )

    parser.set_defaults(command="run")

    raw_args = argv if argv is not None else sys.argv[1:]
    # Allow calling the script without explicitly specifying the "run" subcommand.
    if raw_args and raw_args[0] not in {"run", "rate"} and not raw_args[0].startswith("-"):
        raw_args = ["run", *raw_args]
    return parser.parse_args(raw_args)


def main() -> None:
    args = _parse_args()
    if args.command == "rate":
        rate_ideas(args)
    else:
        engine = _build_engine(args)
        ideas = engine.run()
        print("\nRanked opportunities:\n")
        print(format_ranked_table(ideas))
        print("\nCritic adjustments (delta: reason):")
        for idea in ideas:
            rationale = idea.critic_rationale or "no credibility signals"
            print(f"- {idea.title}: {idea.critic_adjustment:+} ({rationale})")

        top_to_rate = getattr(args, "rate_top", 0)
        if top_to_rate > 0:
            _prompt_for_ratings(engine, ideas, top_to_rate, args.feedback_path)

        if args.export_csv:
            export_ranked_ideas_csv(args.export_csv, ideas)
            print(f"\nExported ranked ideas to CSV at {args.export_csv}")
        if args.export_md:
            export_ranked_ideas_markdown(args.export_md, ideas)
            print(f"Exported ranked ideas to Markdown at {args.export_md}")


if __name__ == "__main__":
    main()
