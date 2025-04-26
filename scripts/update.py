import argparse
from datetime import datetime

parser = argparse.ArgumentParser(description="Update the project.")

parser.add_argument("-t", "--tier", type=int, help="Tier of the update", required=True)
parser.add_argument(
    "-c", "--commit", action="store_true", help="Commit the update", default=False
)


def update_tier(tier):
    with open(f"updates/tier{tier}.md", "w") as f:
        f.write(f"# Tier {tier} Update Trigger\n\n")
        f.write(f"Update Time: {datetime.now().isoformat()}\n")


if __name__ == "__main__":
    args = parser.parse_args()
    update_tier(args.tier)
    print(f"Tier {args.tier} update file created.")

    if args.commit:
        import subprocess

        subprocess.run(["git", "add", f"updates/tier{args.tier}.md"])
        subprocess.run(
            ["git", "commit", "-m", f"chore: update tier {args.tier} packages"]
        )

        print(f"Tier {args.tier} update file committed.")
