from typing import List, Dict, Optional, Tuple
import csv
import json
from pathlib import Path
from src.models import Idea, IdeaScores
from src.scoring import ScoringEngine
from src.researcher import Researcher
from src.critic import Critic
from src.feedback import UserFeedbackManager

TABLE_HEADERS = [
    "Title",
    "ICP",
    "Pain",
    "Solution",
    "Revenue Model",
    "Demand",
    "Acquisition",
    "MVP Complexity",
    "Competition",
    "Revenue Velocity",
    "Total",
    "Recommendation",
    "Key Risks",
]

HEADER_TO_KEY = {
    "Title": "title",
    "ICP": "icp",
    "Pain": "pain",
    "Solution": "solution",
    "Revenue Model": "revenue_model",
    "Demand": "demand_score",
    "Acquisition": "acquisition_score",
    "MVP Complexity": "mvp_complexity_score",
    "Competition": "competition_score",
    "Revenue Velocity": "revenue_velocity_score",
    "Total": "total_score",
    "Recommendation": "recommendation",
    "Key Risks": "key_risks",
}


def _ranked_rows(ideas: List[Idea]) -> Tuple[List[str], List[Dict[str, str]]]:
    """Return ordered headers and row dictionaries for ranked ideas."""

    rows: List[Dict[str, str]] = []
    for idea in ideas:
        record = idea.as_dict()
        rows.append({header: str(record[HEADER_TO_KEY[header]]) for header in TABLE_HEADERS})
    return TABLE_HEADERS, rows


def format_ranked_table(ideas: List[Idea], clip_width: int = 60) -> str:
    """Render ranked ideas as a fixed-width table for console output."""

    headers, rows = _ranked_rows(ideas)
    column_widths: Dict[str, int] = {h: len(h) for h in headers}
    for row in rows:
        for header in headers:
            value = str(row[header])
            if len(value) > column_widths[header]:
                column_widths[header] = len(value)

    header_line = " | ".join(h.ljust(column_widths[h]) for h in headers)
    separator = "-" * len(header_line)
    output_lines = [header_line, separator]
    for row in rows:
        clipped_values = [
            (value[: clip_width - 3] + "..." if len(value) > clip_width else value)
            for value in (row[h] for h in headers)
        ]
        output_lines.append(
            " | ".join(
                clipped_values[idx].ljust(column_widths[headers[idx]]) for idx in range(len(headers))
            )
        )
    return "\n".join(output_lines)


def export_ranked_ideas_csv(path: str, ideas: List[Idea]) -> None:
    """Write ranked ideas to a CSV file in table order."""

    headers, rows = _ranked_rows(ideas)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def export_ranked_ideas_markdown(path: str, ideas: List[Idea]) -> None:
    """Write ranked ideas to a Markdown table."""

    headers, rows = _ranked_rows(ideas)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    header_line = " | ".join(headers)
    separator_line = " | ".join(["---"] * len(headers))
    table_lines = [header_line, separator_line]
    for row in rows:
        table_lines.append(" | ".join(row[h] for h in headers))
    target.write_text("\n".join(table_lines), encoding="utf-8")

