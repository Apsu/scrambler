import hmac


class Auth():
    "HMAC-based message authentication"

    def __init__(self, key, data):
        # Store parameters
        self.key = key
        self.data = data

        # Compute this node's digest
        self.digest = hmac.new(self.key, self.data).hexdigest()

    def digest(self):
        "Get our digest"

        return self.digest

    def verify(self, digest, data):
        "Verify specified digest matches data with our key"

        return (hmac.new(self.key, data) == digest)
