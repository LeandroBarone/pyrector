from pyrector.base import WithUid

import gc
from unittest.mock import patch


def reset_WithUid():
    WithUid.KNOWN_SUBCLASSES = []
    WithUid.CLASS_COUNTERS = {}
    gc.collect()


def test_each_class_has_its_own_id_num():
    class Subclass1(WithUid):
        def __init__(self):
            super().__init__()

    class Subclass2(WithUid):
        def __init__(self):
            super().__init__()

    class Subclass3(Subclass1):
        def __init__(self):
            super().__init__()

    assert Subclass1.get_next_id_num() == 1
    assert Subclass2.get_next_id_num() == 1
    assert Subclass3.get_next_id_num() == 1

    assert Subclass1.get_next_id_num() == 2
    assert Subclass2.get_next_id_num() == 2
    assert Subclass3.get_next_id_num() == 2


def test_get_subclasses():
    class MyClass(WithUid):
        pass

    class MySubclass1(MyClass):
        pass

    class MySubclass2(MyClass):
        pass

    assert MyClass.get_subclasses() == [MySubclass1, MySubclass2, MyClass]

    del MySubclass1, MySubclass2, MyClass


def test_uids_are_unique():
    class MySubclass1(WithUid):
        pass

    class MySubclass2(WithUid):
        pass

    assert MySubclass1.get_uid() != MySubclass2.get_uid()

    del MySubclass1, MySubclass2


def test_uids_are_deterministic_for_the_same_number_of_subclasses():
    def env1():
        reset_WithUid()

        class MyClass(WithUid):
            pass

        class MySubclass(MyClass):
            pass

        uid = MySubclass().uid
        return uid

    def env2():
        reset_WithUid()

        class AnotherClass(WithUid):
            pass

        class AnotherSubclass(AnotherClass):
            pass

        uid = AnotherSubclass().uid
        return uid

    uid1 = env1()
    uid2 = env2()

    assert uid1.split('_')[1] == uid2.split('_')[1]


def test_uids_for_larger_number_of_subclasses():
    class MyClass(WithUid):
        pass

    WithUid.CLASS_COUNTERS[str(MyClass)] = 1000

    uid = MyClass.get_uid()

    assert uid.split('_')[0] == 'MyClass1001'
    assert len(uid.split('_')[1]) >= 16


@patch('pyrector.base.WithUid.ADJECTIVES', ['A', 'B'])
@patch('pyrector.base.WithUid.NOUNS', ['1', '2'])
def test_codename_from_seed():
    reset_WithUid()
    results = [WithUid.codename_from_id_num(i, 0) for i in range(6)]
    assert results == ['B2', 'B1', 'A2', 'A1', 'B2', 'B1']
