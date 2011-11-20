import imaplib2
import getpass

class ImapDataParser(object):
    def __init__(self, s):
        self.__s = s
        self.__i = 0

    def skip_ws(self):
        while self.__i < len(self.__s) and self.__s[self.__i].isspace():
            self.__i += 1

    def get_list_contents(self):
        list_contents = []
        while self.__i < len(self.__s):
            if self.__s[self.__i] == ')':
                self.__i += 1
                break
            list_contents.append(self.get_item())
            self.skip_ws()
        return tuple(list_contents)

    def get_item(self):
        c = self.__s[self.__i]
        if c == '(':
            self.__i += 1
            self.skip_ws()
            return self.get_list_contents()
        elif c == '\\':
            self.__i += 1
            return '\\' + self.get_atom()
        elif c == '"':
            self.__i += 1
            return self.get_quoted_string_contents()
        elif c.isdigit():
            return self.get_number()
        else:
            raise Exception("Don't know how to parse {0!r} at {1}".format(
                    self.__s, self.__i))

    def get_number(self):
        value = 0
        while self.__i < len(self.__s) and self.__s[self.__i].isdigit():
            value *= 10
            value += ord(self.__s[self.__i]) - ord('0')
            self.__i += 1
        return value

    def get_quoted_string_contents(self):
        s = ''
        while self.__i < len(self.__s) and self.__s[self.__i] != '"':
            if self.__s[self.__i] == '\\':
                self.__i += 1
            s += self.__s[self.__i]
            self.__i += 1
        self.__i += 1
        return s

    def get_atom(self):
        s = ''
        while self.__i < len(self.__s) and self.is_atom_char(self.__s[self.__i]):
            s += self.__s[self.__i]
            self.__i += 1
        return s

    @staticmethod
    def is_atom_char(c):
        if c in '(){%*"\\ \x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f\x7f':
            return False
        return True

    @staticmethod
    def parse(s):
        parser = ImapDataParser(s)
        parser.skip_ws()
        result = parser.get_list_contents()
        if parser.__i != len(s):
            raise Exception(
                'Parsing of {0!r} stopped at {1} with {2!r}'.format(
                    s, parser.__i, result))
        assert parser.__i == len(s)
        return result

assert ImapDataParser.parse(r'  (\HasNoChildren) "/" "INBOX"') == ((r'\HasNoChildren',), '/', 'INBOX')
assert ImapDataParser.parse(r'  (\Noselect \HasChildren) "/" "[Gmail]"') == ((r'\Noselect', r'\HasChildren',), '/', '[Gmail]')
assert ImapDataParser.parse('407') == (407,)

password = getpass.getpass()

imap = imaplib2.IMAP4_SSL('imap.gmail.com', 993)
try:
    imap.login('stereotype441', password)
except imaplib2.IMAP4.error, e:
    print 'Login failure: {0!r}'.format(e.args[0])
    exit(1)

status, mailbox_names = imap.list()
assert status == 'OK'
# print 'Mailboxes:'
for n in mailbox_names:
    pass # print ImapDataParser.parse(n)

status, result = imap.select('Piglit', readonly=True)
assert status == 'OK'
assert len(result) == 1
parsed_result = ImapDataParser.parse(result[0])
assert len(parsed_result) == 1
num_messages = parsed_result[0]

#status, result = imap.search(None, 'ALL')
msg_num = 1
status, result = imap.fetch(msg_num, '(BODY.PEEK[HEADER])')
print result

# An "atom" is a sequence of any character except '(', ')', '{', '%',
# '*', '"', backslash, space, or a control character.
#
# A number is a sequence of digits.
#
# A string is either:
# - A literal string: '{', an octet count, '}', CR, LF, and then raw
#   octets.
# - A quoted string: '"', 7-bit characters excluding CR and LF (and
#   presumably '"'), '"'.
#
# A parenthesized list is:
# - '('
# - A sequence of data items (including, possibly, parenthesized
#   lists), delimited by spaces.
# - ')'
#
# A NIL is:
# - 'NIL'
