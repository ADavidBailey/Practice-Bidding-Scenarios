"""
Cross-pipeline-stage comparison for PBN files.
"""

import os
from typing import Dict, Optional

from .comparator import DiffResult, SemanticComparator
from .parser import PBNParser


# Map user-friendly stage names to FOLDERS config keys
STAGE_TO_FOLDER_KEY = {
    "pbn": "pbn",
    "bba": "bba",
    "filtered": "bba_filtered",
    "bba-filtered": "bba_filtered",
    "filtered-out": "bba_filtered_out",
    "bba-filtered-out": "bba_filtered_out",
    "bidding-sheets": "bidding_sheets",
    "rotated": "pbn_rotated",
    "pbn-rotated": "pbn_rotated",
}


class CrossStageComparator:
    """Compare files across pipeline stages."""

    def __init__(self, project_root: str, folders: Dict[str, str]):
        """
        Initialize cross-stage comparator.

        Args:
            project_root: Path to project root
            folders: Dictionary mapping folder keys to paths (from config.FOLDERS)
        """
        self.project_root = project_root
        self.folders = folders

    def get_stage_path(self, scenario: str, stage: str) -> str:
        """
        Get full path for scenario at given stage.

        Args:
            scenario: Scenario name (e.g., "1N", "Smolen")
            stage: Stage name (e.g., "pbn", "bba", "filtered")

        Returns:
            Full path to PBN file

        Raises:
            ValueError: If stage is unknown
        """
        folder_key = STAGE_TO_FOLDER_KEY.get(stage.lower())
        if folder_key is None:
            valid_stages = ", ".join(sorted(STAGE_TO_FOLDER_KEY.keys()))
            raise ValueError(f"Unknown stage: {stage}. Valid stages: {valid_stages}")

        folder = self.folders.get(folder_key)
        if folder is None:
            raise ValueError(f"Folder not configured for stage: {stage}")

        return os.path.join(folder, f"{scenario}.pbn")

    def list_stages(self) -> list:
        """List available stage names."""
        return sorted(set(STAGE_TO_FOLDER_KEY.keys()))

    def compare_stages(
        self,
        scenario: str,
        stage1: str,
        stage2: str,
        comparator: Optional[SemanticComparator] = None,
        parser: Optional[PBNParser] = None,
    ) -> DiffResult:
        """
        Compare a scenario across two pipeline stages.

        Args:
            scenario: Scenario name
            stage1: First stage name
            stage2: Second stage name
            comparator: SemanticComparator instance (created if None)
            parser: PBNParser instance (created if None)

        Returns:
            DiffResult from comparison

        Raises:
            FileNotFoundError: If either file doesn't exist
            ValueError: If stage names are invalid
        """
        if comparator is None:
            comparator = SemanticComparator()
        if parser is None:
            parser = PBNParser()

        path1 = self.get_stage_path(scenario, stage1)
        path2 = self.get_stage_path(scenario, stage2)

        if not os.path.exists(path1):
            raise FileNotFoundError(f"File not found: {path1}")
        if not os.path.exists(path2):
            raise FileNotFoundError(f"File not found: {path2}")

        file1 = parser.parse_file(path1)
        file2 = parser.parse_file(path2)

        return comparator.compare(file1, file2)
