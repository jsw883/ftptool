"""
Auxiliary functions for the package :mod:`ftptool`, including some generally
handy snippets of code for pretty printing. This should eventually be moved
to another package, providing a single repository of generally handy snippets
that can be imported by every other repository.
"""


# -----------------------------------------------------------------------------
# Printing
# -----------------------------------------------------------------------------

class Pretty(object):
    """Pretty printer with custom formatting.

    Pretty is a pretty printing class that allows output to be cusomtized
    for each object type, custom horizonal tab and line feed strings, and
    indenting. Custom formatters are already specified for :class:`dict`,
    :class:`list`, and :class:`tuple` objects, giving a generic line feed
    scaffold, and a default formatter for :class:`object` is included.
    """

    def __init__(self, htchar='  ', lfchar='\n', indent=0):
        """Return an instance of Pretty.

        Args:
            htchar (str): horizontal tab string
            lfchar (str): line feed string
            indent (int): number of htchar to prepend to output (entirety)
        """
        self.htchar = htchar
        self.lfchar = lfchar
        self.indent = indent
        self.types = {
            object: self.__class__.object_formatter,
            dict: self.__class__.dict_formatter,
            list: self.__class__.list_formatter,
            tuple: self.__class__.tuple_formatter,
        }

    def __call__(self, value, **kwargs):
        """Allows class instance to be invoked as a function for formatting.

        Args:
            value (object): object to be formatted
            **kwargs: named arguments to be assigned as attributes

        Returns:
            str: pretty formatted string ready to be printed
        """
        for key, value in kwargs.items():
            setattr(self, key, value)
        return self.get_formatter(value)(self, value, self.indent)

    def add_formatter(self, obj, formatter):
        """Adds a custom formatter for an arbitrary object type.

        Args:
            obj (type): object type
            formatter (function): custom formatter function with signature
                formatter(value, indent)
        """
        self.types[obj] = formatter

    def get_formatter(self, obj):
        """Retrieves the custom formatter for the object type (or default).
        """
        for type_ in self.types:
            if isinstance(obj, type_):
                return self.types[type_]
        return self.types[object]

    def object_formatter(self, value, indent):
        """Default object formatter.
        """
        return repr(value)

    def dict_formatter(self, value, indent):
        """Dictionary formatter.
        """
        items = []
        for key in sorted(value.keys()):
            s = (self.lfchar + self.htchar * (indent + 1) + repr(key) + ': ' +
                 self.get_formatter(value[key])(self, value[key], indent + 1))
            items.append(s)

        return '{%s}' % (','.join(items) + self.lfchar + self.htchar * indent)

    def list_formatter(self, value, indent):
        """List formatter.
        """
        items = [
            self.lfchar + self.htchar * (indent + 1) +
            self.get_formatter(item)(self, item, indent + 1)
            for item in value
        ]
        return '[%s]' % (','.join(items) + self.lfchar + self.htchar * indent)

    def tuple_formatter(self, value, indent):
        """Tuple formatter.
        """
        items = [
            self.lfchar + self.htchar * (indent + 1) +
            self.get_formatter(value)(
                self, item, indent + 1)
            for item in value
        ]
        return '(%s)' % (','.join(items) + self.lfchar + self.htchar * indent)


def sphinx_pretty(obj, name='obj'):
    """Pretty dict to RST.

    Args:
        obj (object): object to be formatted
        name (str): object name to prepend

    Return:
        str: RST code block, indented and formatted
    """

    pretty = Pretty(indent=2)
    print('.. code-block:: Javascript\n\n    {} = {}\n\n'.format(
        name, pretty(obj)))
