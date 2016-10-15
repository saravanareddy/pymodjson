# -*- coding: utf-8 -*-
"""
py mod json: Python Models -> JSON
Compatible with versions of Python2.6+ and Python3+

A module which provides a basic framework to model and structure JSON objects
as classes in Python.

Users can extend or nest PyModJson models to achieve the desired structure
for the responses. All while taking advantage of Python's class declaration
syntax to easily manage, document, validate and extend the models.

Use Case:
If you need to construct JSON responses which are made up of multiple other
inner JSON segments, you can define and initialize classes in Python that match
your JSON segments like shown below:

Sample JSON response:
{
    "users": [
        {
            "Name": "ABC",
            "Age": 22,
            "CoursesEnrolled": ["CS 101"]
        },
        {
            "Name": "XYZ",
            "Age": 44,
            "CoursesTaught": ["CS 101"]
        }
    ]
}

Python Classes:
class UserList(PyModObject):
    users = ListType()

class User(PyModObject):
    name = StringType(alias="Name")
    age = NumberType(alias="Age")

class Student(User):
    courses_taken = ListType(alias="CoursesEnrolled")

class Professor(User):
    courses_taught = ListType(alias="CoursesTaught")

usr1 = Student(name="ABC", age=22)
usr2 = Professor(name="XYZ", age=44)
courses = ["CS 101"]
usr1.courses_taken = usr2.courses_taught = courses
my_user_list = UserList(users=[usr1, usr2])
my_user_list.to_json()  # Output would be similar to the JSON response above
"""
import json
import datetime


class PyModObject(object):
    """
    PyModObject's purpose is to mimic a JSON object.
    Users can define custom Python models by inheriting this class and the
    desired key, value pairs of a JSON object can be defined as
    property(name) = PyModBaseType(value) pairs in the child class
    """
    def __init__(self, **kwargs):
        """
        Properties cannot be initialized without the property name(key)
        If some(or all) of the properties need to be set when the object
        is being initialized, they need to be sent as key value paris to
        the constructor
        """
        # Store the initial state of user defined model in _pymod__all_props
        # by filtering out all the magic methods from the list of attributes
        # We also need to filter out all the callables defined
        dir_map = dict((i, getattr(self, i)) for i in dir(self)
                       if not (i.startswith("__") and i.endswith("__")))
        self._pymod__all_props = dict((k, v) for k, v in dir_map.items()
                                      if not callable(v))
        self._pymod__active_props = set()

        # Iterate over all identified user defined properties
        for key, val in self._pymod__all_props.items():
            # Ensure the type of the property is valid
            if not isinstance(val, PyModBaseType):
                raise AttributeError("Invalid Type '%s' assigned to '%s'"
                                     % (type(val).__name__, key,))

        # Now iterate over all the properties passed in at initialization
        for key, val in kwargs.items():
            # Check if all the properties passed into the constructor exist in
            # the original model
            if key not in self._pymod__all_props:
                raise AttributeError("Undefined field '%s' passed to model"
                                     % key)
            else:
                # Now that the property is valid, ensure the 'value' passed in
                # is valid per the rules defined for the property in the model
                vcls = self._pymod__all_props.get(key)
                vcls.validate_value(key, val)
                # Set the validated value in this instance of the model
                self._pymod__active_props.add(key)
                setattr(self, key, val)

    def __setattr__(self, key, value):
        """
        Intercepts any modifications made to the instance and validates
        only if the key is found in the _pymod_props dict

        Raises a AttributeError if the key being set doesn't exist in the
        model or if there is a type mismatch between the value and property
        """
        # If modifying _pymod_props then just do the default operation
        if key.startswith("_pymod__") or \
           (key.startswith("__") and key.endswith("__")):
            return super(PyModObject, self).__setattr__(key, value)

        # Check if the property going to be set exists in the original set
        if key not in self._pymod__all_props:
            raise AttributeError("Property '%s' not defined in '%s' model"
                                 % (key, self.__class__.__name__,))
        # Get the validating instance for the property being set and set
        # the value if it's valid
        self._pymod__all_props.get(key).validate_value(key, value)
        self._pymod__active_props.add(key)
        super(PyModObject, self).__setattr__(key, value)

    def __delattr__(self, item):
        # If a property is being unset we need to adjust active props list
        if item in self._pymod__active_props:
            self._pymod__active_props.remove(item)
        super(PyModObject, self).__delattr__(item)

    def __getattribute__(self, item):
        if item.startswith("_pymod__"):
            return super(PyModObject, self).__getattribute__(item)

        if hasattr(self, "_pymod__all_props") and \
                item in self._pymod__all_props and \
                item not in self._pymod__active_props:
            return None
        return super(PyModObject, self).__getattribute__(item)

    def get_as_jsonable_object(self):
        """
        Returns a python dictionary representing current state of the model
        """
        response = {}
        # Iterate over all the properties defined in the model
        for key, val_config in self._pymod__all_props.items():
            # A property is allowed to be absent from the final JSON dump
            # as long as the 'not_null' option is'nt set for the property
            if key not in self._pymod__active_props:
                if val_config.not_null:
                    raise ValueError("Found null value for 'not_null' "
                                     "property '%s'" % key)
                # This property can be null, so continue to the next one
                continue
            # If a property is set, and if it's a null value, it can be
            # suppressed from the JSON dump if 'suppress_if_null' is set
            value = getattr(self, key)
            if value is None and val_config.suppress_if_null:
                # This property will not be output, so continue
                continue
            # Finally for all properties that will be present in the dump
            # check if an alias was passed in, if not use the name of the
            # property as the key in the JSON object
            if val_config.title:
                key = val_config.title
            response[key] = val_config.get_jsonable_value(value)
        return response

    def to_json(self):
        """
        Returns a valid JSON string. Any exceptions raised by json.dumps are
        sent downstream as is.
        """
        response = self.get_as_jsonable_object()
        return json.dumps(response)


