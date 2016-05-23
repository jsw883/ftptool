"""
Auxiliary functions for ORM.
"""


# -----------------------------------------------------------------------------
# Printing
# -----------------------------------------------------------------------------

class Pretty(object):
    """Pretty printer with custom formatting.
    """

    def __init__(self, htchar="  ", lfchar="\n", indent=0):
        self.htchar = htchar
        self.lfchar = lfchar
        self.indent = indent
        self.types = {
            object: self.__class__.object_formatter,
            dict: self.__class__.dict_formatter,
            list: self.__class__.list_formatter,
            tuple: self.__class__.tuple_formatter,
        }

    def add_formatter(self, obj, formatter):
        self.types[obj] = formatter

    def get_formatter(self, obj):
        for type_ in self.types:
            if isinstance(obj, type_):
                return self.types[type_]
        return self.types[object]

    def __call__(self, value, **args):
        for key in args:
            setattr(self, key, args[key])
        return self.get_formatter(value)(self, value, self.indent)

    def object_formatter(self, value, indent):
        return repr(value)

    def dict_formatter(self, value, indent):
        items = []
        for key in sorted(value.keys()):
            s = (self.lfchar + self.htchar * (indent + 1) + repr(key) + ': ' +
                 self.get_formatter(value[key])(self, value[key], indent + 1))
            items.append(s)

        return '{%s}' % (','.join(items) + self.lfchar + self.htchar * indent)

    def list_formatter(self, value, indent):
        items = [
            self.lfchar + self.htchar * (indent + 1) +
            self.get_formatter(item)(self, item, indent + 1)
            for item in value
        ]
        return '[%s]' % (','.join(items) + self.lfchar + self.htchar * indent)

    def tuple_formatter(self, value, indent):
        items = [
            self.lfchar + self.htchar * (indent + 1) +
            self.get_formatter(value)(
                self, item, indent + 1)
            for item in value
        ]
        return '(%s)' % (','.join(items) + self.lfchar + self.htchar * indent)


def sphinx_pretty(obj, name='obj'):
    """Pretty dict embedding for Spinx (HTML).
    """

    pretty = Pretty(indent=2)
    print('.. code-block:: Javascript\n\n    {} = {}\n\n'.format(
        name, pretty(obj)))
