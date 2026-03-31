import os
import shutil

PLATFORM = "{{ cookiecutter.platform }}"


def cleanup():
    if PLATFORM == "github":
        if os.path.exists(".gitlab-ci.yml"):
            os.remove(".gitlab-ci.yml")
    elif PLATFORM == "gitlab":
        if os.path.exists(".github"):
            shutil.rmtree(".github")


if __name__ == "__main__":
    cleanup()
