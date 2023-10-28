
import httpx

async def get_tags(url, repo_owner, repo_name):
    proxies = {
        "https": "http://192.168.153.1:3389",
        "http": "http://192.168.153.1:3389"
    }

    async with httpx.AsyncClient(proxies=proxies) as client:
        response = await client.get(
            f"{url.format(repo_owner, repo_name)}/tags", timeout=10
        )
        if response.status_code == 200:
            response_data = response.json()
            return response_data

        response_data = response.json()
        return response_data


