# -*- encoding: UTF-8 -*-
import re
import compiler
import time

__author__ = 'drathier'

glob_id_counter = 0


# FIXME: Check possible bug, if regex -> NFA conversion creates nodes with more than one outgoing ε path
# FIXME: only last one gets saved. If regex_nfa never returns a node where ε path is already set, we're probably fine


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
        global glob_id_counter
        self.id = glob_id_counter
        glob_id_counter += 1

        self.out = dict()
        self.final = False

    @property
    def outs(self):
        return self.out.iteritems()

    def __repr__(self):
        return str(self.id)
        return "(" + ", ".join([k + "->" + (str(v) or "ε;") for k, v in self.out.iteritems()]) + \
               ("; final" * self.final) + ")"


cache = dict()  # TODO: remember to clear out cache between compiles


class MultiNode(object):
    def search(self, node, c):  # TODO: this only checks one step; make it search in depth
        #print "search(", node, ", '" + (c or "ε") + "')"
        ret = {node}
        checked = set()

        def find(n):
            #print "find", type(n), n
            if n in checked:
                return
            checked.add(n)

            if c in n.out:
                for o in n.out[c]:
                    ret.add(o)
                    find(o)

        find(node)
        #print "->", [r.id for r in ret], "->", ret
        return tuple(ret)

    @classmethod
    def new(cls, nodes):
        tnodes = tuple(nodes)
        if tnodes not in cache:
            cache[tnodes] = MultiNode(nodes)
        return cache[tnodes]

    def __init__(self, nodes):
        global glob_id_counter
        self.id = glob_id_counter
        glob_id_counter += 1
        n = set()
        for node in nodes + [self.search(x, '') for x in nodes]:
            if type(node) is Node:
                n.add(node)
            else:
                n = n.union(node)
        nodes = set(n)
        self.nodes = nodes
        self.final = any([node.final for node in nodes])
        self.out = dict()
        #print "created", self

    def __repr__(self):
        return "MultiNode<{0}>({1})".format(self.id, list(self.nodes))

    def nexthop_repr(self):
        return repr(self) + "{" + ", ".join(["{0}->{1}".format(x, next_node) for x, next_node in self.out]) + "}"

    @property
    def outs(self):
        ret = {}
        for key in self.all_keys():
            ret[key] = [self.get(key)]
        return ret.iteritems()

    def get(self, c):
        #print "{0}.get('{1}'):".format(self, c)
        if c in self.out:
            #print "cached ->", self.out[c]
            return self.out[c]
        res = set()
        for n in self.nodes:
            if c in n.out:
                res = res.union(n.out[c])
        #print "res", res
        self.out[c] = MultiNode.new(list(res))
        #print "->", self.out[c]
        return self.out[c]

    def all_keys(self):
        return filter(None, set([c for n in self.nodes for c in n.out.keys()]))


class NFA(object):
    def match(self, string):
        n = self.start
        pos = 0
        while pos < len(string):
            #print "matching", string[pos], "==", bool(n.get(string[pos]))
            if n.get(string[pos]):
                n = n.get(string[pos])
                pos += 1
            else:
                return False
        return n.final

    def __init__(self, regexp):
        self.start = Node()
        self.end = Node()
        if regexp:
            self.end = regex_nfa(regexp, self.start)
        else:
            self.start.out[""] = [self.end]
        self.end.final = True

        global glob_id_counter
        self.id = glob_id_counter
        glob_id_counter += 1

    def __repr__(self):
        edges = []
        checked_nodes = set()
        nodes = [self.start]

        while len(nodes) > 0:
            this = nodes[0]
            nodes = nodes[1:]
            if this in checked_nodes:
                continue

            for char, tos in this.outs:
                for to in tos:
                    nodes.append(to)
                    if (this, char, to) not in edges:
                        # edges.append("{0} -[{1}]-> {2}".format(this.id, char or 'ε', to.id))
                        edges.append('{0} -> {2} [ label="{1}" ];'.format(this.id, char or 'ε', to.id))

            checked_nodes.add(this)

        finals = ["{0} [ shape=doublecircle ];".format(a.id) for a in filter(lambda x: x.final, checked_nodes)]

        return "NFA<" + str(self.id) + ">(\n" + "\n".join(edges) + "\n" + "\n".join(finals) + ")"


def regex_nfa(regexp, node):
    """ Takes former head of NFA. Returns new head node. """
    #print "regex_nfa(", regexp, ", ", node, ")"
    if len(regexp) == 0:
        return node
    if type(regexp) is tuple:
        t = regexp[0]
        if t == "union":
            start = node
            end = Node()
            for part in regexp[1]:
                x = regex_nfa(part, start)
                x.out[""] = [end]
            return end
        if t == "neg-union":
            start = node
            end = Node()
            for part in regexp[1]:
                x = regex_nfa(part, start)
                x.out[""] = [end]
            return start
        elif t == "star":
            start = node
            end = regex_nfa(regexp[1], start)
            end.out[""] = [start]
            return start
        else:
            print "unknown tuple:", t
            assert False
    else:
        for a in regexp:
            if type(a) in (list, tuple):
                node = regex_nfa(a, node)
            elif type(a) is str and a:
                for c in a:
                    x = Node()
                    node.out[c] = [x]
                    node = x
            else:
                print "what", a
        return node


def minimize(nfa):
    #print "minimize(", type(nfa), nfa, ")"

    def union(nodes):
        n = Node()
        for node in nodes:
            n.final |= node.final
            for o in n.out.keys():
                n.out[o] += node.out[o]
        return n

    dfa = NFA(False)
    m = MultiNode.new([nfa])
    dfa.start = m

    return dfa


def compile(pattern):
    tree = compiler.parse_expr(pattern)
    n = NFA(tree)
    return minimize(n.start)


#'''
n = 1000
for n in range(n):
    pattern = r"a?"*n + r"a"*n
    string = "a"*n
    t1 = time.time()
    prog = compile(pattern)
    result = prog.match(string)
    t2 = time.time()
    #reprog = re.compile(pattern)
    #reprog.match(string)
    t3 = time.time()

    #print pattern, "match", string, "->", result

    print n, t2-t1, t3-t2

'''
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
        m = minimize(ret.start)

        print "result: ", ret
        print "minimized: ", m

        print "cache dump"
        for nodes, multinode in cache.iteritems():
            print "multinode", multinode, "->", nodes
            print "outs", list(multinode.outs)
            print "-" * 10
        print "#" * 20
        return
        edges = []
        for nodes, multinode in cache.iteritems():
            for c, tos in multinode.outs:
                for to in tos:
                    print multinode, "to", to
                    edges += ['{0}->{2} [label="{1}"]'.format(multinode.id, c, to.id)]
                    # TODO: make graphviz syntax out of all these nodes, to see where they point.
            print "outs", list(multinode.outs)
            # TODO: i.e. is my NFA repr broken, or the graph? Because the graph looks like it should be ok from console logs.
            print "-" * 10
        print "#" * 20
        print "\n".join(edges)


    """
    test(['abcde'])
    test(['aa', 'ab', 'cc'])
    test(('union', ['a', 'b', 'c']))
    test('aaabcc')
    test(('neg-union', ['^']))
    """
    # test([('union', ['', 'a']), ('union', ['', 'a']), ('union', ['', 'a'])])
    # test(['p', ('star', ['abc']), 's'])
    # test(['aaabc', ('star', ['c'])])
    test(['a', ('star', ['bb']), 'c', ('star', ['d']), 'f', ('union', ['', 't'])])

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
    # '''
