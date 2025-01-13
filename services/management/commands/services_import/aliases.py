import csv
import os

from django import db
from django.conf import settings

from services.models import Unit, UnitAlias

RELEVANT_COLS = [3, 5]  # IMPORTANT: verify the ids are in these columns


def import_aliases():
    path = os.path.join(settings.BASE_DIR, "data", "school_ids.csv")
    try:
        f = open(path, "r")
    except FileNotFoundError:
        print("Aliases file {} not found".format(path))  # noqa: T201
        return

    value_sets = {}
    reader = csv.reader(f, delimiter=",")
    next(reader)
    for row in reader:
        primary_id = row[1]
        value_sets[primary_id] = set(
            row[col] for col in RELEVANT_COLS if row[col] and row[col].strip != ""
        )

    if len(value_sets) == 0:
        print("No aliases found in file.")  # noqa: T201
        return

    counts = {"success": 0, "duplicate": 0, "notfound": 0}
    for primary, aliases in value_sets.items():
        try:
            unit = Unit.objects.get(pk=primary)
            for alias in aliases:
                alias_object = UnitAlias(first=unit, second=alias)
                try:
                    alias_object.save()
                    counts["success"] += 1
                except db.IntegrityError:
                    counts["duplicate"] += 1
        except Unit.DoesNotExist:
            counts["notfound"] += 1

    if counts["success"]:
        print("Imported {} aliases.".format(counts["success"]))  # noqa: T201
    if counts["notfound"]:
        print("{} units not found.".format(counts["notfound"]))  # noqa: T201
    if counts["duplicate"]:
        print("Skipped {} aliases already in database.".format(counts["duplicate"]))  # noqa: T201
