import csv
import pprint
import re
import sys
from collections import OrderedDict
from sys import argv

"""
A module for parsing accessibility rules and sentences from
an csv exported from an excel file. The csv file
must be in UTF-8 format with UNIX linefeeds.

Also, any syntax errors in the logical expressions
should be fixed manually before parsing. The parser will
try to report unbalanced parentheses.
"""

LANGUAGES = ["fi", "sv", "en"]

# CSV row indices
EXPRESSION = 0
VARIABLE = 4
OPERATOR = 5
VALUE = 6
QRS_KEY = 9
KEYS = {
    7: "case_names",
    # The keys below are not currently used.
    # 8: 'shortcoming_title',
    # 10: 'requirement',
    # 11: 'shortcoming_summary',
    13: "shortcoming_fi",
    14: "shortcoming_sv",
    15: "shortcoming_en",
}
FINAL_KEYS = [
    k
    for k in KEYS.values()
    if k not in ["shortcoming_fi", "shortcoming_sv", "shorcoming_en"]
]
FINAL_KEYS.append("shortcoming")


class ParseError(Exception):
    pass


class Expression(object):
    eid = 0

    def __init__(self, depth):
        Expression.eid += 1
        self.messages = {}
        self.depth = depth
        self.eid = Expression.eid
        self.next_sibling = None
        self.parent = None
        self.first_line = None
        self.flags = None
        self.mode = 0
        self.message_id = None

    def id(self):
        return str(self.eid)

    def indent(self):
        return "".ljust(self.depth * 2)

    def include(self):
        return self._included_in_mode(self.mode)

    def _included_in_mode(self, mode):
        if self.flags is None:
            return True
        return "include" in self.flags[mode]


class Compound(Expression):
    id_suffix = "ABC"

    def __init__(self, depth):
        super(Compound, self).__init__(depth)
        self.operator = None
        self.operands = []

    def id(self):
        if self.parent is None:
            return str(self.eid) + Compound.id_suffix[self.mode]
        else:
            return str(self.eid)

    def add_operand(self, operand):
        self.operands.append(operand)
        if len(self.operands) > 1:
            self.operands[-2].next_sibling = operand

    def set_operator(self, operator, row):
        if self.operator is None:
            self.operator = operator
        else:
            if operator != self.operator:
                msg = """
Error, trying to change operator of a compound expression at {}.
Probable cause: missing closing parenthesis right before said line.
                """.format(row[-1])
                print(msg)  # noqa: T201

    def set_mode(self, mode):
        self.mode = mode
        for o in self.operands:
            o.set_mode(mode)

    def include(self):
        if not self._included_in_mode(self.mode):
            return False
        for o in self.operands:
            if o.include():
                return True
        return False

    def val(self):
        operands = [s.val() for s in self.operands if s.val() and s.include()]
        if len(operands):
            ret = {
                "operator": self.operator,
                "id": self.id(),
                "operands": operands,
                "msg": self.message_id,
                "path": self.variable_path,
                "source": self.first_line,
            }
            if self.requirement_id:
                ret["requirement_id"] = self.requirement_id
            return ret
        else:
            return None

    def __str__(self):
        just = "\n" + self.indent()
        ret = "{just}({idstring}{subexpressions}{just}{idstring})".format(
            just=just,
            idstring="%s #%s" % (self.operator, self.id()),
            subexpressions=self.indent().join([str(s) for s in self.operands]),
        )
        if len(self.messages):
            ret += just
            ret += just.join(["%s: %s" % (i, v) for i, v in self.messages.items()])
        return ret + "\n"


class Comparison(Expression):
    def __init__(self, depth, variable, operator, value):
        super(Comparison, self).__init__(depth)
        self.variable = variable
        self.operator = operator
        self.value = value
        self.variable_path = None

    def set_mode(self, mode):
        self.mode = mode

    def val(self):
        ret = {
            "operator": self.operator,
            "operands": [self.variable, self.value],
            "id": self.id(),
            "msg": self.message_id,
            "path": self.variable_path,
            "source": self.first_line,
        }
        if self.requirement_id:
            ret["requirement_id"] = self.requirement_id
        return ret

    def __str__(self):
        just = "".ljust(self.depth * 2)
        ret = "\n" + just
        ret += " ".join(
            [
                ("#%s [%s] " % (self.id(), str(self.variable)) + self.variable_path),
                self.operator,
                self.value,
            ]
        )
        if len(self.messages):
            ret += "\n" + just
            ret += ("\n" + just).join(
                ["%s: %s" % (i, v) for i, v in self.messages.items()]
            )
            ret += "\n"
        return ret


def next_line(reader):
    line = next(reader)
    next_line.lineno += 1
    return next_line.lineno, line


next_line.lineno = 0


def exit_on_error(message, expression=None, lineno=None):
    print("Error: " + message)  # noqa: T201
    if expression:
        print(  # noqa: T201
            "  beginning at line %s, expression %s"
            % (expression.first_line, str(expression))
        )
    if lineno:
        print("  beginning at line %s" % lineno)  # noqa: T201
    sys.exit(2)


