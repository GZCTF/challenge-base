import os

if os.path.exists("/home/ctf/flag"):
    with open("/home/ctf/flag", "r") as f:
        flag = f.read().strip()

    if flag:
        print(f"Flag: {flag}")
        exit(0)

print("There is no flag here")
exit(1)