class OpportunityEngine:
    """Orchestrates the generation, scoring, critique and recommendation of ideas."""

    def __init__(
        self,
        theme: str,
        dataset_path: Optional[str] = None,
        feedback_path: Optional[str] = None,
        urls: Optional[List[str]] = None,
        config_path: Optional[str] = None,
        min_credibility: Optional[str] = None,
    ) -> None:
        """
        Create a new opportunity engine.

        Parameters
        ----------
        theme: str
            A high level theme or domain for the search.
        dataset_path: Optional[str]
            Path to a JSON file containing an array of idea objects.
        feedback_path: Optional[str]
            Path to a JSON file containing user feedback.
        urls: Optional[List[str]]
            List of URLs to scrape for additional ideas.
        """
        self.theme = theme
        self.scoring_engine = ScoringEngine()
        self.researcher = Researcher(urls=urls, config_path=config_path, min_credibility=min_credibility)
        # Components for critique and feedback
        self.critic = Critic()
        self.feedback_manager = UserFeedbackManager(feedback_path)
        # Determine dataset source
        if dataset_path:
            try:
                self.idea_dataset = self._load_dataset_from_file(dataset_path)
            except Exception as exc:
                raise ValueError(f"Failed to load dataset from {dataset_path}: {exc}")
        else:
            # Load the static dataset of ideas. In a real system this could
            # come from web scraping, API calls or a database.
            self.idea_dataset = self._load_static_dataset()

    def _run_iteration(self) -> List[Idea]:
        """Score the current dataset and produce Idea objects with recommendations.

        Returns
        -------
        List[Idea]
            The list of scored Idea instances.
        """
        results: List[Idea] = []
        for idea_data in self.idea_dataset:
            scores = self.scoring_engine.score_idea(idea_data)
            # Compute credibility and feedback adjustments
            cred_adjust, cred_rationale = self.critic.evaluate_with_rationale(idea_data)
            feedback_adjust = self.feedback_manager.get_adjustment(idea_data.get("title", ""))
            # Adjusted total score (bounded between 0 and max)
            raw_total = scores.total.value
            max_total = scores.total.max
            adjusted_total = raw_total + cred_adjust + feedback_adjust
            if adjusted_total < 0:
                adjusted_total = 0
            if adjusted_total > max_total:
                adjusted_total = max_total
            recommendation = self._recommendation(
                scores,
                adjusted_total,
                positive_external_signal=self._has_positive_external_signal(idea_data),
            )
            results.append(
                Idea(
                    title=idea_data["title"],
                    icp=idea_data["icp"],
                    pain=idea_data["pain"],
                    solution=idea_data["solution"],
                    revenue_model=idea_data["revenue_model"],
                    search_volume=self._safe_int(idea_data.get("search_volume")),
                    keyword_difficulty=self._safe_int(idea_data.get("keyword_difficulty")),
                    trend_status=idea_data.get("trend_status", "Unknown"),
                    evidence=[],
                    scores=scores,
                    recommendation=recommendation,
                    key_risks=idea_data.get("key_risks", []),
                    final_total=adjusted_total,
                    critic_adjustment=cred_adjust,
                    feedback_adjustment=feedback_adjust,
                    critic_rationale=cred_rationale,
                )
            )
        return results

    def refine_dataset(self, scored_ideas: List[Idea]) -> None:
        """Refine the dataset by removing low‑quality ideas and adding new research.

        If there are no green_build recommendations after scoring, this method
        drops ideas with a "red_kill" recommendation and appends new ideas
        from the Researcher to the dataset.  This simulates a basic
        reflexion loop where the system critiques its own output and
        attempts to improve the idea pool.

        Parameters
        ----------
        scored_ideas: List[Idea]
            The ideas produced by the latest scoring iteration.
        """
        # Count how many good (green) ideas exist
        green_count = sum(1 for idea in scored_ideas if idea.recommendation == "green_build")
        if green_count > 0:
            return  # we have at least one strong idea; no refinement needed

        # Identify weakest dimension to target with replacements (demand vs acquisition heuristic)
        def _avg_ratio(dimension: str) -> float:
            return sum(
                getattr(idea.scores, dimension).value / getattr(idea.scores, dimension).max
                for idea in scored_ideas
            ) / max(len(scored_ideas), 1)

        weakest_dimension = "demand" if _avg_ratio("demand") <= _avg_ratio("acquisition") else "acquisition"

        # Remove ideas that are clearly not viable (red_kill) or heavily penalized by the critic
        filtered_dataset = []
        for idea_data, scored in zip(self.idea_dataset, scored_ideas):
            if scored.recommendation == "red_kill":
                continue
            if scored.critic_adjustment <= -5:
                continue
            filtered_dataset.append(idea_data)
        self.idea_dataset = filtered_dataset

        # Add new ideas from researcher
        new_ideas = self.researcher.search_micro_saas_ideas(self.theme)
        # Avoid duplicates by checking titles
        existing_titles = {idea["title"] for idea in self.idea_dataset}
        # Score candidates to prioritize the weakest dimension and overall total
        scored_candidates = []
        for idea in new_ideas:
            if idea["title"] in existing_titles:
                continue
            scores = self.scoring_engine.score_idea(idea)
            scored_candidates.append((idea, scores))

        # Sort by weakest dimension, then total score
        if weakest_dimension == "demand":
            scored_candidates.sort(
                key=lambda pair: (
                    -pair[1].demand.value,
                    -pair[1].total.value,
                )
            )
        else:
            scored_candidates.sort(
                key=lambda pair: (
                    -pair[1].acquisition.value,
                    -pair[1].total.value,
                )
            )

        for idea, _scores in scored_candidates[:3]:
            self.idea_dataset.append(idea)
            existing_titles.add(idea["title"])


    @staticmethod
    def _load_static_dataset() -> List[Dict[str, str]]:
        """Return a list of idea dictionaries for the MVP.

        These examples are adapted from a 2025 article on micro‑SaaS
        opportunities【566476804201456†L100-L124】
        and should be replaced with live data in a full implementation.
        """
        return [
            {
                "title": "AI‑first bookkeeping for SMBs",
                "icp": "Small and medium‑sized businesses (SMBs)",
                "pain": "Manual bookkeeping and costly accountants",
                "solution": "Fully autonomous AI that connects to QuickBooks/Xero and reconciles accounts automatically",
                "revenue_model": "$49–149/month subscription",
                "key_risks": [
                    "Regulatory and compliance requirements for financial data",
                    "Convincing SMB owners to trust AI with sensitive accounting",
                ],
            },
            {
                "title": "AI SaaS for clinical trial management",
                "icp": "Research labs and clinical trial coordinators",
                "pain": "Recruiting, scheduling and compliance remain fragmented and costly",
                "solution": "Micro‑SaaS that manages trial logistics with AI scheduling and automated compliance checks",
                "revenue_model": "$500–2,000/month per lab",
                "key_risks": [
                    "Requires domain expertise and regulatory approval",
                    "Smaller market compared to SMB SaaS, making acquisition harder",
                ],
            },
            {
                "title": "Generative design SaaS for product engineers",
                "icp": "Product engineers and hardware startups",
                "pain": "Traditional 3D design is time‑consuming and expensive",
                "solution": "AI‑powered SaaS that generates product blueprints and CAD files from natural language prompts",
                "revenue_model": "$99–399/month",
                "key_risks": [
                    "Requires sophisticated generative AI models",
                    "Competition from established CAD providers",
                ],
            },
            {
                "title": "ESG compliance SaaS for SMBs",
                "icp": "Small and mid‑sized companies needing sustainability reporting",
                "pain": "SMBs lack resources for ESG reporting and benchmarking",
                "solution": "SaaS that automates ESG data collection, reporting and benchmarking",
                "revenue_model": "$200–500/month per company",
                "key_risks": [
                    "Market awareness of ESG among SMBs is still nascent",
                    "Potential regulatory changes could alter requirements",
                ],
            },
            {
                "title": "Digital twins for construction contractors",
                "icp": "Small and mid‑sized construction contractors",
                "pain": "Construction errors and delays are extremely costly",
                "solution": "SaaS that creates lightweight digital twins for buildings enabling error detection and cost savings",
                "revenue_model": "$299–999/month",
                "key_risks": [
                    "High complexity to build accurate digital twins",
                    "Resistance from contractors to adopt new technology",
                ],
            },
        ]

    def _load_dataset_from_file(self, path: str) -> List[Dict[str, str]]:
        """
        Load ideas from a JSON file.

        The file must contain a JSON array of objects with the same keys
        expected by the static dataset.  Missing keys will raise a
        ValueError.

        Parameters
        ----------
        path: str
            Path to a JSON file containing idea definitions.

        Returns
        -------
        List[Dict[str, str]]
            A list of idea dictionaries.
        """
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            raise ValueError("Dataset file must contain a JSON array of ideas")
        required_fields = {"title", "icp", "pain", "solution", "revenue_model", "key_risks"}
        ideas: List[Dict[str, str]] = []
        for idx, item in enumerate(data):
            if not isinstance(item, dict):
                raise ValueError(f"Item at index {idx} is not an object")
            missing = required_fields - item.keys()
            if missing:
                raise ValueError(f"Idea at index {idx} is missing required fields: {', '.join(sorted(missing))}")
            # Ensure key_risks is a list
            if not isinstance(item["key_risks"], list):
                raise ValueError(f"key_risks at index {idx} must be a list")
            ideas.append(item)
        return ideas

    def generate_opportunities(self) -> List[Idea]:
        """Generate Idea instances from the static dataset and apply scoring and recommendations."""
        ideas: List[Idea] = []
        for idea_data in self.idea_dataset:
            # Compute scores
            scores = self.scoring_engine.score_idea(idea_data)
            # Apply credibility and feedback adjustments
            cred_adjust, cred_rationale = self.critic.evaluate_with_rationale(idea_data)
            feedback_adjust = self.feedback_manager.get_adjustment(idea_data.get("title", ""))
            raw_total = scores.total.value
            max_total = scores.total.max
            adjusted_total = raw_total + cred_adjust + feedback_adjust
            if adjusted_total < 0:
                adjusted_total = 0
            if adjusted_total > max_total:
                adjusted_total = max_total
            # Determine recommendation based on adjusted total
            recommendation = self._recommendation(
                scores,
                adjusted_total,
                positive_external_signal=self._has_positive_external_signal(idea_data),
            )
            # Create the Idea with final total set
            idea = Idea(
                title=idea_data["title"],
                icp=idea_data["icp"],
                pain=idea_data["pain"],
                solution=idea_data["solution"],
                revenue_model=idea_data["revenue_model"],
                search_volume=self._safe_int(idea_data.get("search_volume")),
                keyword_difficulty=self._safe_int(idea_data.get("keyword_difficulty")),
                trend_status=idea_data.get("trend_status", "Unknown"),
                evidence=[],  # Evidence would be populated in a full system
                scores=scores,
                recommendation=recommendation,
                key_risks=idea_data["key_risks"],
                final_total=adjusted_total,
                critic_adjustment=cred_adjust,
                feedback_adjustment=feedback_adjust,
                critic_rationale=cred_rationale,
            )
            ideas.append(idea)
        return ideas

    def run(self) -> List[Idea]:
        """Run the opportunity engine, including critique and refinement.

        This function repeatedly scores the current dataset and refines it
        until either a high‑quality (green_build) idea is found or a
        maximum number of iterations is reached.  After the loop
        completes, the ideas are returned sorted by adjusted total score.

        Returns
        -------
        List[Idea]
            Ranked ideas including credibility and feedback adjustments.
        """
        max_iterations = 3
        ideas: List[Idea] = []
        for iteration in range(max_iterations):
            scored = self._run_iteration()
            # Check if we have any green ideas; if yes, stop refining
            if any(idea.recommendation == "green_build" for idea in scored):
                ideas = scored
                break
            # Otherwise refine the dataset and try again
            self.refine_dataset(scored)
            ideas = scored  # Keep the latest scored for printing if no green ideas found
        # Sort by adjusted total score (which includes feedback + credibility)
        ideas.sort(key=lambda i: i.final_total, reverse=True)
        # Prepare table headers and compute widths
        headers = [
            "Title",
            "ICP",
            "Pain",
            "Solution",
            "Revenue Model",
            "Search Volume",
            "Keyword Difficulty",
            "Trend",
            "Demand",
            "Acquisition",
            "MVP Complexity",
            "Competition",
            "Revenue Velocity",
            "Total",
            "Recommendation",
            "Key Risks",
        ]
        header_to_key = {
            "Title": "title",
            "ICP": "icp",
            "Pain": "pain",
            "Solution": "solution",
            "Revenue Model": "revenue_model",
            "Search Volume": "search_volume",
            "Keyword Difficulty": "keyword_difficulty",
            "Trend": "trend_status",
            "Demand": "demand_score",
            "Acquisition": "acquisition_score",
            "MVP Complexity": "mvp_complexity_score",
            "Competition": "competition_score",
            "Revenue Velocity": "revenue_velocity_score",
            "Total": "total_score",
            "Recommendation": "recommendation",
            "Key Risks": "key_risks",
        }
        rows = [i.as_dict() for i in ideas]
        column_widths: Dict[str, int] = {h: len(h) for h in headers}
        for row in rows:
            for h in headers:
                key = header_to_key[h]
                value = str(row[key])
                if len(value) > column_widths[h]:
                    column_widths[h] = len(value)
        # Print header row
        header_line = " | ".join(h.ljust(column_widths[h]) for h in headers)
        print(header_line)
        print("-" * len(header_line))
        # Print rows
        for idea in ideas:
            d = idea.as_dict()
            clipped_row = [
                (str(d[header_to_key[h]])[:57] + "..." if len(str(d[header_to_key[h]])) > 60 else str(d[header_to_key[h]]))
                for h in headers
            ]
            line = " | ".join(
                clipped_row[idx].ljust(column_widths[headers[idx]])
                for idx in range(len(headers))
            )
            print(line)

        # Surface critic adjustments for transparency
        print("\nCritic adjustments (delta: reason):")
        for idea in ideas:
            rationale = idea.critic_rationale or "no credibility signals"
            print(f"- {idea.title}: {idea.critic_adjustment:+} ({rationale})")
        return ideas

    def _safe_int(self, value: Optional[object]) -> Optional[int]:
        try:
            return int(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    def _has_positive_external_signal(self, idea_data: Dict[str, object]) -> bool:
        search_volume = self._safe_int(idea_data.get("search_volume")) if isinstance(idea_data, dict) else None
        keyword_difficulty = self._safe_int(idea_data.get("keyword_difficulty")) if isinstance(idea_data, dict) else None
        trend_status = "" if not isinstance(idea_data, dict) else str(idea_data.get("trend_status", "")).lower()
        search_signal = search_volume is not None and search_volume >= 1000
        difficulty_signal = keyword_difficulty is not None and keyword_difficulty <= 50
        trend_signal = trend_status == "rising"
        return search_signal or difficulty_signal or trend_signal

    def _recommendation(self, scores: IdeaScores, adjusted_total: float, positive_external_signal: bool) -> str:
        total_max = scores.total.max
        green_cutoff = 0.75 * total_max
        yellow_cutoff = 0.65 * total_max
        demand_cutoff = 0.8 * scores.demand.max
        acquisition_cutoff = 0.75 * scores.acquisition.max
        demand_value = scores.demand.value
        acquisition_value = scores.acquisition.value
        if (
            adjusted_total >= green_cutoff
            and demand_value >= demand_cutoff
            and acquisition_value >= acquisition_cutoff
            and positive_external_signal
        ):
            return "green_build"
        if adjusted_total >= yellow_cutoff:
            return "yellow_validate"
        return "red_kill"
