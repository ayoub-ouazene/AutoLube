"""
Generate a bcrypt hash for the admin password.

Usage:
    python -m scripts.hash_password

You'll be prompted for the password. The script prints the hash line to
paste into .env.
"""

import sys

import bcrypt


MIN_LENGTH = 12


def main() -> int:
    print("AutoLube admin password hasher")
    print("-------------------------------")
    print("You'll be prompted for the password. Nothing is written to disk —")
    print("the hash is printed for you to paste into .env manually.")
    print()

    password = input("Admin password: ").strip()
    if not password:
        print("Error: password cannot be empty.", file=sys.stderr)
        return 1

    confirm = input("Confirm password: ").strip()
    if password != confirm:
        print("Error: passwords do not match.", file=sys.stderr)
        return 1

    encoded = password.encode("utf-8")
    if len(encoded) > 72:
        print(
            f"Error: password is {len(encoded)} bytes but bcrypt supports at most 72.",
            file=sys.stderr,
        )
        return 1

    if len(password) < MIN_LENGTH:
        print(
            f"Warning: password is only {len(password)} chars. "
            f"Use at least {MIN_LENGTH} for real security.",
            file=sys.stderr,
        )

    hashed = bcrypt.hashpw(encoded, bcrypt.gensalt(rounds=12)).decode("utf-8")

    print()
    print("Add this line to your .env file:")
    print()
    print(f"ADMIN_PASSWORD_HASH={hashed}")
    print()
    print("If you don't have a JWT secret yet, generate one with:")
    print("  python -c \"import secrets; print(secrets.token_urlsafe(64))\"")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())