import sys
from sys import argv
import codecs
import csv
import re
import pprint
import itertools
import traceback

# CSV row indices
EXPRESSION = 0
VARIABLE = 4
OPERATOR = 5
VALUE = 6
KEYS = {
    7: 'case_names',
    8: 'shortcoming_title',
    10: 'requirement',
    11: 'shortcoming_summary',
    13: 'shortcoming_fi',
    14: 'shortcoming_sv',
    15: 'shortcoming_en',
}

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
    def indent(self):
        return ''.ljust(self.depth * 2)

class Compound(Expression):
    def __init__(self, depth):
        super(Compound, self).__init__(depth)
        self.operator = None
        self.operands = []
    def add_operand(self, operand):
        self.operands.append(operand)
        if len(self.operands) > 1:
            self.operands[-2].next_sibling = operand

    def set_operator(self, operator):
        if self.operator is None:
            self.operator = operator
        else:
            if operator != self.operator:
                print("Error, trying to change operator of a compound expression.")
    def val(self):
        return {
            self.operator: [s.val() for s in self.operands],
            'messages': self.messages,
        }
    def __str__(self):
        just = "\n" + self.indent()
        ret = "{just}({idstring}{subexpressions}{just}{idstring})".format(
            just=just,
            idstring="%s #%s" % (self.operator, self.eid),
            subexpressions=self.indent().join([str(s) for s in self.operands]))
        if len(self.messages):
            ret += just
            ret += just.join(["%s: %s" % (i, v)
                              for i, v in self.messages.items()])
        return ret + "\n"

class Comparison(Expression):
    def __init__(self, depth, variable, operator, value):
        super(Comparison, self).__init__(depth)
        self.variable = variable
        self.operator = operator
        self.value = value
        self.variable_path = None
    def val(self):
        if self.next_sibling:
            nexts = self.next_sibling.eid
        else:
            nexts = '<none>'
        return {self.operator: [self.variable, self.value],
                'messages': self.messages,
        }
    def __str__(self):
        just = ''.ljust(self.depth*2)
        ret = "\n" + just
        ret += " ".join([("[%s] " % str(self.variable) + self.variable_path), self.operator, self.value])
        if len(self.messages):
            ret += "\n" + just
            ret += ("\n" + just).join(["%s: %s" % (i,v) for i,v in self.messages.items()])
            ret += "\n"
        return ret

def next_line(reader):
    line = next(reader)
    next_line.lineno += 1
    return next_line.lineno, line
next_line.lineno = 0


def exit_on_error(message, expression=None, lineno=None):
    print("Error: " + message)
    if expression:
        print("  beginning at line %s, expression %s" % (
            expression.first_line, str(expression)))
    if lineno:
        print("  beginning at line %s" % lineno)
    sys.exit(2)

OPENING_PARENTHESIS = re.compile(r'([ ]*)\(')
CLOSING_PARENTHESIS = re.compile(r'([ ]*)\)')
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
        g1, g2 = match.group(1), match.group(2)
        return (len(match.group(1)), match.group(2))
    else:
        return (None, None)

def parse_case_names(string):
    return [{'fi': fi, 'sv': sv, 'en': en}
            for (fi, sv, en) in
            [case.split(';') for case in string.split(':')]]

def update_messages(row, expression):
    for i, key in KEYS.items():
        current = row[i]
        if current is not None and current.strip() != '':
            if key == 'case_names':
                current = parse_case_names(current)
            expression.messages[key] = current

def build_comparison(iterator, row, depth=0):
    try:
        variable, operator, value = int(row[VARIABLE]), row[OPERATOR], row[VALUE]
    except ValueError as e:
        exit_on_error("Value error %s." % row)
    if operator == 'I':
        operator = 'NEQ'
    elif operator == 'E':
        operator = 'EQ'
    else:
        exit_on_error("Unknown comparison operator %s." % operator)

    expression = Comparison(depth, variable, operator, value)
    match = VARIABLE_NAME.match(row[EXPRESSION])
    if match:
        expression.variable_path = match.group(1)
    else:
        print('nomatch')
    update_messages(row, expression)
    return expression

def build_compound(iterator, depth=0):
    row = next(iterator)
    compound = Compound(depth)
    while parenthesis(row[EXPRESSION], CLOSING_PARENTHESIS) is None:
        op_depth, op = operator(row[EXPRESSION])
        if op_depth is not None:
            compound.set_operator(op)
        else:
            child = build_expression(iterator, row, depth=depth+1)
            child.parent = compound
            compound.add_operand(child)
        try:
            row = next(iterator)
        except StopIteration:
            break
    depth = parenthesis(row[EXPRESSION], CLOSING_PARENTHESIS)
    if depth is None:
        raise ParseError('Unclosed compound expression (aka mismatched parentheses(.')
    if len(compound.operands) == 1:
        compound.operands[0].parent = compound.parent
        compound.operands[0].messages = compound.messages
        return compound.operands[0]
    return compound

def build_expression(iterator, row, depth=0):
    result = None
    parenthesis_depth = parenthesis(row[EXPRESSION], OPENING_PARENTHESIS)
    next_expression_id = Expression.eid + 1
    first_line = row[-1]
    if parenthesis_depth is None:
        expression = build_comparison(iterator, row, depth=depth)
    else:
        try:
            expression = build_compound(iterator, depth=depth)
        except ParseError as e:
            exit_on_error(str(e), lineno=first_line)
    expression.first_line = row[-1]
    return expression

def rescope_messages(expression):
    if type(expression) is Compound:
        for subexpression in expression.operands:
            rescope_messages(subexpression)
    if expression == None:
        return
    next_sibling = expression.next_sibling
    if next_sibling is None:# or type(next_sibling) != type(expression):
        return
    for i, key in KEYS.items():
        current = expression.messages.get(key)
        if not current:
            continue
        if key == 'case_names':
            if expression.parent is not None:
                expression.parent.messages[key] = current
                del expression.messages[key]
                continue
        next_message = next_sibling.messages.get(key)
        if next_message is None or next_message == '':
            if expression.parent.parent is not None:
                expression.parent.messages[key] = current
                del expression.messages[key]

# def gather_messages(expression):
#     if expression == None or not isinstance(expression, Expression):
#         return {}
#     elif isinstance(expression, Comparison):
#         return {expression.eid: expression.messages}
#     elif isinstance(expression, Compound):
#         ret = {expression.eid: expression.messages}
#         for e in expression.operands

def build_tree(reader):
    tree = {}
    row_groups = {}
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
        rows = [['(']] + rows + [[')']]
        it = iter(rows)
        row = next(it)
        tree[acid] = build_expression(it, row, depth=0)
    for acid, expression in tree.items():
        rescope_messages(expression)
    # messages = {}
    # for acid, expression in tree.items():
    #     messages.update(gather_messages(expression))
    return tree

def parse_accessibility_rules(filename):
    with open(filename, 'r') as f:
        reader = csv.reader(f, delimiter=';', quotechar='"')
        return build_tree(reader)

if __name__ == '__main__':
    if len(argv) != 2:
        print("Please provide the input csv filename "
              "as the first and only parameter")
        sys.exit(1)
    tree = parse_accessibility_rules(argv[1])
    for i, v in tree.items():
        print("Case " + i)
        print(v.messages['case_names'])
        print(str(v))
        pprint.pprint(v.val())
