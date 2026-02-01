from github import Github
import base64

class GitHubService:
    def __init__(self, access_token):
        self.g = Github(access_token)
        
    def get_repo(self, repo_name):
        # repo_name format: "owner/repo"
        return self.g.get_repo(repo_name)

    def list_files(self, repo_name, path=""):
        repo = self.get_repo(repo_name)
        contents = repo.get_contents(path)
        files = []
        while contents:
            file_content = contents.pop(0)
            if file_content.type == "dir":
                # For MVP, let's just go one level deep or skip recursion to avoid huge trees
                # Or maybe recursive? Let's stay flat or user-guided for now to save tokens.
                # Actually, specialized agents need recursive often. Let's return just the path.
                files.append(f"{file_content.path}/")
                # contents.extend(repo.get_contents(file_content.path)) 
            else:
                files.append(file_content.path)
        return files

    def get_file_content(self, repo_name, file_path):
        repo = self.get_repo(repo_name)
        try:
            content = repo.get_contents(file_path)
            return base64.b64decode(content.content).decode('utf-8')
        except Exception as e:
            return f"Error reading file: {str(e)}"

    def create_pr(self, repo_name, title, body, branch_name, changes):
        # changes: dict of {path: new_content}
        repo = self.get_repo(repo_name)
        sb = repo.get_branch("main")
        
        # Create branch
        try:
            repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=sb.commit.sha)
        except Exception:
            # Branch might exist
            pass
            
        # Commit changes
        # (Simplified: one commit per file or batched? PyGithub element-wise is easiest for MVP)
        for path, content in changes.items():
            try:
                contents = repo.get_contents(path, ref=branch_name)
                repo.update_file(contents.path, f"Update {path}", content, contents.sha, branch=branch_name)
            except:
                repo.create_file(path, f"Create {path}", content, branch=branch_name)
                
        # Create PR
        pr = repo.create_pull(title=title, body=body, head=branch_name, base="main")
        return pr.html_url

    def merge_pull_request(self, repo_name, pr_number, commit_message="Auto-merge by DriveCode"):
        """
        Merge a pull request after validation.
        """
        repo = self.get_repo(repo_name)
        pr = repo.get_pull(pr_number)
        
        if pr.mergeable:
            pr.merge(commit_message=commit_message, merge_method="squash")
            return True, "PR merged successfully"
        else:
            return False, "PR is not mergeable (conflicts or checks failing)"
