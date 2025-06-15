import os
import subprocess
import time

DIDNT_REALLY_PULL_TEXT = "Already up to date."

while True:
    print("Attempting to pull")
    did_really_pull = subprocess.run(["git", "pull"], capture_output=True)

    if did_really_pull.returncode == 0:
        if DIDNT_REALLY_PULL_TEXT in did_really_pull.stdout.decode("utf-8"):
            print("Empty pull")
        else:
            print("Pulled successfully, re-running compose")
            try:
                if os.name == "nt":
                    # check compose call type either docker-compose or docker compose
                    if "docker-compose" in subprocess.run(["where", "docker-compose"], capture_output=True).stdout.decode("utf-8"):
                        subprocess.run(["docker-compose", "up", "-d"]).check_returncode()
                    else:
                        subprocess.run(["docker", "compose", "up", "-d"]).check_returncode()
                else:
                    # for bash / zsh / fish / etc.
                    if "docker-compose" in subprocess.run(["which", "docker-compose"], capture_output=True).stdout.decode("utf-8"):
                        subprocess.run(["docker-compose", "up", "-d"]).check_returncode()
                    else:
                        subprocess.run(["docker", "compose", "up", "-d"]).check_returncode()
            except subprocess.CalledProcessError as e:
                print(f"Error running compose: {e}")
    else:
        print("Pull failed")
    print("Sleeping for 10 seconds")
    time.sleep(10)