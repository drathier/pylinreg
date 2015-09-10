__author__ = 'drathier'

character_classes = {
    "alnum": r"[0-9A-Za-z]",
    "alpha": r"[A-Za-z]",
    "ascii": r"[\x00-\x7F]",
    "blank": r"[\t ]",
    "cntrl": r"[\x00-\x1F\x7F]",
    "digit": r"[0-9]",
    "graph": r"[A-Za-z0-9!\"#$%&'()*+,\-./:;<=>?@[\\\]^_`{|}~]",
    "lower": r"[a-z]",
    "print": r"[A-Za-z0-9!\"#$%&'()*+,\-./:;<=>?@[\\\]^_`{|}~ ]",  # graph + space
    "punct": r"[!-/:-@[-`{-~]",
    "space": r"[\t\n\v\f\r ]",
    "upper": r"[A-Z]",
    "word": r"[0-9A-Za-z_]",
    "xdigit": r"[0-9A-Fa-f]",
}

max_character_class_name_length = max((len(x) for x in character_classes.keys()))


class ParseException(Exception):
    pass


class Parser(object):
    def __init__(self, regexp):
        self.regexp = regexp
        self.pos = 0
        self.stack = []

    def raise_exception(self, got, expected):
        raise ParseException("Expected {0} at position {1}, got {2}".format(expected, self.pos, got))

    """ Helpers, to save typing and make code more readable. """

    def next(self):
        self.pos += 1
        if self.pos > len(self.regexp):
            raise ParseException("Out of bounds")
        return self.pos

    @property
    def curr(self):
        return self.regexp[self.pos]

    def lookahead(self, n):
        return self.regexp[self.pos + n]

    def assert_char(self, c):
        if self.curr != c:
            self.raise_exception(self.curr, c)
        self.pos += 1

    def read_until(self, c, max_length=-1):
        s = ""
        while self.curr != c and (max_length < 0 or len(s) < max_length):
            s += self.curr
            self.next()
        return s

    """ Parsing functions. """

    def parse(self):
        if self.curr == '[':
            self.pos += 1
            self.parse_char_class()

    def parse_char_class(self):
        charset = ""
        # extract charset string
        if self.curr == '[':  # character classes, [[:somestring:]]
            self.assert_char('[')
            self.assert_char(':')

            # parse name of character class
            s = self.read_until(":", 10)
            if s not in character_classes:
                self.raise_exception(s, "valid character class")
            charset = character_classes[s]
        else:  # parse charset as written in regex
            charset = self.read_until(']')

        # create set of characters from charset string
        ret = set()
        pos = 0
        try:
            while pos < len(charset):
                if charset[pos] == '\\':  # escapes, such as \-
                    ret.add(charset[pos + 1])
                    pos += 2  # consume 2 characters
                elif charset[pos + 1] == '-':  # A-Z
                    ret = ret.union([chr(x) for x in range(ord(charset[pos]), ord(charset[pos + 2]))])
                    pos += 3  # consume 3 characters
                else:  # single characters
                    ret.add(charset[pos])
                    pos += 1
        except IndexError as e:
            raise ParseException(
                "charset at {0} has invalid syntax at offset {1} in extended string {2} (raw:{3})".format(self.curr,
                                                                                                          pos,
                                                                                                          charset, e))
        self.assert_char(']')
        return ret