class PyModBaseType(object):
    """
    This is the base class for all the PyModJSON types, and all the common
    attributes for the properties are set here in the constructor.

    Each sub type inheriting from this base class will need to provide a
    tuple of valid python types that can be accepted as input for that type
    by defining 'supported_py_types'
    Example:
        supported_py_types = (int, float, long,)
    """
    supported_py_types = None

    def __init__(self, alias=None, suppress_if_null=True, not_null=False,
                 validators=()):
        """"
        alias:
        The alias provided will be used as the key value for the json object,
        instead of the declared property name in the model.

        suppress_if_null:
        A property will not be visible in the JSON output if the property value
        is 'None' or equates to null in python

        not_null:
        As the name indicates, null values are not permitted for a property
        that has this flag set. The JSON dump is guaranteed to have this key,
        if not, a ValueError is raised

        validators:
        User can set custom validators for each property being set.
        The validator takes just the property being set as input and expects a
        boolean value to be returned.
            Example:
            age = NumberType(validators=[lambda age_val: 0 < age_val < 120])
        """
        self._value = None
        self.title = alias
        self.suppress_if_null = suppress_if_null
        self.not_null = not_null
        self.validators = validators

    def validate_value(self, key, val):
        """
        Called to check if a property value satisfies all the rules assigned
        to it at the time of declaration.

        Exceptions caused by user provided validator callables are passed down
        as is. A ValueError with an appropriate message is raised if any of the
        predefined rules are violated by the value
        """
        # Execute all user defined validator callables(if any) and ensure all
        # return a value that equates to true.
        custom_validated = all(validator(val) for validator in self.validators)
        if val is not None and not custom_validated:
            raise ValueError("Supplied Validator for property '%s' failed to "
                             "validate value: %s" % (key, val,))
        if val is None and self.not_null:
            raise ValueError("Found null value for 'not_null' property '%s'"
                             % key)
        # Values which are not of a know type will not be processed, since
        # the serialization to JSON will throw an exception.
        if val is not None and not isinstance(val, self.supported_py_types):
            raise ValueError("Object type '%s' is not supported by '%s"
                             % (type(val).__name__, self.__class__.__name__,))

    def get_jsonable_value(self, val):
        """
        Returns a value that can be serialized by json.dumps
        """
        return val


class StringType(PyModBaseType):
    supported_py_types = (str, unicode,)


class NumberType(PyModBaseType):
    supported_py_types = (int, float, long,)


class BooleanType(PyModBaseType):
    supported_py_types = (bool,)


class DateTimeType(PyModBaseType):
    supported_py_types = (datetime.date, datetime.datetime,)

    def __init__(self, alias=None, hide_if_null=True, not_null=False,
                 validators=(), dt_format="%b %d, %Y - %H:%M:%S"):
        """
        In addition to the basic options, DateTimeType also accepts a dt_format
        parameter. The format is "%b %d, %Y - %H:%M:%S" by default.
        Refer datetime's strftime for formatting options.
        """
        super(DateTimeType, self).__init__(alias, hide_if_null, not_null,
                                           validators)
        self.dt_format = dt_format

    def get_jsonable_value(self, val):
        """
        Converts the datetime object to string using the user supplied format.
        'None' is returned if value is not set
        ValueError is raised if 'dt_fomat' could not be understood by strftime
        """
        if val:
            return datetime.datetime.strftime(val, self.dt_format)


class ListType(PyModBaseType):
    supported_py_types = (list, tuple)

    def _flatten(self, val_list):
        """
        A helper function to flatten a list.
        """
        for val in val_list:
            if isinstance(val, self.supported_py_types):
                for i in self._flatten(val):
                    yield i
            else:
                yield val

    def validate_value(self, key, val):
        """
        Scans all the items inside the list recursively and validates them
        A ValueError is raised if any items in the list is not supported.
        """
        # Perform the basic checks supported in the base class
        super(ListType, self).validate_value(key, val)
        # Make a list of all supported types
        supported_types = (str, unicode, int, float, long, bool, PyModObject,)
        # Now recursively iterate and ensure all of the values are supported
        for item in self._flatten(val):
            if not isinstance(item, supported_types):
                raise ValueError("Invalid item of type '%s' found in '%s'"
                                 % (type(item).__name__, key,))

    def get_jsonable_value(self, val):
        """
        Expand the value recursively and return a fully jsonable list that
        maintains the order of elements in the input list.
        """
        ret_val = []
        for v in val:
            # If the inner value is a list or a tuple, add the value by
            # recursively expanding it
            if isinstance(v, self.supported_py_types):
                ret_val.append(self.get_jsonable_value(v))
            # If the value is a PyModObject, simply request a dictionary
            # representation of the object and append to list
            elif isinstance(v, PyModObject):
                ret_val.append(v.get_as_jsonable_object())
            # All other valid types can be added as is
            else:
                ret_val.append(v)
        return ret_val


class PyModObjectType(PyModBaseType):
    """
    Use this type when there is a need to generate a JSON map object
    This type can be nested as many times as needed
    """
    supported_py_types = (PyModObject,)

    def get_jsonable_value(self, val):
        return val.get_as_jsonable_object()
