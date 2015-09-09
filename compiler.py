# -*- encoding: UTF-8 -*-

__author__ = 'drathier'


def old_parse_expr(expr):
    #print "parse_expr(", expr, ")"

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


def parse_charset(expr):
    ret = []
    #print "parse_charset", "expr", expr
    # todo: implement [^whatever]
    pos = -1
    neg = False

    if expr[0] == "^":
        neg = True
        pos += 1

    while pos + 1 < len(expr):
        pos += 1
        c = expr[pos]
        print expr, "; ", pos, "; ", c
        if pos + 2 < len(expr) and expr[pos + 1] == "-" and c != "\\":
            ret += [chr(x) for x in range(ord(expr[pos]), ord(expr[pos + 2]) + 1)]
            pos += 2
        else:
            ret += [c]

    union = [('union', ret)]
    if neg:
        union = [('neg-union', ret)]

    #print "parse_charset", union
    return union


def parse_expr(expr):
    #print "parse_expr(", expr, ")"
    ret = []
    union = []
    this = ""
    depth = 0
    pos = -1

    while pos + 1 < len(expr):
        pos += 1
        c = expr[pos]
        #print expr, "; ", pos, "; ", c
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
            d = expr[pos]
            if d == "d":
                if this != "":
                    ret += [this]
                    this = ""
                ret += ('union', ['0', '9'])
            elif d == "D":
                if this != "":
                    ret += [this]
                    this = ""
                ret += ('neg-union', ['0', '9'])
            elif d == "s":
                if this != "":
                    ret += [this]
                    this = ""
                ret += ('union', ['\t', '\n', '\r', '\f', '\v'])
            elif d == "S":
                if this != "":
                    ret += [this]
                    this = ""
                ret += ('neg-union', ['\t', '\n', '\r', '\f', '\v'])
            elif d == "w":
                if this != "":
                    ret += [this]
                    this = ""
                ret += ('union', [('range', ['a', 'z']), ('range', ['A', 'Z']), ('range', ['0', '9']), '_'])
            elif d == "W":
                if this != "":
                    ret += [this]
                    this = ""
                ret += ('neg-union', [('range', ['a', 'z']), ('range', ['A', 'Z']), ('range', ['0', '9']), '_'])
            else:
                this += d

        elif c == "{":
            if this != "":
                ret += [this]
                this = ""
            endpos = expr.find("}", pos)
            a = expr[pos + 1:endpos]
            pos = endpos
            print "a:", a

            if ',' in a:
                fr, to = a.split(",")
            else:
                fr = to = a
            to = int(to)
            fr = int(fr)
            ret, pop = ret[:-1], ret[-1]
            ret += [pop] * fr + [('union', ['', pop])] * (to - fr)

        elif c == "[":
            if this != "":
                ret += [this]
                this = ""
            endpos = expr.find("]", pos)
            a = expr[pos + 1:endpos]
            pos = endpos
            ret += parse_charset(a)

        else:
            this += c

    if union:
        union += [this]
        ret += [("union", list(union))]
    elif this != "":
        ret += [this]

    if type(ret) == list:
        ret = filter(None, ret)

    if len(ret) == 1:
        ret = ret[0]

    """
    if type(ret) is list and all([type(x) in (list, str) for x in ret]):
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

    #print "ret", ret
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
    test("a*", ('star', ['a']))
    test("(abc)+", ['abc', ('star', ['abc'])])
    test("(abc)?", ('union', ['', 'abc']))
    test("abc?", ['ab', ('union', ['', 'c'])])
    test("aa(ab)*cc", ['aa', ('star', ['ab']), 'cc'])
    test("(aaa(bc)c)", ['aaa', 'bc', 'c'])
    test(r"(aa.a(bc)*\)c)", ['aa', ('dot',), 'a', ('star', ['bc']), ')c'])
    test("(aaa(bc){2}c)", ['aaa', 'bc', 'bc', 'c'])
    test("(aaa(bc){3,3}c)", ['aaa', 'bc', 'bc', 'bc', 'c'])
    test("(aaa(bc){1,3}c)", ['aaa', 'bc', ('union', ['', 'bc']), ('union', ['', 'bc']), 'c'])
    test("[abc]*", ('star', [('union', ['a', 'b', 'c'])]))
    test("[a-c]", ('union', ['a', 'b', 'c']))
    test("[xa-fA-Fy]", ('union', ['x', 'a', 'b', 'c', 'd', 'e', 'f', 'A', 'B', 'C', 'D', 'E', 'F', 'y']))
    test("[^a-c]", ('neg-union', ['a', 'b', 'c']))
    test("[-a-c]", ('union', ['-', 'a', 'b', 'c']))
    test("[a-c-]", ('union', ['a', 'b', 'c', '-']))
    test("[^^]", ('neg-union', ['^']))

    print "-" * 50
    print "all tests ok"


    # TODO: minimization algorithm adds nodes until graph is optimal, but keeps the old ones.
    # TODO: there's always a non-empty edge to move along, but it's not minimal at all
    # TODO: maybe it's good enough, if we just remove the empty edges?
    # TODO: there are definitely nodes that are equal in the final graph,
