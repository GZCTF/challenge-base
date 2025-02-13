import os
import json

with open("scripts/template.yml", "r") as f:
    ACTION_TEMPLATE = f.read()


def info(content):
    leading = "\033[1;32m[+] \033[0m"
    bold_content = f"\033[1m{content}\033[0m"
    print(f"{leading}{bold_content}")


def heading(content):
    leading = f"\033[1;33m[*] {content}\033[0m"
    print(leading)


def error(content):
    leading = f"\033[1;31m[!] {content}\033[0m"
    print(leading)
    exit(1)


DEFAULT_CONFIG = {
    "tag": "latest",
    "action_name": None,
    "action_file": None,
    "dockerfile": "Dockerfile",
    "depends_on": None,
}


def gen_action(chall_dir, name):
    global ACTION_TEMPLATE

    for conf in json.load(open(f"{chall_dir}/config.json", "r")):
        # merge with default config
        conf = {**DEFAULT_CONFIG, **conf, "name": name}

        if conf["action_file"] is None:
            conf["action_file"] = conf["name"]

        if conf["action_name"] is None:
            error("action_name is required in config.json")

        if conf["depends_on"] is None:
            conf["depends_on"] = []

        conf["depends_on"].append(f"base/{conf['name']}/**")

        info(f"Generating action: {json.dumps(conf, indent=2)}")

        result = ACTION_TEMPLATE.replace("<ACTION_NAME>", conf["action_name"])
        result = result.replace("<ACTION_FILE>", conf["action_file"])
        result = result.replace("<DOCKERFILE>", conf["dockerfile"])
        result = result.replace("<TAG>", conf["tag"])
        result = result.replace("<NAME>", conf["name"])
        result = result.replace(
            "#<DEPENDENCY_PATHS>",
            "\n      ".join([f'- "{i}"' for i in conf["depends_on"]]),
        )

        file_path = f".github/workflows/base.{conf['action_file']}.yml"
        info(f"Writing action to {file_path}")
        with open(file_path, "w") as f:
            f.write(result)


if __name__ == "__main__":
    info("Generating GitHub actions...")

    for root, _, files in os.walk("base"):
        if "config.json" in files:
            name = root.split("/")[-1]
            heading(f"{f' {name} '.center(60, '=')}")
            try:
                gen_action(root, name)
            except Exception as e:
                error(e)
