from model_w.project_maker.namer import smart_split_name


def test_smart_split_name():
    assert smart_split_name("") == tuple()
    assert smart_split_name("FooBar") == ("foo", "bar")
    assert smart_split_name("FooBarBaz42") == ("foo", "bar", "baz", "42")
    assert smart_split_name("_foo_bar") == ("foo", "bar")
    assert smart_split_name("foo") == ("foo",)
    assert smart_split_name(".foo-bar") == ("foo", "bar")
    assert smart_split_name("GDPR") == ("gdpr",)
    assert smart_split_name("YoloGDPR") == ("yolo", "gdpr")
    assert smart_split_name("YoloGDPR42") == ("yolo", "gdpr", "42")
    assert smart_split_name("GDPRFooBar") == ("gdpr", "foo", "bar")
    assert smart_split_name("_GDPRFooBar") == ("gdpr", "foo", "bar")
    assert smart_split_name("getUserByID") == ("get", "user", "by", "id")
    assert smart_split_name("getIDOfUser") == ("get", "id", "of", "user")
    assert smart_split_name("getUserID42") == ("get", "user", "id", "42")
    assert smart_split_name("makeMeASandwich") == ("make", "me", "a", "sandwich")
    assert smart_split_name("éléphant rose!!!") == ("elephant", "rose")
