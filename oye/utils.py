from django.contrib.auth.tokens import PasswordResetTokenGenerator

class TokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        # Customize how the hash value for the token is generated
        return (
            str(user.pk) +
            str(timestamp) +
            str(user.password)  # Use hashed password or another unique field
        )

password_reset_token = TokenGenerator()
