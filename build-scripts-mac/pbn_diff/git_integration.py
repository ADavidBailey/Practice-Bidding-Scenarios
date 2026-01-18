"""
Git integration for comparing file versions.
"""

import os
import subprocess
import tempfile
from typing import List, Optional


class GitIntegration:
    """Git integration for comparing file versions."""

    def __init__(self, repo_path: str):
        """
        Initialize git integration.

        Args:
            repo_path: Path to git repository root
        """
        self.repo_path = repo_path

    def get_committed_content(
        self, file_path: str, commit_ref: str = "HEAD"
    ) -> Optional[str]:
        """
        Get file content from a specific commit.

        Args:
            file_path: Absolute or relative path to file
            commit_ref: Git commit reference (default: HEAD)

        Returns:
            File content as string, or None if file doesn't exist at that commit
        """
        try:
            # Get relative path from repo root
            if os.path.isabs(file_path):
                rel_path = os.path.relpath(file_path, self.repo_path)
            else:
                rel_path = file_path

            result = subprocess.run(
                ["git", "show", f"{commit_ref}:{rel_path}"],
                cwd=self.repo_path,
                capture_output=True,
                check=True,
            )
            # Try to decode as UTF-8, fall back to latin-1
            try:
                return result.stdout.decode('utf-8')
            except UnicodeDecodeError:
                return result.stdout.decode('latin-1')
        except subprocess.CalledProcessError as e:
            stderr = e.stderr.decode('utf-8', errors='replace') if e.stderr else ""
            if "does not exist" in stderr or "exists on disk" in stderr:
                return None
            raise

    def get_file_at_commit(
        self, file_path: str, commit_ref: str = "HEAD"
    ) -> Optional[str]:
        """
        Get a file's content at a specific commit and return path to temp file.

        Args:
            file_path: Path to file
            commit_ref: Git commit reference

        Returns:
            Path to temporary file with committed content, or None if not found
        """
        content = self.get_committed_content(file_path, commit_ref)
        if content is None:
            return None

        # Write to temp file for parsing
        fd, temp_path = tempfile.mkstemp(suffix=".pbn", prefix="pbn_git_")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(content)
            return temp_path
        except Exception:
            os.close(fd)
            os.unlink(temp_path)
            raise

    def has_uncommitted_changes(self, file_path: str) -> bool:
        """
        Check if file has uncommitted changes.

        Args:
            file_path: Path to file

        Returns:
            True if file has uncommitted changes
        """
        try:
            # Get relative path
            if os.path.isabs(file_path):
                rel_path = os.path.relpath(file_path, self.repo_path)
            else:
                rel_path = file_path

            result = subprocess.run(
                ["git", "diff", "--quiet", "--", rel_path],
                cwd=self.repo_path,
                capture_output=True,
            )
            return result.returncode != 0
        except subprocess.CalledProcessError:
            return False

    def get_changed_pbn_files(self, staged: bool = False) -> List[str]:
        """
        Get list of changed PBN files.

        Args:
            staged: If True, get staged changes; otherwise get unstaged

        Returns:
            List of relative paths to changed .pbn files
        """
        try:
            cmd = ["git", "diff", "--name-only"]
            if staged:
                cmd.append("--staged")
            cmd.extend(["--", "*.pbn"])

            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
            return [f for f in result.stdout.strip().split("\n") if f.endswith(".pbn")]
        except subprocess.CalledProcessError:
            return []

    def get_changed_files(
        self, commit_ref: str = "HEAD", path_pattern: Optional[str] = None
    ) -> List[str]:
        """
        Get list of files changed between commit and working copy.

        Uses git diff --name-only for fast detection without reading file contents.

        Args:
            commit_ref: Git commit reference to compare against (default: HEAD)
            path_pattern: Optional path or glob pattern to filter (e.g., "pbn/*.pbn")

        Returns:
            List of relative paths to changed files
        """
        try:
            cmd = ["git", "diff", "--name-only", commit_ref]
            if path_pattern:
                cmd.extend(["--", path_pattern])

            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
            files = result.stdout.strip().split("\n")
            return [f for f in files if f]  # Filter empty strings
        except subprocess.CalledProcessError:
            return []

    def get_repo_root(self) -> str:
        """Get the repository root path."""
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()


def find_repo_root(start_path: str) -> Optional[str]:
    """
    Find git repository root starting from given path.

    Args:
        start_path: Starting path to search from

    Returns:
        Repository root path, or None if not in a git repo
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=start_path,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None
