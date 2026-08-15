#!/usr/bin/env python3
"""
Generate a VAPID keypair for Web Push (daily verse reminders).

Run once:  python generate_vapid.py

Then add the two printed values to your Render environment variables:
    VAPID_PUBLIC_KEY=...
    VAPID_PRIVATE_KEY=...
and (recommended) set:
    VAPID_SUBJECT=mailto:you@example.com
    APP_PUSH_TOKEN=<a long random secret>

Keep the PRIVATE key secret - it lives only in your server env vars.
"""

import base64
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization


def b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def main():
    key = ec.generate_private_key(ec.SECP256R1())

    private_bytes = key.private_numbers().private_value.to_bytes(32, "big")
    public_bytes = key.public_key().public_bytes(
        serialization.Encoding.X962,
        serialization.PublicFormat.UncompressedPoint,
    )

    print("\nAdd these to your Render environment variables:\n")
    print("VAPID_PUBLIC_KEY=" + b64url(public_bytes))
    print("VAPID_PRIVATE_KEY=" + b64url(private_bytes))
    print("VAPID_SUBJECT=mailto:you@example.com   # replace with your email")
    print("APP_PUSH_TOKEN=" + base64.urlsafe_b64encode(__import__("os").urandom(24)).rstrip(b"=").decode("ascii"))
    print("\n(Keep VAPID_PRIVATE_KEY and APP_PUSH_TOKEN secret.)\n")


if __name__ == "__main__":
    main()
