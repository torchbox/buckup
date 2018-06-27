class BucketNameAlreadyInUse(ValueError):
    pass


class InvalidBucketName(ValueError):
    pass


class UserNameTaken(ValueError):
    pass


class InvalidUserName(ValueError):
    pass


class CredentialsNotFound(RuntimeError):
    pass


class CannotListAccountAliases(RuntimeError):
    pass


class CannotGetCurrentUser(RuntimeError):
    pass
