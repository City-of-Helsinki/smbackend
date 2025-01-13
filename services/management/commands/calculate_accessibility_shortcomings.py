from django.core.management.base import BaseCommand
from tqdm import tqdm

from services.models import AccessibilityVariable, Unit, UnitAccessibilityShortcomings
from services.utils import AccessibilityShortcomingCalculator as Calculator


class Command(BaseCommand):
    help = "Calculate accessibility shortcomings for all units"

    def add_arguments(self, parser):
        parser.add_argument(
            "--print-rules", action="store_true", help="Display rules only"
        )
        parser.add_argument(
            "--no-progress-bar",
            action="store_false",
            dest="progress_bar",
            help="Disable progress bar",
        )

    def handle(self, **options):
        if options["print_rules"]:
            self.print_rules()
            return

        progress_bar = (
            tqdm(desc="Calculating shortcomings", total=Unit.objects.count())
            if options["progress_bar"]
            else None
        )
        for unit in Unit.objects.all():
            description, shortcoming_count = Calculator().calculate(unit)
            UnitAccessibilityShortcomings.objects.update_or_create(
                unit=unit,
                defaults={
                    "accessibility_shortcoming_count": shortcoming_count,
                    "accessibility_description": description,
                },
            )
            if progress_bar:
                progress_bar.update(1)
        if progress_bar:
            progress_bar.close()

    def print_rules(self):
        def print_rule(rule, indent=""):
            message = (
                " >> {}".format(list(Calculator().messages[rule["msg"]].values())[0])
                if rule["msg"] is not None and rule["msg"] < len(Calculator().messages)
                else ""
            )
            try:
                evaluation = (
                    " {} : {}".format(
                        AccessibilityVariable.objects.get(id=rule["operands"][0]),
                        rule["operands"][1],
                    )
                    if not isinstance(rule["operands"][0], dict)
                    else ""
                )
            except AccessibilityVariable.DoesNotExist:
                evaluation = "**MISSING**"
            print(  # noqa: T201
                "{}{} {}{}{}".format(
                    indent, rule["id"], rule["operator"], evaluation, message
                )
            )
            for operand in rule["operands"]:
                if isinstance(operand, dict):
                    print_rule(operand, indent + "  ")

        for name, rule in Calculator().rules.items():
            print("=== RULE {} ===".format(name))  # noqa: T201
            print_rule(rule)
