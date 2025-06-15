import os
import logging
import subprocess
import time

logger = logging.getLogger(__name__)
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

DIDNT_REALLY_PULL_TEXT = "Already up to date."

while True:
    logger.info("Attempting to pull")
    did_really_pull = subprocess.run(["git", "pull"], capture_output=True)

    if did_really_pull.returncode == 0:
        if DIDNT_REALLY_PULL_TEXT in did_really_pull.stdout.decode("utf-8"):
            logger.info("Empty pull")
        else:
            logger.info("Pulled successfully, re-running compose")
            try:
                if os.name == "nt":
                    # check compose call type either docker-compose or docker compose
                    if "docker-compose" in subprocess.run(["where", "docker-compose"], capture_output=True).stdout.decode("utf-8"):
                        subprocess.run(["docker-compose", "build"]).check_returncode()
                        subprocess.run(["docker-compose", "up", "-d"]).check_returncode()
                    else:
                        subprocess.run(["docker", "compose", "build"]).check_returncode()
                        subprocess.run(["docker", "compose", "up", "-d"]).check_returncode()
                else:
                    # for bash / zsh / fish / etc.
                    if "docker-compose" in subprocess.run(["which", "docker-compose"], capture_output=True).stdout.decode("utf-8"):
                        subprocess.run(["docker-compose", "build"]).check_returncode()
                        subprocess.run(["docker-compose", "up", "-d"]).check_returncode()
                    else:
                        subprocess.run(["docker", "compose", "build"]).check_returncode()
                        subprocess.run(["docker", "compose", "up", "-d"]).check_returncode()
            except subprocess.CalledProcessError as e:
                logger.error(f"Error running compose: {e}")
    else:
        logger.error("Pull failed")
    logger.info("Sleeping for 10 seconds")
    time.sleep(10)