"""
Human-interpreted testing for full text queries

Please note this is not meant to be run with pytest nor as part of CI
since the process is only partly automated.
"""
import hashlib
import json
import subprocess
from itertools import zip_longest

from django.core.management.base import BaseCommand
from django.utils import timezone

from services.search_suggestions import get_suggestions

SYMBOLS = {"raise": "▲", "lower": "▽", "missing": "∅", "new": "☛"}

SEARCH_MODIFYING_PATHS = ["services/search_suggestions.py"]

INDEX_MODIFYING_PATHS = [
    "smbackend/elasticsearch/",
    "services/search_indexes.py",
    "services/templates/search/indexes/services/",
]

BASE_QUERIES = [
    # Remember to bump revision when changing queries
    "uima",
    "uimastadion",
    "moni",
    "monipuolinen",
    "päivä",
    "päiväkoti",
    "lasten",
    "lastentarha",
    "meri",
    "merihelsinki",
    "kallion",
    "kallion kirjasto",
]


def incomplete_queries(queries):
    # Add variations with last characters missing from specified queries
    return [x[0:-1] for x in queries]


QUERIES = {
    "revision": 3,
    "queries": sorted(BASE_QUERIES + incomplete_queries(BASE_QUERIES)),
}


def get_git_nth_commit(n=0):
    command = ["git", "log", "-n", str(n + 1), "--pretty=format:%h", "--"]
    command.extend(SEARCH_MODIFYING_PATHS)
    result = subprocess.run(command, stdout=subprocess.PIPE, encoding="utf-8")
    return result.stdout.splitlines()[-1].strip()


def format_git_commit(commit):
    command = ["git", "log", "-1", "--date=short", "--pretty=format:%s [%ad]", commit]
    command.extend(SEARCH_MODIFYING_PATHS)
    result = subprocess.run(command, stdout=subprocess.PIPE, encoding="utf-8")
    return commit + " " + result.stdout.strip()


def get_git_commit(only_index=False, ignore_working_dir=False):
    def restrict_to_index_if_desired(command):
        command.append("--")
        command.extend(SEARCH_MODIFYING_PATHS)
        if only_index:
            command.extend(INDEX_MODIFYING_PATHS)
        return command

    command = restrict_to_index_if_desired(
        ["git", "status", "--porcelain", "--untracked-files=no"]
    )

    result = subprocess.run(command, stdout=subprocess.PIPE, encoding="utf-8")

    if len(result.stdout) == 0 or ignore_working_dir:
        # working directory clean, get HEAD
        if only_index is False:
            return get_git_nth_commit(0)
        else:
            command = restrict_to_index_if_desired(
                ["git", "log", "-n 1", "--pretty=format:%h", "--"]
            )
            result = subprocess.run(command, stdout=subprocess.PIPE, encoding="utf-8")
            return result.stdout.strip()
    else:
        return None


def get_relevant_commits():
    current_commit = get_git_commit()
    if current_commit is None:
        return {"new": None, "old": get_git_nth_commit(0)}
    else:
        return {"new": get_git_nth_commit(0), "old": get_git_nth_commit(1)}


def enrich_result(index, result):
    result.update(
        {
            "index": index,
            "hash": hashlib.sha256(result["suggestion"].encode("utf-8")).hexdigest(),
        }
    )
    return result


def process_results(results):
    return [enrich_result(index, result) for index, result in enumerate(results)]


def run_tests(queries=QUERIES):
    all_results = {
        "queries": {},
    }
    for query in queries["queries"]:
        results = get_suggestions(query, language="fi")
        all_results["queries"][query] = {
            "query": query,
            "results": process_results(results["suggestions"]),
        }
    return all_results


def get_results_filename(commit):
    return "test_search_results.{}.json".format(commit)


