from pymodjson import pymodjson


class User(pymodjson.PyModObject):
    name = pymodjson.StringType(never_null=True)
    age = pymodjson.NumberType(suppress_if_null=True)
    join_dt = pymodjson.DateTimeType(dt_format="%d/%m/%Y")


class Student(User):
    courses = pymodjson.ListType(alias="courses_enrolled")


class Professor(User):
    courses = pymodjson.ListType(alias="courses_taught")


class UserList(pymodjson.PyModObject):
    users = pymodjson.ListType(validators=[lambda obj: isinstance(obj, User)])
