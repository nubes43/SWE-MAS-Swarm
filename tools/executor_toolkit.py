import subprocess
from pathlib import Path


def run_code_execution(repo_name: str, test_file_name: str) -> str:
    """
    Executes the provided code in the given Repo. Can be used to run created pytest files.
    
    Args:
        repo_name (str): the name of the repository
        test_file_name (str): full name of the test file

    Returns:
        str: The result of the execution
    """
    work_dir=f".\\coding\\{repo_name}\\"
    # Create a code executor agent that uses a Docker container to execute code.
    try:
        return subprocess.run(
                ["pytest", work_dir + test_file_name],
                check=True,
                capture_output=True
            )
    except subprocess.CalledProcessError as e:
        return e
    
    # Run the agent with a given code snippet.

    # Stop the code executor.
    