OPENING_PARENTHESIS = re.compile(r"([ ]*)\(")
CLOSING_PARENTHESIS = re.compile(r"([ ]*)\)")
OPERATOR_PATTERN = re.compile(r"([ ]*)(AND|OR)")
NUMERIC_ID = re.compile(r"[0-9]+")
VARIABLE_NAME = re.compile(r"[ ]*\[[0-9]+\][ ]?([^ ]+) .*")


def parenthesis(string, pattern):
    match = pattern.match(string.rstrip())
    if match:
        whitespace = match.groups()[0]
        if whitespace:
            return len(whitespace)
        else:
            return 0
    return None


def operator(string):
    match = OPERATOR_PATTERN.match(string)
    if match:
        return (len(match.group(1)), match.group(2))
    else:
        return (None, None)


def parse_language_versions(string):
    return [
        {"fi": fi, "sv": sv, "en": en}
        for (fi, sv, en) in [case.split(";") for case in string.split(":")]
    ]


def update_messages(row, expression):
    for i, key in KEYS.items():
        current = row[i]
        if current is not None and current.strip() != "":
            if key in ["case_names", "shortcoming_title"]:
                current = parse_language_versions(current)
            expression.messages[key] = current
    shortcoming = {}
    for lang in LANGUAGES:
        key = "shortcoming_%s" % lang
        msg = expression.messages.get(key)
        if not msg:
            continue
        del expression.messages[key]
        shortcoming[lang] = msg
    if len(shortcoming):
        expression.messages["shortcoming"] = shortcoming


def update_flags(row, expression):
    raw_string = row[QRS_KEY]
    string_parts = raw_string.split(":")
    human_keys = {"Q": "include", "R": "reports", "S": "detailed_choice"}
    bits = []
    for part in string_parts:
        vals = set()
        for char in part:
            if char not in human_keys.keys():
                exit_on_error("Wrong QRS character %s at row %s." % (char, row))
            vals.add(human_keys[char])
        bits.append(vals)
    completely_empty = True
    for val in bits:
        if len(val):
            completely_empty = False
            break
    if not completely_empty:
        expression.flags = bits


def build_comparison(iterator, row, depth=0, requirement_id=None):
    try:
        variable, operator, value = int(row[VARIABLE]), row[OPERATOR], row[VALUE]
    except ValueError:
        return exit_on_error("Value error %s." % row)
    if operator == "I":
        operator = "NEQ"
    elif operator == "E":
        operator = "EQ"
    else:
        return exit_on_error("Unknown comparison operator %s." % operator)

    expression = Comparison(depth, variable, operator, value)
    match = VARIABLE_NAME.match(row[EXPRESSION])
    if match:
        path = match.group(1).split(".")
        path[0] = path[0].lower()
        expression.variable_path = path
    else:
        print("nomatch")  # noqa: T201
    update_messages(row, expression)
    update_flags(row, expression)
    return expression


def build_compound(iterator, depth=0, requirement_id=None):
    row = next(iterator)
    compound = Compound(depth)
    while parenthesis(row[EXPRESSION], CLOSING_PARENTHESIS) is None:
        op_depth, op = operator(row[EXPRESSION])
        if op_depth is not None:
            compound.set_operator(op, row)
        else:
            child = build_expression(
                iterator, row, depth=depth + 1, requirement_id=requirement_id
            )
            child.parent = compound
            compound.add_operand(child)
        try:
            row = next(iterator)
        except StopIteration:
            break
    depth = parenthesis(row[EXPRESSION], CLOSING_PARENTHESIS)
    if depth is None:
        raise ParseError("Unclosed compound expression (aka mismatched parentheses(.")
    for operand in compound.operands:
        if operand.variable_path[0] != "service_point":
            compound.variable_path = operand.variable_path[0:1]
            break

    if len(compound.operands) == 1:
        compound.operands[0].parent = compound.parent
        compound.operands[0].messages = compound.messages
        return compound.operands[0]
    return compound


def build_expression(iterator, row, depth=0, requirement_id=None):
    parenthesis_depth = parenthesis(row[EXPRESSION], OPENING_PARENTHESIS)
    next_expression_id = Expression.eid + 1
    if depth == 1:
        requirement_id = str(next_expression_id)

    first_line = row[-1]
    if parenthesis_depth is None:
        expression = build_comparison(
            iterator, row, depth=depth, requirement_id=requirement_id
        )
    else:
        try:
            expression = build_compound(
                iterator, depth=depth, requirement_id=requirement_id
            )
        except ParseError as e:
            return exit_on_error(str(e), lineno=first_line)
    expression.first_line = row[-1]
    expression.requirement_id = requirement_id
    return expression


