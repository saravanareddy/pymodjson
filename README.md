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

