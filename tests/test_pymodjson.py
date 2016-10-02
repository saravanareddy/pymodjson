#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_pymodjson
----------------------------------

Tests for `pymodjson` module.
"""

import json
import pytest
from datetime import datetime
from dummy_test_models import *
from pymodjson import pymodjson


class TestPyModObjectCreation(object):

    def test_class_init_with_parameters(self):
        dt = datetime.today()
        user = User(name="Test", age=44, join_dt=dt)
        assert user.name == "Test"
        assert user.age == 44
        assert user.join_dt == dt

    def test_class_init_without_parameters(self):
        user = User()
        user.age = 44
        user.name = "Test"
        assert user.name == "Test"
        assert user.age == 44

    def test_class_init_with_partial_parameters(self):
        user = User(name="Test")
        user.age = 44
        assert user.age == 44
        assert user.name == "Test"

    def test_inherited_class_init(self):
        prof = Professor(name="Test", age=44, courses=['CS 101'])
        assert prof.name == "Test"
        assert prof.age == 44
        assert prof.courses == ['CS 101']

    def test_class_init_raise_attribute_error(self):
        with pytest.raises(AttributeError):
            User(name="Test", Age=44)

        with pytest.raises(AttributeError):
            user = User()
            user.Age = 44

    def test_class_init_with_invalid_values(self):
        with pytest.raises(ValueError):
            User(name=None)

        with pytest.raises(ValueError):
            UserList(users=[set()])

    def test_class_init_with_invalid_type(self):
        class Test(pymodjson.PyModObject):
            invalid = set()

        with pytest.raises(AttributeError):
            Test()


class TestPyModObjectPropertyTypes(object):
    """
    Tests to ensure 'get_jsonable_value' is returning the right values and
    not corrupting them in any way.
    """
    def test_string_property(self):
        string = pymodjson.StringType()
        regular_str = "test"
        unicode_str = u"test"
        string.validate_value("test", regular_str)
        string.validate_value("test", unicode_str)
        assert string.get_jsonable_value(regular_str) == regular_str
        assert string.get_jsonable_value(unicode_str) == unicode_str

        with pytest.raises(ValueError):
            string.validate_value("test", 1)

    def test_number_property(self):
        number = pymodjson.NumberType()
        test_int = 0
        test_float = 0.0
        number.validate_value("test", test_float)
        number.validate_value("test", test_int)
        assert number.get_jsonable_value(test_int) == test_int
        assert number.get_jsonable_value(test_float) == test_float

        with pytest.raises(ValueError):
            number.validate_value("test", '1')

    def test_boolean_property(self):
        boolean = pymodjson.BooleanType()
        boolean.validate_value("test", True)
        boolean.validate_value("test", False)
        assert boolean.get_jsonable_value(True)
        assert not boolean.get_jsonable_value(False)

        with pytest.raises(ValueError):
            boolean.validate_value("test", 1)

    def test_datetime_property(self):
        dt_format = "%d/%m/%Y"
        dt = pymodjson.DateTimeType(dt_format=dt_format)
        test_dt = datetime.today()
        dt.validate_value("test", test_dt)
        assert dt.get_jsonable_value(test_dt) == datetime.strftime(test_dt, dt_format)

        with pytest.raises(ValueError):
            dt.validate_value("test", "01/01/2011")

    def test_list_property(self):
        class Test(pymodjson.PyModObject):
            test = pymodjson.BooleanType()

        test_list = pymodjson.ListType()
        # Since 'test' property is not set: Test() -> {}
        test_input = [[1], Test()]
        test_list.validate_value("test", test_input)
        assert test_list.get_jsonable_value(test_input) == [[1], {}]

        with pytest.raises(ValueError):
            test_list.validate_value("test", [{}])

    def test_pymod_property(self):
        class Test(pymodjson.PyModObject):
            test = pymodjson.BooleanType()

        test = Test(test=True)
        pymod_obj = pymodjson.PyModObjectType()
        assert pymod_obj.get_jsonable_value(test) == {"test": True}

        with pytest.raises(ValueError):
            pymod_obj.validate_value("test", "1")


class TestPyModObjectOutput(object):

    def test_output_on_properties_set_at_initialization(self):
        kwargs = {"name": "Test", "age": 44}
        user = User(**kwargs)
        assert user.to_json() == json.dumps(kwargs)

    def test_output_on_properties_set_post_initialization(self):
        output = json.dumps({"name": "Test", "age": 44})
        user = User()
        user.name = "Test"
        user.age = 44
        assert user.to_json() == output

    def test_output_on_properties_with_alias(self):
        user = Student(name="Test", courses=["101"])
        output = '{"name": "Test", "courses_enrolled": ["101"]}'
        assert user.to_json() == output

    def test_output_on_suppress_if_null_property(self):
        user = Student(name="Test", age=None)
        output = '{"name": "Test"}'
        assert user.to_json() == output

    def test_raise_value_error_for_never_null_properties(self):
        with pytest.raises(ValueError):
            User().to_json()


if __name__ == "__main__":
    pytest.main()
