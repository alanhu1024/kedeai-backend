import json
import os
from contextlib import asynccontextmanager

import uvicorn

from agenta_backend.config import settings
from agenta_backend.routers import (
    app_variant,
    container_router,
    environment_router,
    evaluation_router,
    testset_router,
)
from agenta_backend.services.cache_manager import (
    retrieve_templates_from_dockerhub_cached,
    retrieve_templates_info_from_dockerhub_cached,
)
from agenta_backend.services.container_manager import pull_image_from_docker_hub, retrieve_manifests_from_dockerhub
from agenta_backend.services.db_manager import add_template, remove_old_template_from_db
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://0.0.0.0:3000",
    "http://0.0.0.0:3001",
]


@asynccontextmanager
async def lifespan(application: FastAPI, cache=False):
    """

    Args:
        application: FastAPI application.
        cache: A boolean value that indicates whether to use the cached data or not.
    """
    # Get docker hub config
    repo_user = settings.docker_registry_user
    repo_pass = settings.docker_registry_pass
    repo_loc = settings.docker_registry_loc
    repo_url = settings.docker_hub_url

    templates_info_string = await retrieve_templates_info_from_dockerhub_cached(
        cache=cache
    )

    if isinstance(templates_info_string, str):
        templates_info = json.loads(templates_info_string)
        if not templates_info['errors'] is None:
            print(templates_info['errors'])
    else:
        templates_info = templates_info_string

    templates_in_hub = []
    for rep_name in templates_info["repositories"]:
        tags = await retrieve_templates_from_dockerhub_cached(cache=cache, rep_name=rep_name)
        for tag in tags['tags']:
            # Append the template id in the list of templates_in_hub
            # We do this to remove old templates from database
            rep_name = tags["name"]
            template_id = rep_name + "-" + tag
            templates_in_hub.append(template_id)
            temp_info = await retrieve_manifests_from_dockerhub(repo_url, repo_user, repo_pass, rep_name, tag)
            await add_template(
                **{
                    "template_id": template_id,
                    "name": rep_name,
                    "size": temp_info["size"],
                    "architecture": temp_info["architecture"],
                    "title": rep_name,
                    "description": rep_name,
                    "digest": temp_info["digest"],
                    "status": temp_info["status"],
                    "last_pushed": temp_info["last_pushed"],
                    "repo_name": rep_name,
                    "media_type": temp_info["media_type"],
                }
            )
            image_res = await pull_image_from_docker_hub(
                f"{rep_name}", tag["name"],
                repo_user, repo_pass, repo_loc
            )
            print(f"Template {tag['id']} added to the database.")
            print(f"Template Image {image_res[0]['id']} pulled from DockerHub.")

    # Remove old templates from database
    await remove_old_template_from_db(templates_in_hub)
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(app_variant.router, prefix="/app_variant")
app.include_router(evaluation_router.router, prefix="/evaluations")
app.include_router(testset_router.router, prefix="/testsets")
app.include_router(container_router.router, prefix="/containers")
app.include_router(environment_router.router, prefix="/environments")

allow_headers = ["Content-Type"]

if os.environ["FEATURE_FLAG"] in ["cloud", "ee", "demo"]:
    import agenta_backend.ee.main as ee

    app, allow_headers = ee.extend_main(app)
# this is the prefix in which we are reverse proxying the api
#
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=allow_headers,
)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8010, reload=True)
