===============================
pymodjson
===============================

pymodjson provides a framework to model JSON objects as classes in Python


* Free software: MIT license
* Documentation: https://pymodjson.readthedocs.io.


UseCase
-------

Sample JSON response modeled in Python:
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


Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage

