pymodjson
===============================

pymodjson provides a framework to model JSON objects as classes in Python


* Free software: MIT license


## UseCase

```
Sample JSON response to be modeled in Python:
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


class User(PyModObject):
    name = StringType(alias="Name")
    age = NumberType(alias="Age")


class Student(User):
    courses_taken = ListType(alias="CoursesEnrolled")


class Professor(User):
    courses_taught = ListType(alias="CoursesTaught")


class UserList(PyModObject):
    users = ListType()


courses = ["CS 101"]
usr1 = Student(name="ABC", age=22)
usr2 = Professor(name="XYZ", age=44)
usr1.courses_taken = usr2.courses_taught = courses
my_user_list = UserList(users=[usr1, usr2])
my_user_list.to_json()  # Output would be similar to the JSON response above
```


## Available object types for modelling JSON data

```
StringType:
    supported_py_types: (str, unicode)

NumberType:
    supported_py_types: (int, float, long)

BooleanType:
    supported_py_types: bool

DateTimeType:
    supported_py_types: (datetime.date, datetime.datetime)

ListType:
    supported_types: (list, tuple)
    List type object can contain all of the types supported by the above
    mentioned types, and also the PyModObjectType within the input list
    or tuple

PyModObject:
    supported_types: PyModObject
    Use this type when there is a need to generate a JSON map object
    This type can be nested as many times as needed

Example:
class TestTypes(PyModObject):
    my_name = StringType()
    my_age = NumberType()
    am_i_a_robot = BooleanType()
    dob = DateTimeType()
    my_collections = ListType()
    my_object = PyModObjectType()

class TestObj(PyModObject):
    my_name = StringType()

test = TestTypes()
test.my_name = u'iRobot'
test.my_age = 0
test.am_i_a_robot = True
test.dob = datetime.datetime.now()
test.my_collections = ["", 0, False, ("", 0, False,), TestObj()]
test.my_object = TestObj(my_name="foo")
test.to_json()

Output:
{
    "am_i_a_robot": true,
    "dob": "Oct 15, 2016 - 20:36:47",
    "my_age": 0,
    "my_collections": [
        "",
        0,
        false,
        [
            "",
            0,
            false
        ],
        {}
    ],
    "my_name": "iRobot",
    "my_object": {
        "my_name": "foo"
    }
}
```


## Options for types:
```
alias:
The alias provided will be used as the key value for the json object,
instead of the declared property name in the model.
    Example:
    age = NumberType(alias="MyAge")  # JSON output will have: "MyAge": 22

suppress_if_null:
A property will not be visible in the JSON output if the property value
is 'None' or equates to null in python
    Example:
    age = NumberType(alias="MyAge", suppress_if_null=False)

not_null:
As the name indicates, null values are not permitted for a property
that has this flag set. The JSON dump is guaranteed to have this key,
if not, a ValueError is raised
    Example:
    age = NumberType(alias="MyAge", not_null=True)

validators:
User can set custom validators for each property being set.
The validator takes just the property being set as input and expects a
boolean value to be returned.
    Example:
    age = NumberType(validators=[lambda age_val: 0 < age_val < 120])

DateTimeType specific option:
dt_format:
In addition to the basic options, DateTimeType also accepts a dt_format
parameter. The format is "%b %d, %Y - %H:%M:%S" by default.
Refer datetime's strftime for formatting options.
    Example:
    dob = DateTimeType(dt_format="%m-%d-%Y")

```

## Testing

```
Refer to requirements_dev.txt for the required packages.

run 'py.test' from project root to run the tests under /tests
```


## Credits

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

Cookiecutter: https://github.com/audreyr/cookiecutter
`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage

Peterl Downs, for his simple tutorial on how to submit to PyPi.

