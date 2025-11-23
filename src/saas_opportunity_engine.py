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

def main() -> None:
    parser = argparse.ArgumentParser(description="Run the micro‑SaaS opportunity engine")
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
            "Optional path to a JSON file mapping idea titles to user ratings (0–5). "
            "These ratings adjust the total scores during ranking."
        ),
        default=None,
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
        help="Optional path to a JSON or YAML file that lists source_urls and min_credibility.",
        default=None,
    )
    parser.add_argument(
        "--min-credibility",
        dest="min_credibility",
        help="Minimum credibility label (low|medium|high) to include scraped ideas.",
        default=None,
    )
    parser.add_argument(
        "--rate",
        action="store_true",
        help="Interactively rate the top ideas.",
    )
    args = parser.parse_args()
    urls_list = args.urls.split(",") if args.urls else None
    engine = OpportunityEngine(
        theme=args.theme,
        dataset_path=args.dataset_path,
        feedback_path=args.feedback_path,
        urls=urls_list,
        config_path=args.config_path,
        min_credibility=args.min_credibility,
    )
    
    if args.rate:
        print("Running engine to generate ideas for rating...")
        # Run one iteration to get ideas
        ideas = engine.generate_opportunities()
        # Sort by total score
        ideas.sort(key=lambda i: i.scores.total.value, reverse=True)
        
        print(f"\nTop {min(5, len(ideas))} ideas to rate:")
        for i, idea in enumerate(ideas[:5]):
            print(f"\n{i+1}. {idea.title}")
            print(f"   Solution: {idea.solution}")
            print(f"   Current Score: {idea.final_total}")
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
        
        save_path = args.feedback_path or "data/user_feedback.json"
        engine.feedback_manager.save_feedback(save_path)
        print(f"\nFeedback saved to {save_path}")
        print("Re-run without --rate to see adjusted scores.")
    else:
        engine.run()


if __name__ == "__main__":
    main()