def rescope(expression, rescope_key):
    if type(expression) is Compound:
        for subexpression in expression.operands:
            rescope(subexpression, rescope_key)
    if expression is None:
        return
    next_sibling = expression.next_sibling
    if next_sibling is None:
        return
    if rescope_key == "messages":
        for key in FINAL_KEYS:
            current = getattr(expression, rescope_key).get(key)
            if not current:
                continue
            if key in ["case_names", "shortcoming_title"]:
                if expression.parent is not None:
                    current = getattr(expression.parent, rescope_key)[key] = current
                    del getattr(expression, rescope_key)[key]
                    continue
            next_message = getattr(next_sibling, rescope_key).get(key)
            if next_message is None or next_message == "":
                if expression.parent.parent is not None:
                    getattr(expression.parent, rescope_key)[key] = current
                    del getattr(expression, rescope_key)[key]
    elif rescope_key == "flags":
        current = getattr(expression, rescope_key)
        if not current:
            return
        next_flags = getattr(next_sibling, rescope_key, None)
        if next_flags is None:
            if expression.parent.parent is not None:
                setattr(expression.parent, rescope_key, current)
                setattr(expression, rescope_key, None)


messages = []
message_ids = {}
message_id_incr = 0
PRIMARY_KEY = "fi"


def save_message(multilingual_message):
    global messages, message_ids, message_id_incr
    if multilingual_message is None:
        return None
    # de-duplicate messages based on PRIMARY KEY contents
    for lang, val in multilingual_message.items():
        val = val.replace("#3", "")
        if lang == "en":
            multilingual_message[lang] = re.sub("#[12]ntrance", "Entrance", val)
        elif lang == "fi":
            multilingual_message[lang] = re.sub("#[12]isään", "Sisään", val)
        elif lang == "sv":
            multilingual_message[lang] = re.sub("#[12]ngång", "Ingång", val)
    msg_key = multilingual_message[PRIMARY_KEY]
    msg_id = None
    if msg_key not in message_ids:
        msg_id = message_id_incr
        message_id_incr += 1
        message_ids[msg_key] = msg_id
    msg_id = message_ids[msg_key]
    for lang in multilingual_message.keys():
        try:
            current_message = messages[msg_id]
        except IndexError:
            messages.append({})
            current_message = messages[msg_id]
        if lang not in current_message:
            current_message[lang] = multilingual_message[lang]
        # else:
        #     if current_message[lang] != multilingual_message[lang]:
        #         exit_on_error("Mismatching translations: {} != {} (orig: {})".format(
        #             current_message[lang], multilingual_message[lang],
        #             current_message[PRIMARY_KEY]))
    return msg_id


def gather_messages(expression):
    if expression is None or not isinstance(expression, Expression):
        return {}
    if len(expression.messages):
        if "shortcoming" in expression.messages:
            msg_id = save_message(expression.messages["shortcoming"])
            expression.message_id = msg_id
    if isinstance(expression, Compound):
        for e in expression.operands:
            gather_messages(e)


def build_tree(reader):
    global messages
    tree = OrderedDict()
    row_groups = OrderedDict()
    _, row = next_line(reader)
    accessibility_case_id = None
    while True:
        if NUMERIC_ID.match(row[EXPRESSION]):
            accessibility_case_id = row[EXPRESSION]
            row_groups[accessibility_case_id] = []
        elif len(row[EXPRESSION]) > 0:
            row_groups[accessibility_case_id].append(row)
        try:
            lineno, row = next_line(reader)
            row.append("lineno: %s" % lineno)
        except StopIteration:
            break
    for acid, rows in row_groups.items():
        rows = [["("]] + rows + [[")"]]
        it = iter(rows)
        row = next(it)
        tree[acid] = build_expression(it, row, depth=0)
    for expression in tree.values():
        rescope(expression, "messages")
        rescope(expression, "flags")
    for expression in tree.values():
        gather_messages(expression)
    return tree, messages


def parse_accessibility_rules(filename):
    with open(filename, "r", encoding="utf8") as f:
        reader = csv.reader(f, delimiter=";", quotechar='"')
        tree = build_tree(reader)
        return tree


WIDTH = 140
if __name__ == "__main__":
    if len(argv) != 3:
        print(  # noqa: T201
            "Please provide the desired operation and the input csv filename "
            "as the first and second parameters.\n\nOperation is one of\n"
            "  values, messages or debug."
        )
        sys.exit(1)
    op, filename = argv[1], argv[2]
    tree, messages = parse_accessibility_rules(filename)
    if op == "debug":
        for i, v in tree.items():
            print("Case " + i)  # noqa: T201
            print(str(v))  # noqa: T201
    elif op == "values":
        key_qualifiers = "ABC"
        for v in tree.values():
            for mode in range(len(v.messages["case_names"])):
                v.set_mode(mode)
                pprint.pprint(v.val(), width=WIDTH)  # noqa: T203
    elif op == "messages":
        pprint.pprint(messages, width=WIDTH)  # noqa: T203
