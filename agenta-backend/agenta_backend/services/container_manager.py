import traceback

import httpx
import shutil
import docker
import logging
import backoff
from pathlib import Path
from aiodocker import Docker
from httpx import ConnectError
from typing import List, Union
from fastapi import HTTPException

from asyncio.exceptions import CancelledError

import json

from agenta_backend.models.api.api_models import Image

client = docker.from_env()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def build_image_job(
        app_name: str,
        variant_name: str,
        user_id: str,
        tar_path: Path,
        image_name: str,
        temp_dir: Path,
) -> Image:
    """Business logic for building a docker image from a tar file

    TODO: This should be a background task

    Arguments:
        app_name --  The `app_name` parameter is a string that represents the name of the application
        variant_name --  The `variant_name` parameter is a string that represents the variant of the \
            application. It could be a specific version, configuration, or any other distinguishing \
                factor for the application
        user_id -- The unique id of the user
        tar_path --  The `tar_path` parameter is the path to the tar file that contains the source code \
            or files needed to build the Docker image
        image_name --  The `image_name` parameter is a string that represents the name of the Docker \
            image that will be built. It is used as the tag for the image
        temp_dir --  The `temp_dir` parameter is a `Path` object that represents the temporary directory
            where the contents of the tar file will be extracted

    Raises:
        HTTPException: _description_
        HTTPException: _description_

    Returns:
        an instance of the `Image` class.
    """

    # Extract the tar file
    shutil.unpack_archive(tar_path, temp_dir)

    try:
        logger.info("image_name:" + image_name)
        image, build_log = client.images.build(
            path=str(temp_dir),
            tag=image_name,
            buildargs={"ROOT_PATH": f"/{user_id}/{app_name}/{variant_name}"},
            rm=True,
        )
        for line in build_log:
            logger.info(line)
        return Image(docker_id=image.id, tags=image.tags[0])
    except docker.errors.BuildError as ex:
        log = "Error building Docker image:\n"
        log += str(ex) + "\n"
        logger.error(log)
        raise HTTPException(status_code=500, detail=str(ex))
    except Exception as ex:
        log = "Error building Docker image:\n"
        log += str(ex) + "\n"
        logger.error(log)
        traceback.print_tb(ex.__traceback__)
        raise HTTPException(status_code=500, detail=str(ex))


@backoff.on_exception(backoff.expo, (ConnectError, CancelledError), max_tries=5)
async def retrieve_templates_from_dockerhub(
        url: str,
        repo_user: str,
        repo_pass: str,
        rep_name: str
) -> Union[List[dict], dict]:
    """
    Business logic to retrieve templates from DockerHub.

    Args:
        url (str): The URL endpoint for retrieving templates. Should contain placeholders `{}`
            for the `repo_owner` and `repo_name` values to be inserted. For example:
            `http://{}:{}@127.0.0.1:5000/v2/tags/list`.
        repo_user (str): The user for login to docker registry.
        repo_pass (str): The pass for login to docker registry.

    Returns:
        tuple: A tuple containing two values.
        :param url:
        :param repo_user:
        :param repo_pass:
        :param repo_name:
        :param repo_owner:
    """

    async with httpx.AsyncClient() as client_http:
        try:
            async with httpx.AsyncClient() as client_http:
                url_to_load = f"{url}/{rep_name}/tags/list"
                print("url_to_load" + url_to_load)
                response = await client_http.get(url_to_load, auth=(repo_user, repo_pass), timeout=10)
                if response.status_code == 200:
                    response_data = response.json()
                    return response_data

                response_data = response.json()
                return response_data

        except Exception as e:
            # 抛出自定义异常，将异常信息和url_to_load传递给异常类
            raise Exception(str(e) + f"; url to load is : {url_to_load}.")


