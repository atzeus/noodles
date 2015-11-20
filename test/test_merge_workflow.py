from nose.tools import raises

from noodles import *
from prototype import draw_workflow

def dummy(a, b, c, *args, **kwargs):
    pass

def test_is_workflow():
    assert is_workflow(Workflow(root=None, nodes={}, links={}))

@schedule
def value(a):
    return a

@schedule
def add(a, b):
    return a+b

@schedule
def sub(a, b):
    return a - b

def test_merge_workflow():
    A = value(1)
    B = value(2)
    C = add(A, B)

    assert is_workflow(C)
    C = get_workflow(C)
    A = get_workflow(A)
    B = get_workflow(B)
    assert C.nodes[C.root].bound_args.args == (Empty, Empty)
    assert (C.root, ArgumentAddress(ArgumentKind.regular, 'a', None)) in C.links[A.root]
    assert (C.root, ArgumentAddress(ArgumentKind.regular, 'b', None)) in C.links[B.root]

def test_binder():
    A = value(1)
    B = value(2)
    C = gather(A, B)

    C = get_workflow(C)
    A = get_workflow(A)
    B = get_workflow(B)

    assert is_workflow(C)
    assert C.nodes[C.root].bound_args.args == (Empty, Empty)
    assert (C.root, ArgumentAddress(ArgumentKind.variadic, 'a', 0)) in C.links[A.root]
    assert (C.root, ArgumentAddress(ArgumentKind.variadic, 'a', 1)) in C.links[B.root]

@schedule
def takes_keywords(s, **kwargs):
    pass

def test_with_keywords():
    A = value(1)
    B = value(2)
    C = takes_keywords(a = A, b = B, s = "regular!")
    C = get_workflow(C)
    A = get_workflow(A)
    B = get_workflow(B)

    assert is_workflow(C)
    assert C.nodes[C.root].bound_args.args     == ("regular!",)
    assert C.nodes[C.root].bound_args.kwargs   == {'a': Empty, 'b': Empty}

class Normal:
    pass

@schedule
class Scheduled:
    pass

def test_arg_by_ref():
    n = Normal()
    s = Scheduled()

    n.x = 4
    s.x = n
    n.x = 5
    s.y = n

    result = run(s)
    assert result.x.x == 4
    assert result.y.x == 5

@raises(TypeError)
def test_hidden_promise():
    a = Normal()
    b = Scheduled()
    c = Scheduled()

    a.x = b
    c.x = a

def test_tuple_unpack():
    a = Scheduled()
    b = Scheduled()

    a.x, a.y = 2, 3
    b.x, b.y = sub(a.x, a.y), sub(a.y, a.x)

    draw_workflow('tuple-test.png', b)
    result = run(b)
    assert result.x == -1
    assert result.y == 1
