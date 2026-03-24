"""
KURSORIN Git Updater Utility

Handles checking for and pulling updates from the remote Git repository.
"""

import subprocess
import os
from pathlib import Path
from typing import Tuple, Optional
from loguru import logger


class GitUpdater:
    """
    Utility for managing Git-based updates for KURSORIN.
    """
    
    def __init__(self, repo_path: Optional[str] = None):
        """
        Initialize the updater.
        
        Args:
            repo_path: Path to the local repository. 
                      Defaults to the root of the kursorin package.
        """
        if repo_path is None:
            # Default to the parent of the package directory
            repo_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        self.repo_path = repo_path
        self._is_git_repo = os.path.exists(os.path.join(repo_path, ".git"))

    def check_git_installed(self) -> bool:
        """Check if git is installed and accessible."""
        try:
            subprocess.run(["git", "--version"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def is_git_repo(self) -> bool:
        """Check if the current path is a git repository."""
        return self._is_git_repo

    def auto_convert_to_git(self, remote_url: str = "https://github.com/Ardelyo/kursorin2.git") -> Tuple[bool, str]:
        """
        Automatically converts the current directory to a Git repository tracking the given remote.
        This handles the scenario where the user downloaded the project as a ZIP.
        """
        if not self.check_git_installed():
            return False, "Git not installed."
        try:
            subprocess.run(["git", "init"], cwd=self.repo_path, check=True, capture_output=True)
            self._is_git_repo = True
            
            subprocess.run(["git", "remote", "add", "origin", remote_url], cwd=self.repo_path, check=True, capture_output=True)
            subprocess.run(["git", "fetch", "origin"], cwd=self.repo_path, check=True, capture_output=True)
            subprocess.run(["git", "branch", "-M", "main"], cwd=self.repo_path, check=True, capture_output=True)
            
            # Reset to origin/main mixed so local uncommitted changes are kept but history is synced
            subprocess.run(["git", "reset", "--mixed", "origin/main"], cwd=self.repo_path, check=True, capture_output=True)
            
            return True, "Successfully initialized Git tracking."
        except subprocess.CalledProcessError as e:
            logger.error(f"Auto Git init failed: {e.stderr.decode() if e.stderr else str(e)}")
            return False, f"Failed to convert to Git repo: {e}"

    def check_for_updates(self) -> Tuple[bool, str]:
        """
        Check if updates are available on the remote.
        
        Returns:
            Tuple: (update_available: bool, message: str)
        """
        if not self.check_git_installed():
            return False, "Git not found"
        
        if not self.is_git_repo():
            return False, "Not a git repository"

        try:
            # Fetch latest from remote
            subprocess.run(
                ["git", "fetch"], 
                cwd=self.repo_path, 
                capture_output=True, 
                check=True
            )
            
            # Compare local and remote HEAD
            result = subprocess.run(
                ["git", "status", "-uno"], 
                cwd=self.repo_path, 
                capture_output=True, 
                text=True, 
                check=True
            )
            
            output = result.stdout
            if "Your branch is behind" in output:
                return True, "Update available"
            elif "Your branch is up to date" in output:
                return False, "Up to date"
            else:
                return False, "Unknown state or local changes"
        
        except subprocess.CalledProcessError as e:
            logger.error(f"Git check failed: {e.stderr.decode() if e.stderr else str(e)}")
            return False, f"Check failed: {e}"

    def pull_update(self, force: bool = False) -> Tuple[bool, str]:
        """
        Pull the latest updates from the remote.
        
        Args:
            force: If True, uses 'git reset --hard' to overwrite local changes.
            
        Returns:
            Tuple: (success: bool, message: str)
        """
        if not self.check_git_installed():
            return False, "Git not found"

        try:
            if force:
                # Discard local changes and reset to remote
                subprocess.run(
                    ["git", "reset", "--hard", "@{u}"], 
                    cwd=self.repo_path, 
                    check=True, 
                    capture_output=True
                )
                return True, "Successfully reset to latest remote version"
            else:
                # Normal pull
                result = subprocess.run(
                    ["git", "pull"], 
                    cwd=self.repo_path, 
                    capture_output=True, 
                    text=True, 
                    check=True
                )
                if "Already up to date" in result.stdout:
                    return True, "Already up to date"
                return True, "Update successfully pulled"
                
        except subprocess.CalledProcessError as e:
            stderr = e.stderr.decode() if e.stderr else str(e)
            if "local changes to the following files would be overwritten" in stderr:
                return False, "Local changes detected. Use --force to overwrite or commit them."
            logger.error(f"Git pull failed: {stderr}")
            return False, f"Update failed: {stderr}"
