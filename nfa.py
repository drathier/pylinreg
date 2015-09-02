# -*- encoding: UTF-8 -*-
__author__ = 'drathier'


class Node(object):
    """
    traverse algorithm:
        assuming next char in string is x:
        if x in node.out:
            node = node.out[x]
        else:
            node = node.out[""] # empty string

    """
    def __init__(self):
        self.out = dict()
        self.final = False

    def __repr__(self):
        return "(" + ", ".join([k + "->" + ("ε;" if k == "" else str(v)) for k, v in self.out.iteritems()]) + \
               ("; final" * self.final) + ")"


class NFA(object):
    def __init__(self, regexp):
        self.start = Node()
        self.end = regex_nfa(regexp, self.start)
        self.end.final = True

    def __repr__(self):
        return "NFA(" + str(self.start) + ")"


def regex_nfa(regexp, node):
    """ returns last node """
    print "regex_nfa(", regexp, ", ", node, ")"
    if len(regexp) == 0:
        return node
    if type(regexp) is tuple:
        t = regexp[0]
        if t == "union":
            start = node
            end = Node()
            for part in regexp[1]:
                x = regex_nfa(part, start)
                x.out[""] = end
            return end
        if t == "neg-union":
            start = node
            end = Node()
            for part in regexp[1]:
                x = regex_nfa(part, start)
                x.out[""] = end
            return start
        elif t == "star":
            start = node
            end = Node()
            start.out[""] = end
            end.out[""] = start
            for part in regexp[1]:
                x = regex_nfa(part, start)
                x.out[""] = end
            return end
        else:
            print "unknown tuple:", t
            assert False
    else:
        for a in regexp:
            if type(a) is list:
                node = regex_nfa(a, node)
            elif type(a) is str and a:
                for c in a:
                    x = Node()
                    node.out[c] = x
                    node = x
            else:
                print "what", a
        return node


if __name__ == "__main__":
    def test(a, exp=None):
        print "-" * 50
        print "->", a
        ret = NFA(a)
        if exp:
            if exp == ret:
                return
            else:
                print "failed test case; expected", exp, "got", ret
                assert False
        print "result: ", ret


    test(['abcde'])
    test(['aa', 'ab', 'cc'])
    test(('union', ['a', 'b', 'c']))
    test(('union', ['a', 'b', 'c']))
    test('aaabcc')
    test(('neg-union', ['^']))
    test("[a-c]", ('union', [('range', 'a', 'c')]))
    #test(('star', ['aaabcc']))
    #test(['aaabc', ('star', ['c'])])
    # test(('star', ['a']))
    """
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
    test("[xa-fA-Fy]", ('union', ['x', ('range', 'a', 'f'), ('range', 'A', 'F'), 'y']))
    test("[^a-c]", ('neg-union', [('range', 'a', 'c')]))
    test("[-a-c]", ('union', ['-', ('range', 'a', 'c')]))
    test("[a-c-]", ('union', [('range', 'a', 'c'), '-']))
    """
    print "-" * 50
    print "all tests ok"
