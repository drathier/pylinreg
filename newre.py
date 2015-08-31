# -*- encoding: UTF-8 -*-

__author__ = 'drathier'


def old_parse_expr(expr):
    print "parse_expr(", expr, ")"

    kind = None
    ret = []
    pos = -1

    while pos + 1 < len(expr):
        pos += 1
        c = expr[pos]
        print "char", c, "at", pos, "in", expr
        if c == '(':
            nret, npos = parse_expr(expr[pos + 1:])
            print "nret", nret, "npos", npos
            pos += npos
            ret += [nret]

        # breakers
        elif c == "|":
            ret = ["union", ret]
        elif c == ')':
            print "end paren", ret, pos + 1
            return (ret,), pos + 1

        # suffixes
        elif c == "*":
            ret[-1] = ("star", ret[-1])
        elif c == "+":
            ret[-1] = ret[-1], ("star", ret[-1])
        else:
            print "adding char", c
            ret += c

    return ret, pos + 1


def _compile(expr):
    return parse_expr(expr)[0]


STAR = "star"
UNION = "union"

"""

tuples start with identifying string, such as 'star' or 'union'

lists are used to build tree structures

"""


def parse_expr(expr):
    print "parse_expr(", expr, ")"
    ret = []
    union = []
    this = ""
    depth = 0
    pos = -1

    while pos + 1 < len(expr):
        pos += 1
        c = expr[pos]
        print expr, "; ", pos, "; ", c
        if c == "(":
            depth += 1
            paren_start = pos
            while pos + 1 < len(expr) and depth > 0:
                pos += 1
                c = expr[pos]
                if c == "\\":
                    pos += 1
                    continue
                if c == "(":
                    depth += 1
                elif c == ")":
                    depth -= 1
            if this:
                ret += [this]
            ret += [parse_expr(expr[paren_start + 1:pos])]
            this = ""
        elif c == ")":
            ValueError("malformed regex:", expr, pos, c)

        elif c == "|":
            union += [this]
            this = ""

        elif c == "*":
            if this != "":
                ret += [this[:-1], this[-1:]]
                this = ""
            ret[-1] = ("star", [ret[-1]])

        elif c == "+":
            if this != "":
                ret += [this[:-1], this[-1:]]
                this = ""
            ret += [("star", [ret[-1]])]

        elif c == "?":
            if this != "":
                ret += [this[:-1], this[-1:]]
                this = ""
            ret[-1] = ("union", ['', ret[-1]])

        elif c == ".":
            if this != "":
                ret += [this]
                this = ""
            ret += [("dot",)]

        elif c == "\\":
            pos += 1
            this += expr[pos]

        elif c == "{":
            if this != "":
                ret += [this]
                this = ""
            endpos = expr.find("}", pos)
            a = expr[pos + 1:endpos]
            pos = endpos
            print "a:", a
            fr, to = a.split(",")
            to = int(to)
            fr = int(fr)
            ret, pop = ret[:-1], ret[-1]
            ret += [pop] * fr + [('union', ['', pop])] * (to - fr)

        else:
            this += c

    if union:
        union += [this]
        ret += [("union", list(union))]
    elif this != "":
        ret += [this]

    if len(ret) == 1:
        ret = ret[0]

    """if type(ret) is list and all([type(x) in (list, str) for x in ret]):
        print "flattening ret", ret
        flat = []
        for inner_list in ret:
            if type(inner_list) is list:
                for x in inner_list:
                    flat += [x]
            else:
                flat += [inner_list]
        ret = flat
        print ret, "-->", flat
    """

    print "ret", ret
    return ret


if __name__ == "__main__":
    def test(a, exp=None):
        print "-" * 50
        print "->", a
        ret = parse_expr(a)
        if exp:
            if exp == ret:
                return
            else:
                print "failed test case; expected", exp, "got", ret
                assert False
        print "result: ", ret


    test("aa(ab)cc", ['aa', 'ab', 'cc'])
    test("a|b|c", ('union', ['a', 'b', 'c']))
    test("(a|b|c)", ('union', ['a', 'b', 'c']))
    test("(aaabcc)", 'aaabcc')
    test("(aaabcc)*", ('star', ['aaabcc']))
    test("aaabcc*", ['aaabc', ('star', ['c'])])
    test("(abc)+", ['abc', ('star', ['abc'])])
    test("(abc)?", ('union', ['', 'abc']))
    test("abc?", ['ab', ('union', ['', 'c'])])
    test("aa(ab)*cc", ['aa', ('star', ['ab']), 'cc'])
    test("(aaa(bc)c)", ['aaa', 'bc', 'c'])
    test(r"(aa.a(bc)*\)c)", ['aa', ('dot',), 'a', ('star', ['bc']), ')c'])
    test("(aaa(bc){3,3}c)", ['aaa', 'bc', 'bc', 'bc', 'c'])
    test("(aaa(bc){1,3}c)", ['aaa', 'bc', ('union', ['', 'bc']), ('union', ['', 'bc']), 'c'])

    print "-" * 50
    print "all tests ok"
