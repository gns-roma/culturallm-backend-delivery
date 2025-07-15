class TokenError(Exception):
    pass

class TokenExpired(TokenError):
    pass

class TokenInvalid(TokenError):
    pass

class TokenMissing(TokenError):
    pass