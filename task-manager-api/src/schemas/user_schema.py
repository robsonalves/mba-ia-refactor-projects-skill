from marshmallow import Schema, fields, validate

from src.config.constants import PASSWORD_MIN, USER_ROLES


class UserSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=PASSWORD_MIN))
    role = fields.Str(load_default="user", validate=validate.OneOf(USER_ROLES))


class UserUpdateSchema(Schema):
    name = fields.Str(validate=validate.Length(min=1, max=100))
    email = fields.Email()
    password = fields.Str(validate=validate.Length(min=PASSWORD_MIN))
    role = fields.Str(validate=validate.OneOf(USER_ROLES))
    active = fields.Bool()


class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True)


user_create_schema = UserSchema()
user_update_schema = UserUpdateSchema()
login_schema = LoginSchema()
