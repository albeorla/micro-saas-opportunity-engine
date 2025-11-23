from typing import List, Dict, Optional
import json
from src.models import Idea
from src.scoring import ScoringEngine
from src.researcher import Researcher
from src.critic import Critic
from src.feedback import UserFeedbackManager

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
            cred_adjust = self.critic.evaluate(idea_data)
            feedback_adjust = self.feedback_manager.get_adjustment(idea_data.get("title", ""))
            # Adjusted total score (bounded between 0 and max)
            raw_total = scores.total.value
            max_total = scores.total.max
            adjusted_total = raw_total + cred_adjust + feedback_adjust
            if adjusted_total < 0:
                adjusted_total = 0
            if adjusted_total > max_total:
                adjusted_total = max_total
            demand_value = scores.demand.value
            acquisition_value = scores.acquisition.value
            # Use adjusted total for recommendations
            if adjusted_total >= 75 and demand_value >= 24 and acquisition_value >= 15:
                recommendation = "green_build"
            elif adjusted_total >= 65:
                recommendation = "yellow_validate"
            else:
                recommendation = "red_kill"
            results.append(
                Idea(
                    title=idea_data["title"],
                    icp=idea_data["icp"],
                    pain=idea_data["pain"],
                    solution=idea_data["solution"],
                    revenue_model=idea_data["revenue_model"],
                    evidence=[],
                    scores=scores,
                    recommendation=recommendation,
                    key_risks=idea_data.get("key_risks", []),
                    final_total=adjusted_total,
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
        # Remove ideas that are clearly not viable (red_kill)
        self.idea_dataset = [
            idea_data
            for idea_data, scored in zip(self.idea_dataset, scored_ideas)
            if scored.recommendation != "red_kill"
        ]
        # Add new ideas from researcher
        new_ideas = self.researcher.search_micro_saas_ideas(self.theme)
        # Avoid duplicates by checking titles
        existing_titles = {idea["title"] for idea in self.idea_dataset}
        for idea in new_ideas:
            if idea["title"] not in existing_titles:
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
            cred_adjust = self.critic.evaluate(idea_data)
            feedback_adjust = self.feedback_manager.get_adjustment(idea_data.get("title", ""))
            raw_total = scores.total.value
            max_total = scores.total.max
            adjusted_total = raw_total + cred_adjust + feedback_adjust
            if adjusted_total < 0:
                adjusted_total = 0
            if adjusted_total > max_total:
                adjusted_total = max_total
            # Determine recommendation based on adjusted total
            demand_value = scores.demand.value
            acquisition_value = scores.acquisition.value
            if (
                adjusted_total >= 75
                and demand_value >= 24
                and acquisition_value >= 15
            ):
                recommendation = "green_build"
            elif adjusted_total >= 65:
                recommendation = "yellow_validate"
            else:
                recommendation = "red_kill"
            # Create the Idea with final total set
            idea = Idea(
                title=idea_data["title"],
                icp=idea_data["icp"],
                pain=idea_data["pain"],
                solution=idea_data["solution"],
                revenue_model=idea_data["revenue_model"],
                evidence=[],  # Evidence would be populated in a full system
                scores=scores,
                recommendation=recommendation,
                key_risks=idea_data["key_risks"],
                final_total=adjusted_total,
            )
            ideas.append(idea)
        return ideas

    def run(self) -> None:
        """Run the opportunity engine, including critique and refinement.

        This function repeatedly scores the current dataset and refines it
        until either a high‑quality (green_build) idea is found or a
        maximum number of iterations is reached.  After the loop
        completes, the ideas are printed in a table sorted by total
        score.
        """
        max_iterations = 3
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
