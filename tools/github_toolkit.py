import os
import re
import requests
import base64
import subprocess
from pathlib import Path

def fetch_github_issue(owner: str, repository: str, issue_number: int) -> dict:
    """
    Fetches issue details from GitHub.
    """
    token = os.getenv("GITHUB_TOKEN")
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    url = f"https://api.github.com/repos/{owner}/{repository}/issues/{issue_number}"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def list_repository_files(owner: str, repository: str, branch: str = "main") -> list:
    """
    Lists all files in a repository on the specified branch.
    """
    token = os.getenv("GITHUB_TOKEN")
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    url = f"https://api.github.com/repos/{owner}/{repository}/git/trees/{branch}?recursive=1"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        tree = response.json().get("tree", [])
        return [item["path"] for item in tree if item["type"] == "blob"]
    else:
        print(f"Error listing files: {response.status_code} - {response.text}")
        return []

def fetch_code_from_github(owner: str, repository: str, file_path: str, branch: str = "main") -> str:
    """
    Fetches the content of a file from GitHub.
    """
    token = os.getenv("GITHUB_TOKEN")
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    url = f"https://api.github.com/repos/{owner}/{repository}/contents/{file_path}?ref={branch}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        file_content: str = response.json().get("content", "")
        return base64.b64decode(file_content).decode("utf-8")  # Decode base64 file content
    else:
        return f"Error fetching file content: {response.status_code} - {response.text}"
    
    
def get_imported_modules(file_content: str):
    imported_modules = set()
    for line in file_content.splitlines():
        match = re.match(r'^\s*(?:from|import) ([\w\.]+)', line)
        if match:
            module = match.group(1).split('.')[-1]  # Get the top-level module
            imported_modules.add(module)
    return imported_modules
 
def find_relevant_files(files: list, keywords: list, owner, repository, branch) -> list:
    """
    Filters a list of files for relevance based on keywords.
    """
    relevant_files = []
    for file_path in files:
        if any(keyword.lower() == file_path.lower().split(".")[0] for keyword in keywords):
            relevant_files.append(file_path)
    
    module_to_file = {path.split("/")[-1].replace(".py", ""): path for path in files}
    files_to_check = list(relevant_files)
    while files_to_check:
        current_file = files_to_check.pop(0)
        file_content = fetch_code_from_github(owner, repository, current_file, branch)
        imported_modules = get_imported_modules(file_content)
        for module in imported_modules:
            if module in module_to_file:
                module_file = module_to_file[module]
                if module_file not in relevant_files:
                    relevant_files.append(module_file)
                    files_to_check.append(module_file)
    return relevant_files


def analyze_issue(owner: str, repository: str, issue_number: int, branch: str = "main") -> dict:
    """
    Analyzes a GitHub issue, categorizes it, and dynamically fetches relevant code files.
    """
    return analyze_issue_async(owner, repository, issue_number, branch)
    
def analyze_issue_async(owner, repository, issue_number, branch):
    issue = fetch_github_issue(owner, repository, issue_number)
    title = issue.get("title", "").lower()
    body = issue.get("body", "").lower()

    # Fetch repository file structure
    all_files = list_repository_files(owner, repository, branch)

    # Build the response
    response = {
        "Repository Name": repository,
        "Title": title,
        "Description": body,
        "File Structure": all_files
    }
    return response


def clone_repository(owner: str, repository: str) -> str:
    """
    Klont ein Git-Repository basierend auf Owner und Repository-Name in das angegebene Zielverzeichnis.
    
    Args:
        owner (str): GitHub-Owner (z. B. Benutzername oder Organisation).
        repo (str): Name des GitHub-Repositorys.
        
    Returns:
        str: Pfad des geklonten Repositorys oder eine Fehlermeldung.
    """
    try:
        # Erstelle die Repository-URL
        repo_url = f"https://github.com/{owner}/{repository}.git"
        
        # Zielverzeichnis erstellen, falls es nicht existiert
        destination_path = Path('./coding')
        destination_path.mkdir(parents=True, exist_ok=True)
        
        # Repository-Pfad erstellen
        repo_path = destination_path / repository

        # Überprüfen, ob das Repository bereits existiert
        if repo_path.exists():
            return f"Repository '{repository}' wurde bereits geklont in {repo_path}."

        # Git-Klon-Befehl ausführen
        subprocess.run(
            ["git", "clone", repo_url, str(repo_path)],
            check=True,
        )
        return f"Repository erfolgreich geklont: {repo_path}"
    except subprocess.CalledProcessError as e:
        return f"Fehler beim Klonen des Repositorys: {e}"
    
def checkout_commit(repository: str, commit_hash: str):
    """
    Checks out on a specified commit within the repository
    
    Args:
        repository (str): name of the repository.
        commit_hash (str): The commit hash of the commit to check out to
    """
    try:
        destination_path = Path('./coding')
        destination_path.mkdir(parents=True, exist_ok=True)
        
        repo_path = destination_path / repository
        
        subprocess.run(["git", "-C", repo_path, "checkout", commit_hash], check=True)
        print(f"Successfully checked out to commit: {commit_hash}")
    except subprocess.CalledProcessError as e:
        print(f"Error during checkout: {e}")