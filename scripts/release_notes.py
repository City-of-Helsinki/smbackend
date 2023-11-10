import sys

from github import Github

repo_owner = "City-of-Helsinki"
repo_name = "smbackend"


def print_section(title, items):
    if items:
        print(f"## {title}")
        for item in items:
            print(f"- {item.title} [(#{item.number})]({item.issue_url})")


def create_release_notes(start_tag, end_tag):
    """
    Fetch the pull request titles between two tags and print them in a Markdown format.
    """
    g = Github()
    repo = g.get_repo(f"{repo_owner}/{repo_name}")
    commits = list(repo.compare(start_tag, end_tag).commits)

    prs = []
    features = []
    fixes = []
    improvements = []
    other = []

    for commit in commits:
        for p in commit.get_pulls():
            if p not in prs:
                prs.append(p)
                branch = p.head.ref
                if "feature" in branch:
                    features.append(p)
                elif "fix" in branch:
                    fixes.append(p)
                elif "improvement" in branch:
                    improvements.append(p)
                else:
                    other.append(p)

    print(f"# Release Notes - {end_tag}")
    print_section("Features", features)
    print_section("Fixes", fixes)
    print_section("Improvements", improvements)
    print_section("Other", other)


if __name__ == "__main__":
    start_tag = sys.argv[1]
    end_tag = sys.argv[2]
    create_release_notes(start_tag, end_tag)
