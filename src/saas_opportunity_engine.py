"""
Micro‑SaaS Opportunity Engine
==============================

This module implements a simplified version of the micro‑SaaS opportunity
engine described in the product requirement document.  The goal of this
MVP is to demonstrate the core architecture and scoring logic using a
small, preloaded dataset of opportunity ideas.  In a full implementation,
the ``IdeaGenerator`` would retrieve data from web searches and other
sources, and the scoring functions would be informed by evidence and
structured user feedback.  For this minimal version, we define a few
example ideas directly in code and compute heuristic scores.

The engine is orchestrated by the ``OpportunityEngine`` class, which
combines a simple planner, idea generator, scoring engine and
recommendation system.  When run from the command line this script
accepts a ``theme`` argument (e.g. "micro saas for smb bookkeeping") and
prints the resulting opportunity briefs to stdout.

Usage
-----

To run the engine with the built‑in sample data, execute the module as a
script:

.. code:: bash

   python src/saas_opportunity_engine.py "micro saas for SMBs"

This will print a table of ideas with their scores and final
recommendations.
"""

import argparse

from src.engine import OpportunityEngine


DEFAULT_FEEDBACK_PATH = "data/user_feedback.json"


def _add_common_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "theme",
        help=(
            "A high level theme or domain for the search (currently unused, "
            "but required for forward compatibility)"
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


def _build_engine(args: argparse.Namespace) -> OpportunityEngine:
    urls_list = args.urls.split(",") if args.urls else None
    return OpportunityEngine(
        theme=args.theme,
        dataset_path=args.dataset_path,
        feedback_path=args.feedback_path,
        urls=urls_list,
    )


def rate_ideas(args: argparse.Namespace) -> None:
    engine = _build_engine(args)
    print("Running engine to generate ideas for rating...")
    ideas = engine.generate_opportunities()
    ideas.sort(key=lambda i: i.final_total, reverse=True)

    top_n = getattr(args, "top", 5)
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
                    print(f"   Recorded rating: {rating}")
                    break
                else:
                    print("   Please enter a number between 0 and 5.")
            except ValueError:
                print("   Invalid input.")

    engine.feedback_manager.save_feedback(args.feedback_path)
    print(f"\nFeedback saved to {args.feedback_path}")
    print("Re-run the engine to see adjusted rankings.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the micro‑SaaS opportunity engine")
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run", help="Generate and score opportunities (default)")
    _add_common_arguments(run_parser)

    rate_parser = subparsers.add_parser("rate", help="List top ideas and capture user ratings")
    _add_common_arguments(rate_parser)
    rate_parser.add_argument(
        "--top",
        type=int,
        default=5,
        help="Number of ideas to show for rating (default: 5)",
    )

    args = parser.parse_args()
    if args.command is None:
        args.command = "run"

    if args.command == "rate":
        rate_ideas(args)
    else:
        engine = _build_engine(args)
        engine.run()


if __name__ == "__main__":
    main()
