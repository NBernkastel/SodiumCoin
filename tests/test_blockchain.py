def inc(x):
    return x + 1


def smf():
    return 45

def test_inc():
    assert inc(3) == 4

def test_smf():
    assert smf() == 45
