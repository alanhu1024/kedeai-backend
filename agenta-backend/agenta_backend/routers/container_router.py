import os
import traceback
import uuid
import asyncio
import logging
from pathlib import Path
from typing import List, Union

from fastapi.responses import JSONResponse
from fastapi import UploadFile, APIRouter, Depends, HTTPException

from agenta_backend.config import settings
from aiodocker.exceptions import DockerError
from concurrent.futures import ThreadPoolExecutor

from agenta_backend.models.db_models import TemplateDB
from agenta_backend.services import docker_utils
from agenta_backend.services.docker_utils import restart_container
from agenta_backend.models.api.api_models import (
    Image,
    RestartAppContainer,
    Template,
    URI,
)
from agenta_backend.services.db_manager import get_templates, get_user_object, add_template, find_template
from agenta_backend.services.container_manager import (
    build_image_job,
    get_image_details_from_docker_hub,
    pull_image_from_docker_hub,
)

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
from agenta_backend.services.auth_helper import (
    SessionContainer,
    verify_session, authenticate_token,
)

from agenta_backend.services.selectors import get_user_and_org_id

router = APIRouter()


@router.post("/build_image/")
async def build_image(
        app_name: str,
        variant_name: str,
        tar_file: UploadFile,
        stoken_session: SessionContainer = Depends(verify_session()),
) -> Image:
    """Takes a tar file and builds a docker image from it

    Arguments:
        app_name -- The `app_name` parameter is a string that represents the name of \
            the application for which the docker image is being built
        variant_name -- The `variant_name` parameter is a string that represents the \
            name or type of the variant for which the docker image is being built.
        tar_file -- The `tar_file` parameter is of type `UploadFile`. It represents the \
            uploaded tar file that will be used to build the Docker image

    Returns:
        an object of type `Image`.
    """
    try:
        # Get user and org id
        kwargs: dict = await get_user_and_org_id(stoken_session)

        # Get user object
        user = await get_user_object(kwargs["uid"])

        # Get event loop
        loop = asyncio.get_event_loop()

        # Create a ThreadPoolExecutor for running threads
        thread_pool = ThreadPoolExecutor(max_workers=4)

        # Create a unique temporary directory for each upload
        temp_dir = Path(f"/tmp/{uuid.uuid4()}")
        temp_dir.mkdir(parents=True, exist_ok=True)

        # Save uploaded file to the temporary directory
        tar_path = temp_dir / tar_file.filename
        with tar_path.open("wb") as buffer:
            buffer.write(await tar_file.read())
        logger.info(f"app_name | variant_name == {app_name.lower()} |   {variant_name.lower()}")
        image_name = f"agentaai/{app_name.lower()}_{variant_name.lower()}:latest"
        logger.info(f"image_name == {image_name}")

        # Use the thread pool to run the build_image_job function in a separate thread
        future = loop.run_in_executor(
            thread_pool,
            build_image_job,
            *(
                app_name,
                variant_name,
                str(user.id),
                tar_path,
                image_name,
                temp_dir,
            ),
        )

        # Return immediately while the image build is in progress
        image_result = await asyncio.wrap_future(future)
        return image_result
    except Exception as ex:
        traceback.print_tb(ex.__traceback__)
        return JSONResponse({"message": str(ex)}, status_code=500)


@router.post("/restart_container/")
async def restart_docker_container(
        payload: RestartAppContainer,
        stoken_session: SessionContainer = Depends(verify_session()),
) -> dict:
    """Restart docker container.

    Args:
        payload (RestartAppContainer) -- the required data (app_name and variant_name)
    """

    # Get user and org id
    kwargs: dict = await get_user_and_org_id(stoken_session)

    # Get user object
    user = await get_user_object(kwargs["uid"])

    try:
        container_id = f"{payload.app_name}-{payload.variant_name}-{str(user.id)}"
        restart_container(container_id)
        return {"message": "Please wait a moment. The container is now restarting."}
    except Exception as ex:
        return JSONResponse({"message": str(ex)}, status_code=500)


@router.get("/templates/")
async def container_templates(
        stoken_session: SessionContainer = Depends(verify_session()),
) -> Union[List[Template], str]:
    """Returns a list of container templates.

    Returns:
        a list of `Template` objects.
    """
    templates = await get_templates()
    return templates


@router.get("/images/")
async def container_templates(
        stoken_session: SessionContainer = Depends(verify_session()),
) -> List[Image]:
    """Returns a list of container templates.

    Returns:
        a list of `Template` objects.
    """
    images = docker_utils.list_images()
    return images


@router.put("/add_template/", dependencies=[Depends(authenticate_token)], )
async def add_single_template(
        template: Template,
):
    await add_template(
        **{
            "template_id": str(template.id),
            "name": template.image.name,
            "size": template.image.size,
            "architecture": template.image.architecture,
            "title": template.image.title,
            "description": template.image.description,
            "digest": template.image.digest,
            "status": template.image.status,
            "last_pushed": template.image.last_pushed,
            "repo_name": template.image.repo_name,
            "media_type": template.image.media_type,
        }
    )


@router.get("/templates/{image_name}/images/")
async def pull_image(
        image_name: str,
        stoken_session: SessionContainer = Depends(verify_session()),
) -> dict:
    """Pulls an image from Docker Hub using the provided configuration

    Arguments:
        image_name -- The name of the image to be pulled

    Returns:
        -- a JSON response with the image tag name and image ID
        -- a JSON response with the pull_image exception error
    """
    logger.info(f"image_name == {image_name}")

    existing_template = await find_template(
        image_name
    )
    logger.info(f"existing_template == {existing_template}")
    if existing_template is not None:
        repo_name = existing_template.repo_name
        image = docker_utils.get_image(repo_name)
        if image is not None:
            return JSONResponse({"image_tag": image.tags, "image_id": image.docker_id}, 200)

    # Get docker hub config
    repo_owner = settings.docker_hub_repo_owner
    repo_name = settings.docker_hub_repo_name
    repo_user = settings.docker_registry_user
    repo_pass = settings.docker_registry_pass
    repo_loc = settings.docker_registry_loc

    # Pull image from docker hub with provided config
    try:
        image_res = await pull_image_from_docker_hub(
            f"{repo_owner}/{repo_name}", image_name,
            repo_user, repo_pass, repo_loc
        )
    except DockerError as ext:
        return JSONResponse(
            {"message": "Image with tag does not exist", "meta": str(ext)}, 404
        )

    # Get data from image response
    image_tag_name = image_res[0]["id"]
    image_id = await get_image_details_from_docker_hub(
        repo_owner, repo_name, image_tag_name
    )
    return JSONResponse({"image_tag": image_tag_name, "image_id": image_id}, 200)


@router.get("/container_url/")
async def construct_app_container_url(
        app_name: str,
        variant_name: str,
        stoken_session: SessionContainer = Depends(verify_session()),
) -> URI:
    """Construct and return the app container url path.

    Arguments:
        app_name -- The name of app to construct the container url path
        variant_name -- The  variant name of the app to construct the container url path
        stoken_session (SessionContainer) -- the user session.

    Returns:
        URI -- the url path of the container
    """

    # Get user and org id
    kwargs: dict = await get_user_and_org_id(stoken_session)

    # Get user object
    user = await get_user_object(kwargs["uid"])

    # Set user backend url path and container name
    user_backend_url_path = f"{str(user.id)}/{app_name}/{variant_name}"
    return URI(uri=f"{user_backend_url_path}")
