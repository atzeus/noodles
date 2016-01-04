from inspect import getargspec
from itertools import repeat


def _ordinal(n):
    """
    Ugly hack to get ordinal number. Is there an internationalized solution
    to this?
    """
    return "%d%s" % (n, "tsnrhtdd"[
        (n / 10 % 10 != 1) * (n % 10 < 4) * n % 10::4])


class MissingArgument(Exception):
    def __init__(self, func_name, pos, arg_name, doc):
        self.msg = "Missing {rank} argument '{arg}'"           \
                   " in scheduling function call to '{func}'."   \
            .format(rank=_ordinal(pos), arg=arg_name, func=func_name)
        self.doc = doc if doc else "This function is not documented"

    def __str__(self):
        return self.msg + "\n" + self.doc


class DuplicateArgument(Exception):
    def __init__(self, func_name, pos, arg_name, doc):
        self.msg = "Duplicate argument '{arg}'; already given as {rank}" \
                   " argument in call to '{func}'."                        \
            .format(arg=arg_name, rank=_ordinal(pos), func=func_name)
        self.doc = doc if doc else "This function is not documented"

    def __str__(self):
        return self.msg + "\n" + self.doc


class SpuriousArgument(Exception):
    def __init__(self, func_name, nargs, ngiven, doc):
        self.msg = "Too many arguments; '{func}' takes {nargs} regular" \
                   " arguments and does not take variadic arguments;" \
                   " {ngiven} arguments given."                       \
            .format(func=func_name, nargs=nargs, ngiven=ngiven)
        self.doc = doc if doc else "This function is not documented"

    def __str__(self):
        return self.msg + "\n" + self.doc


class SpuriousKeywordArgument(Exception):
    def __init__(self, func_name, doc):
        self.msg = "Function '{func}' does not take keyword arguments." \
            .format(func=func_name)
        self.doc = doc if doc else "This function is not documented"

    def __str__(self):
        return self.msg + "\n" + self.doc


def _pluck_arguments(f, args, kwargs):
    """
    Given a function, arguments and keyword arguments, match the
    values to the correct arguments of the function. Checks the validity
    of the function call explicitely and raises appropriate exception
    if the call doesn't match the function description.

    There is room here to implement a more strict analysis than python
    actually requires itself. I'm thinking of storing explicit type information
    in the function meta-data and checking that for compatibility with the
    arguments, which consequently should have a similar interface. Ideally
    this should be implemented conforming PEP-0484.

    @param args:
        The non-keyword arguments given at function call.
    @type args: Iterable

    @param kwargs:
        Keyword arguments given at function call.
    @type kwargs: dict

    @returns: 3-tuple of regular, variadic, keyword arguments
    @rtype: (list, list, dict)
    """
    spec = getargspec(f)
    n_args = len(spec.args)
    n_dflt = len(spec.defaults) if spec.defaults else 0

    # fact: regular arguments are non-optional

    # start with a blank slate
    regular = list(repeat(None,  n_args))

    # fill argument list with defaults
    if spec.defaults:
        regular[-n_dflt:] = spec.defaults

    # overwrite with given arguments
    n_given = min(len(args), n_args)
    regular[:n_given] = args[:n_given]

    # the variadic arguments are the remaining ones in *args
    variadic = args[n_given:]

    # if the user made a mistake or gave some regular arguments as keywords,
    # there may be a gap of regular arguments, not given nor provided by
    # defaults we should have: n_dflt + n_given >= n_args
    # We search the missing arguments in the kwargs and move them from
    # kwargs if found there, otherwise raise an exception.
    if (n_dflt + n_given) < n_args:
        missing = spec.args[n_given:n_args-n_dflt]
        for i, a in enumerate(missing):
            if a in kwargs:
                regular[n_given+i] = kwargs[a]
                del kwargs[a]
            else:
                raise MissingArgument(f.__name__, n_given+i, a, f.__doc__)

    # are there any arguments with default values given by keyword?
    if n_given < n_args:
        offset = n_args - min(n_dflt, (n_args - n_given))
        defaulted = spec.args[offset:]
        for i, a in enumerate(defaulted):
            if a in kwargs:
                regular[offset+i] = kwargs[a]
                del kwargs[a]

    # last, none of the keyword arguments should assign to an argument
    # that was already given as a regular one.
    for i, a in enumerate(spec.args[:n_given]):
        if a in kwargs:
            raise DuplicateArgument(f.__name__, i, a, f.__doc__)

    if spec.varargs is None and len(variadic) != 0:
        raise SpuriousArgument(f.__name__, n_args, len(args), f.__doc__)

    if len(variadic) == 0:
        variadic = None

    if spec.keywords is None and len(kwargs) != 0:
        raise SpuriousKeywordArgument(f.__name__, f.__doc__)

    if len(kwargs) == 0:
        kwargs = None

    return regular, variadic, kwargs
