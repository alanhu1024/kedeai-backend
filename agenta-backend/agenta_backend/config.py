from pydantic import BaseSettings

import os
import toml
from typing import Optional

# Load the settings from the .toml file
toml_config = toml.load("./config.toml")

# Set the environment variables from the TOML configurations
os.environ["DOCKER_REGISTRY_URL"] = toml_config["docker_registry_url"]
os.environ["REGISTRY"] = toml_config["registry"]
os.environ["DATABASE_URL"] = toml_config["database_url"]
os.environ["DOCKER_HUB_URL"] = toml_config["docker_hub_url"]
os.environ["DOCKER_HUB_REPO_OWNER"] = toml_config["docker_hub_repo_owner"]
os.environ["DOCKER_HUB_REPO_NAME"] = toml_config["docker_hub_repo_name"]
os.environ["REDIS_URL"] = toml_config["redis_url"]
os.environ["DOCKER_REGISTRY_USER"] = toml_config["docker_registry_user"]
os.environ["DOCKER_REGISTRY_PASS"] = toml_config["docker_registry_pass"]
os.environ["DOCKER_REGISTRY_LOC"] = toml_config["docker_registry_loc"]


class Settings(BaseSettings):
    docker_registry_url: str
    registry: str
    redis_url: str
    database_url: str
    docker_hub_url: str
    docker_hub_repo_owner: str
    docker_hub_repo_name: str
    docker_registry_user: str
    docker_registry_pass: str
    docker_registry_loc: str


settings = Settings()