@backoff.on_exception(backoff.expo, (ConnectError, CancelledError), max_tries=5)
async def retrieve_manifests_from_dockerhub(
        url: str,
        repo_user: str,
        repo_pass: str,
        rep_name: str,
        tag: str
) -> dict:
    """
    Business logic to retrieve manifests from DockerRegistry.

    Args:
        url (str): The URL endpoint for retrieving templates. Should contain placeholders `{}`
            for the `repo_owner` and `repo_name` values to be inserted. For example:
            `http://{}:{}@127.0.0.1:5000/v2/tags/list`.
        :param url:
        :param repo_pass: The pass for login to docker registry.
        :param repo_user: The user for login to docker registry.
        :param tag:
        :param rep_name:

    Returns:
                     "size": temp_info["size"],
                    "architecture": temp_info["architecture"],
                    "digest": temp_info["digest"],
                    "status": temp_info["status"],
                    "last_pushed": temp_info["last_pushed"],
                    "media_type": rep_name["media_type"]

    """

    try:
        async with httpx.AsyncClient() as client_http:
            temp_info = {}
            url_to_load = f"{url}/{rep_name}/manifests/{tag}"
            print("url_manifest_to_load: " + url_to_load)
            headers = {'Accept': 'application/vnd.docker.distribution.manifest.v2+json'}
            response = await client_http.get(url_to_load, auth=(repo_user, repo_pass), timeout=10, headers=headers)
            if response.status_code == 200:
                response_data = response.json()
                temp_info["media_type"] = response_data["mediaType"]
                temp_info["size"] = response_data["config"]["size"]
                temp_info["digest"] = response_data["config"]["digest"]

            headers = {'Accept': 'application/vnd.docker.distribution.manifest.list.v2+json'}
            response = await client_http.get(url_to_load, auth=(repo_user, repo_pass), timeout=10, headers=headers)
            if response.status_code == 200:
                response_data = response.json()
                temp_info["architecture"] = response_data["architecture"]

            temp_info["last_pushed"] = "dummy"
            temp_info["status"] = "dummy"
            return temp_info

    except Exception as e:
        # 抛出自定义异常，将异常信息和url_to_load传递给异常类
        raise Exception(str(e) + f"; url to load is : {url_to_load}.")


async def get_templates_info(url: str, repo_user: str, repo_pass: str) -> dict:
    """
    Business logic to retrieve templates from DockerHub.

    Args:
        url (str): The URL endpoint for retrieving templates. Should contain placeholders `{}`
            for the `repo_owner` and `repo_name` values to be inserted. For example:
            `http://{}:{}@127.0.0.1:5000/v2/_catalog`.
        repo_user (str): The user for login to docker registry.
        repo_pass (str): The pass for login to docker registry.

    Returns:
        tuple: A tuple containing two values.
    """
    async with httpx.AsyncClient() as client_http:
        try:
            url_load = f"{url}/_catalog"
            response = await client_http.get(url_load, auth=(repo_user, repo_pass), timeout=10)
            if response.status_code == 200:
                response_data = response.json()
                return response_data

            response_data = response.json()
            print("response_data is:" + json.dumps(response_data))
            return response_data
        except Exception as e:
            raise Exception(f" error  load url: {url_load}  ; {str(e)}") from e


async def check_docker_arch() -> str:
    """Checks the architecture of the Docker system.

    Returns:
        The architecture mapping for the Docker system.
    """
    async with Docker() as docker:
        info = await docker.system.info()
        arch_mapping = {
            "x86_64": "amd",
            "amd64": "amd",
            "aarch64": "arm",
            "arm64": "arm",
            "armhf": "arm",
            "ppc64le": "ppc",
            "s390x": "s390",
            # Add more mappings as needed
        }
        return arch_mapping.get(info["Architecture"], "unknown")


async def pull_image_from_docker_hub(repo_name: str, tag: str,
                                     repo_user: str, repo_pass: str,
                                     repo_loc: str) -> dict:
    """Bussiness logic to asynchronously pull an image from Docker Hub.

    Args:
        repo_name (str): The name of the repository on Docker Hub from which the image is to be pulled.
            Typically follows the format `username/repository_name`.
        tag (str): Specifies a specific version or tag of the image to pull from the Docker Hub repository.

    Returns:
        Image: An image object from Docker Hub.
        :param tag:
        :param repo_name:
        :param repo_loc:
        :param repo_pass:
        :param repo_user:
    """
    # 登录到 Docker Registry
    client.login(username=repo_user, password=repo_pass, registry=repo_loc)
    # 使用 Docker SDK 拉取镜像
    image = await client.images.pull(repo_name, tag=tag)

    return image


async def get_image_details_from_docker_hub(
        repo_owner: str, repo_name: str, image_name: str
) -> str:
    """Retrieves the image details (specifically the image ID) from Docker Hub.

    Args:
        repo_owner (str): The owner or organization of the repository from which image details are to be retrieved.
        repo_name (str): The name of the repository.
        image_name (str): The name of the Docker image for which details are to be retrieved.

    Returns:
        str: The "Id" of the image details obtained from Docker Hub.
    """
    async with Docker() as docker:
        image_details = await docker.images.inspect(
            f"{repo_owner}/{repo_name}:{image_name}"
        )
        return image_details["Id"]