def calculate_results(commit):
    index_commit = get_git_commit(only_index=True)

    all_results = run_tests()
    all_results.update(
        {
            "git_commit": commit,
            "git_index_commit": index_commit,
            "persisted": False
            # 'data_timestamp': 'TODO',
            # 'unit_count': 'TODO'
        }
    )
    save_results(all_results)
    return all_results


def load_results(commit, accept_calculated=True):
    if commit is None:
        # Results have to be dynamically received, changes not committed yet.
        # (This is by contract.)
        return calculate_results(commit)
    try:
        with open(get_results_filename(commit), "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        if accept_calculated:
            return calculate_results(commit)
        return None


def save_results(results):
    results["persisted"] = True
    commit = results.get("git_commit")
    if commit is None:
        print(
            "Running on working directory, results will not be saved until changes committed."
        )
        return
    with open(get_results_filename(commit), "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)


def format_suggestion(suggestion, max_length=None, direction="<"):
    if suggestion is None:
        return "".join(" " for _ in range(max_length + 6))
    return "{0:{direction}{padding}}{1:>6}".format(
        suggestion["suggestion"],
        suggestion.get("count") or "",
        direction=direction,
        padding=max_length,
    )


def format_revision(commit, query):
    quality = query.get("quality")
    if commit is None:
        result = "<UNCOMMITTED CHANGES>"
    else:
        result = format_git_commit(commit)
    if quality:
        timestamp = quality["timestamp"]
        result += "   {stars} (awarded {timestamp})".format(
            timestamp=timestamp, stars=format_star_rating(quality["grade"])
        )
    return result


def format_difference(
    old_position, new_position, only_not_found=False, zero_symbol="!"
):
    if new_position is None:
        return "     "
    else:
        new_position = new_position["index"]
    if old_position is None:
        return "    " + zero_symbol
    if only_not_found:
        return "     "
    else:
        difference = old_position - new_position
        if difference == 0:
            return "     "
        elif difference < 0:
            return "{0:3} {1}".format(abs(difference), SYMBOLS["lower"])
        elif difference > 0:
            return "{0:3} {1}".format(difference, SYMBOLS["raise"])


def get_rating_from_user():
    valid_number = False
    while not valid_number:
        try:
            user_input = input("Quality of results as stars (0-5 or enter to skip): ")
            if len(user_input.strip()) == 0:
                break
            stars = int(user_input)
            if -1 < stars < 6:
                valid_number = True
        except Exception:
            pass
    if valid_number:
        return stars
    else:
        return None


def compare_results(commits, show_unchanged=False, no_input=False):
    results = {
        "old": load_results(commits["old"], accept_calculated=False),
        "new": load_results(commits["new"], accept_calculated=True),
    }
    for k in ["old", "new"]:
        if results[k] is None:
            print(
                """Cannot find persisted results for {0}
            Please checkout the relevant git commit, make sure the
            index is up-to-date, and run this management command,
            like this:

            git checkout {0}
            ./manage.py search_suggestions save
            """.format(
                    commits[k]
                )
            )
            exit(1)

    suggestion_max_length = 0
    for key in ["old", "new"]:
        for query in QUERIES["queries"]:
            _results = results[key]["queries"].get(query, {}).get("results", [])
            for suggestion in _results:
                suggestion_max_length = max(
                    len(suggestion["suggestion"]), suggestion_max_length
                )

    results_changed = False
    no_changes = []
    for query in QUERIES["queries"]:
        old_query = results["old"]["queries"].get(query, {})
        new_query = results["new"]["queries"].get(query, {})
        old_suggestions = old_query.get("results", [])
        new_suggestions = new_query.get("results", [])
        unchanged = False
        if [x["hash"] for x in old_suggestions] == [x["hash"] for x in new_suggestions]:
            no_changes.append('"{}"'.format(query))
            if not show_unchanged:
                continue
            unchanged = True

        print()
        warnings = []
        for key in ["old", "new"]:
            if query not in results[key]["queries"]:
                warnings.append(
                    "→ NO RESULTS FOUND IN FILE FOR COMMIT {} -- PLEASE RE-RUN TESTS THERE".format(
                        commits[key]
                    )
                )
        print(
            query,
            "→ RESULTS UNCHANGED BETWEEN REVISIONS" if unchanged else "",
            " ".join(warnings),
        )
        print("".join(("—" for _ in range(len(query)))))

        for suggestion_l, suggestion_r in zip_longest(new_suggestions, old_suggestions):
            old_position = None
            if suggestion_l:
                old_position = next(
                    (
                        index
                        for index, value in enumerate(old_suggestions)
                        if value["hash"] == suggestion_l["hash"]
                    ),
                    None,
                )
            new_position = None
            if suggestion_r:
                new_position = next(
                    (
                        index
                        for index, value in enumerate(new_suggestions)
                        if value["hash"] == suggestion_r["hash"]
                    ),
                    None,
                )

            print(
                format_difference(
                    old_position, suggestion_l, zero_symbol=SYMBOLS["new"]
                ),
                format_suggestion(
                    suggestion_l, max_length=suggestion_max_length, direction="<"
                ),
                format_difference(
                    new_position,
                    suggestion_r,
                    only_not_found=True,
                    zero_symbol=SYMBOLS["missing"],
                ),
                format_suggestion(
                    suggestion_r, max_length=suggestion_max_length, direction="<"
                ),
                sep="    ",
            )
        print(
            "\n {:<{padding}}{:>}".format(
                format_revision(commits["new"], new_query),
                format_revision(commits["old"], old_query),
                padding=suggestion_max_length + 12,
            )
        )
        print("\n\n")
        if no_input:
            continue
        if commits["new"] is None:
            input("press enter to continue")
            continue
        stars = get_rating_from_user()
        if stars is None:
            continue
        results_changed = True
        results["new"]["queries"][query]["quality"] = {
            "grade": stars,
            "timestamp": timezone.now().isoformat(),
        }
        print("You awarded {}".format(format_star_rating(stars)))

    if len(no_changes) > 0:
        print("NO CHANGES DETECTED IN", *no_changes)

    if results_changed:
        save_results(results["new"])


def format_star_rating(stars):
    if stars == 0:
        return "∅"
    else:
        return "".join("★" for _ in range(stars))


class Command(BaseCommand):
    help = "Run human-interpretable regression tests for search suggestions"

    def add_arguments(self, parser):
        parser.add_argument(
            "save",
            nargs="?",
            type=str,
            help='Leave empty or use the value "save" if you want to save results for current commit',
        )
        parser.add_argument(
            "--show-unchanged",
            action="store_true",
            help="Add if you want to see also unchanged results.",
        )
        parser.add_argument(
            "--no-input", action="store_true", help="Add for non-interactive usage."
        )
        parser.add_argument(
            "--force-save",
            action="store_true",
            help="Force saving with HEAD commit even with uncommitted changes",
        )
        parser.add_argument(
            "--old", action="store", help="Explicitly compare this version"
        )
        parser.add_argument(
            "--new", action="store", help="Explicitly compare this version"
        )

    def handle(self, **options):
        subcommand = options["save"]
        if subcommand == "save":
            commit = get_git_commit()
            if commit is None:
                if options["force_save"]:
                    commit = get_git_commit(ignore_working_dir=True)
                else:
                    print("Saving doesn't work with uncommitted changes. Commit first.")
                    exit(1)
            save_results(calculate_results(commit))
        else:
            if "new" in options and "old" in options:
                commits = {"new": options["new"][0:7], "old": options["old"][0:7]}
            else:
                commits = get_relevant_commits()
            try:
                compare_results(
                    commits,
                    show_unchanged=options["show_unchanged"],
                    no_input=options["no_input"],
                )
            except (KeyboardInterrupt, EOFError):
                print()
                exit(1)
