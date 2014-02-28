import hmac


class Auth():
    "HMAC-based message authentication"

    def __init__(self, key, data):
        # Store parameters
        self._key = key
        self._data = data

        # Compute this node's digest
        self._digest = hmac.new(str(self._key), str(self._data)).hexdigest()

    def digest(self):
        "Get our digest"

        return self._digest

    def verify(self, digest, data):
        "Verify specified digest matches data with our key"

        return hmac.new(str(self._key), str(data)).hexdigest() == digest
