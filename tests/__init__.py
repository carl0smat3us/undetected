import logging
import os
from pathlib import Path

logging.basicConfig(level=10)
logger = logging.getLogger("test")


def find_and_prepare_chrome(tmp_dir: Path = Path("/tmp")):
    for k, v in os.environ.items():
        logger.info("%s = %s", k, v)
    logger.info("==== END ENV ====")

    tmp_dir = tmp_dir.resolve()

    for item in tmp_dir.rglob("**"):
        logger.info("found %s", item)

        if item.is_dir() and "chrome-" in item.name:
            logger.info("adding %s to PATH", item)
            logger.info("current PATH: %s", os.environ.get("PATH"))

            path_list = os.environ["PATH"].split(os.pathsep)
            path_list.insert(0, str(item))
            os.environ["PATH"] = os.pathsep.join(path_list)

            logger.info("new PATH: %s", os.environ["PATH"])

            chrome_path = item / "chrome"
            if chrome_path.exists():
                return str(chrome_path)

    return None
