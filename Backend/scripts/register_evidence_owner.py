"""Explicit legacy receipt registration. Dry-run unless --apply is supplied.

Verify the upload's original owner from trusted records before using this tool.
Do not infer ownership solely from a client-supplied ledger filename.
"""
import argparse

from app.services.evidence_storage import _paths, register_existing_receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--filename", required=True)
    parser.add_argument("--merchant-id", required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    path, metadata = _paths(args.filename)
    if not path.is_file() or path.is_symlink() or metadata.exists() or not args.merchant_id.strip():
        parser.error("File must exist, be unregistered and have an explicitly verified owner.")
    if not args.apply:
        print("Dry-run: one receipt would be assigned. Verify its original owner, then repeat with --apply.")
        return
    register_existing_receipt(args.filename, args.merchant_id)
    print("Registered one receipt. No ledger rows were changed.")


if __name__ == "__main__":
    main()
