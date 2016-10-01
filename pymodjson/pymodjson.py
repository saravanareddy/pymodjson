# -*- coding: utf-8 -*-
"""
py mod json: Python Models -> JSON

A module which provides a basic framework to model and structure JSON objects
as classes in Python.

Users can extend or nest PyModJson models to achieve the desired structure
for the responses. All while taking advantage of Python's class declaration
syntax to easily manage, document, validate and extend the models.

Compatible with versions of Python2.6+ and Python3+

Use Case:
If you need to construct a JSON response which is made up of multiple other
inner JSON segments, you can define and document classes in python that match
your JSON segments like show below:

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
class UserList(pymodjson.PyModObject):
    users = pymodjson.ListType()

class User(pymodjson.PyModObject):
    name = pymodjson.StringType(alias="Name")
    age = pymodjson.NumberType(alias="Age")

class Student(User):
    courses_taken = pymodjson.ListType(alias="CoursesEnrolled")

class Professor(User):
    courses_taught = pymodjson.ListType(alias="CoursesTaught")

usr1 = Student(name="ABC", age=22)
usr2 = Professor(name="XYZ", age=44)
courses = ["CS 101"]
usr1.courses_taken = usr2.courses_taught = courses
my_user_list = UserList(users=[usr1, usr2])
my_user_list.json()  # This should be equivalent to the example structure
"""
import json
import inspect
import datetime


class PyModType(object):
    """
    This is the base class for all the PyModJSON types, and all the common
    attributes for the properties are set here in the constructor.

    Each sub type inheriting from this base class will need to provide a
    tuple of valid python types that can be accepted as input for that type
    by defining 'supported_py_types'
    Example:
        supported_py_types = (int, float, long,)
    """
    def __init__(self, alias=None, suppress_if_null=True, never_null=False,
                 validators=[]):
        """"
        alias:
        The alias provided will be used as the key value for the json object,
        instead of the declared property name in the model.

        suppress_if_null:
        A property will not be visible in the JSON output if the property value
        is 'None' or equates to null in python

        never_null:
        As the name indicates, null values are not permitted for a property
        that has this flag set. The JSON dump is guaranteed to have this key,
        if not, a ValueError is raised

        vallidators:
        User can set custom validators for each property being set.
        The validator takes just the property being set as input and expects a
        boolean value to be returned.
            Example:
            age = NumberType(validators=[lambda age_val: 0 < age_val < 120])
        """
        self.title = alias
        self.suppress_if_null = suppress_if_null
        self.never_null = never_null
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
        if val is None and self.never_null:
            raise ValueError("Found null value for 'never_null' property '%s'"
                             % key)
        # Values which are not of a know type will not be processed, since
        # the serialization to JSON will throw an exception.
        if val is not None and not isinstance(val, self.supported_py_types):
            raise ValueError("Expected object of type '%s' found '%s' instead"
                             % (self.__class__.__name__, type(val).__name__,))
        return True

    def get_jsonable_value(self, val):
        """
        Returns a value that can be serialized by json.dumps
        """
        return val


class PyModObject(object):
    """
    PyModObject's purpose is to mimic a JSON object.
    Users can define custom Ptyhon models by inherting this class and the
    key, value pairs of a JSON object can be defined as property(name),
    PyModType(value)
    """
    def __init__(self, **kwargs):
        """
        Properties cannot be initialized without the property name(key)
        If some(or all) of the properties need to be set when the object
        is being initialized, they need to be sent as key value paris to
        the constructor
        """
        # Store the initial state of the user defined model in _pymod_state
        # Ensure only non callables are being identified
        self._pymod_state = dict((i, getattr(self, i)) for i in dir(self)
                                 if isinstance(getattr(self, i), PyModType))

        # Iterate over all identified user defined properties
        for key, val in self._pymod_state.items():
            # Ensure the type of the property is valid
            if not isinstance(val, PyModType):
                raise ValueError("Invalid Type '%s' assigned to '%s'"
                                 % (type(val).__name__, key,))

            # If for this instance of the model if the property has not
            # been defined(yet), remove it from the property list
            if key not in kwargs:
                self.delete_attribute(key)

        # Now iterate over all the properties passes in at model initialization
        for key, val in kwargs.items():
            # Check if all the properties passed into the constructor exist in
            # the original model
            if key not in self._pymod_state:
                raise AttributeError("Undefined field '%s' passed to model"
                                     % key)
            else:
                # Now that the property is valid, ensure the 'value' passed in
                # is valid per the rules defined for the property in the model
                vcls = self._pymod_state.get(key)
                vcls.validate_value(key, val)
                # Set the validated value in this instance of the model
                setattr(self, key, val)

    def __setattr__(self, key, value):
        """
        Intercepts any modifications made to the instance and validates
        the key(property name) and the value

        Raises a ValueError if the key being set doesn't exist in the model
        """
        # If modifying _pymod_state then just do the default operation
        if key == "_pymod_state" or \
           (key.startswith("__") and key.endswith("__")):
            return super(PyModObject, self).__setattr__(key, value)

        # Check if the property going to be set exists in the original set
        if key not in self._pymod_state:
            raise ValueError("Uable to find property '%s' in '%s' model"
                             % (key, self.__class__.__name__,))
        # Get the validating instance for the property being set and set
        # the value if it's valid
        self._pymod_state.get(key).validate_value(key, value)
        super(PyModObject, self).__setattr__(key, value)

    def delete_attribute(self, key):
        """
        Since some of the properties can be derived from another class
        we go over the classes in the MRO and delete the key when found
        """
        for cl in inspect.getmro(self.__class__):
            if key in cl.__dict__:
                delattr(cl, key)

    def get_as_jsonable_object(self):
        """
        Returns a python dictionary representing the current state of the model
        """
        response = {}
        # Iterate over all the properties defined in the model
        for key, val_config in self._pymod_state.items():
            # A property is allowed to be absent from the final JSON dump
            # as long as the 'never_null' option is'nt set for the property
            if not hasattr(self, key):
                if val_config.never_null:
                    raise ValueError("Found null value for 'never_null' "
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

    def json(self):
        """
        Returns a valid JSON string. Any exceptions occuring inside json.dumps
        are sent downstream as is.
        """
        response = self.get_as_jsonable_object()
        return json.dumps(response)


class DateTimeType(PyModType):
    supported_py_types = (datetime.date, datetime.datetime,)

    def __init__(self, alias=None, hide_if_null=True, never_null=False,
                 validators=[], format="%b %d, %Y - %H:%M:%S"):
        """
        In addition to the basic options, DateTimeType also accepts a format
        option. The format is "%b %d, %Y - %H:%M:%S" by default.
        Refer datetime's strftime for formatting options.
        """
        super(DateTimeType, self).__init__(alias, hide_if_null, never_null,
                                           validators)
        self.format = format

    def get_jsonable_value(self, val):
        """
        Converts the datetime object to string using the initialized format.
        """
        return datetime.datetime.strftime(val, self.format)


class ListType(PyModType):
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
        maintains the order of elements in the input value.
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


class PyModType(PyModType):
    """
    Use this type when there is a need to generate a JSON map object
    This type can be nested as many times as needed
    """
    supported_py_types = (PyModObject,)

    def get_jsonable_value(self, val):
        return val.get_as_jsonable_object()


class StringType(PyModType):
    supported_py_types = (str, unicode,)


class NumberType(PyModType):
    supported_py_types = (int, float, long,)


class BooleanType(PyModType):
    supported_py_types = (bool,)

