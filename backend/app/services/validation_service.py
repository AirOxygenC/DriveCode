import os
import subprocess
import tempfile
import shutil
from pathlib import Path

class ValidationService:
    def __init__(self):
        pass

    def run_tests(self, repo_url, branch, test_command="pytest"):
        """
        Clone repo, checkout branch, and run tests.
        Returns (success: bool, output: str)
        """
        temp_dir = None
        try:
            # Create temp directory
            temp_dir = tempfile.mkdtemp()
            print(f"Cloning repo to {temp_dir}...")
            
            # Clone repo
            clone_result = subprocess.run(
                ["git", "clone", "--depth", "1", "--branch", branch, repo_url, temp_dir],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if clone_result.returncode != 0:
                return False, f"Clone failed: {clone_result.stderr}"
            
            # Run tests
            print(f"Running tests: {test_command}")
            test_result = subprocess.run(
                test_command.split(),
                cwd=temp_dir,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            success = test_result.returncode == 0
            output = test_result.stdout + "\n" + test_result.stderr
            
            return success, output
            
        except subprocess.TimeoutExpired:
            return False, "Test execution timed out"
        except Exception as e:
            return False, f"Test execution error: {str(e)}"
        finally:
            # Cleanup
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)

    def validate_code_quality(self, code, language="python"):
        """
        Basic code quality checks (can be extended with linters).
        """
        # For now, just basic checks
        if not code or len(code.strip()) == 0:
            return False, "Empty code"
        
        # Check for syntax errors (Python only for now)
        if language == "python":
            try:
                compile(code, '<string>', 'exec')
                return True, "Syntax valid"
            except SyntaxError as e:
                return False, f"Syntax error: {str(e)}"
        
        return True, "Basic validation passed"
