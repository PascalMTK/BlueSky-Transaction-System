import bcrypt
from django.contrib.auth.hashers import BasePasswordHasher
from django.utils.crypto import constant_time_compare


class LaravelBcryptHasher(BasePasswordHasher):
    """Verifies Laravel bcrypt hashes ($2y$...) and creates new ones."""
    algorithm = 'laravel_bcrypt'

    def salt(self):
        return ''

    def encode(self, password, salt):
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=10))
        return hashed.decode()

    def verify(self, password, encoded):
        try:
            pwd_bytes = password.encode('utf-8')
            # Laravel uses $2y$, Python bcrypt uses $2b$ — both are compatible
            encoded_bytes = encoded.encode('utf-8').replace(b'$2y$', b'$2b$')
            return bcrypt.checkpw(pwd_bytes, encoded_bytes)
        except Exception:
            return False

    def safe_summary(self, encoded):
        return {'algorithm': self.algorithm, 'hash': encoded[:20] + '...'}

    def must_update(self, encoded):
        return False

    def harden_runtime(self, password, encoded):
        pass

    @staticmethod
    def is_laravel_hash(encoded):
        return encoded.startswith('$2y$') or encoded.startswith('$2b$')
