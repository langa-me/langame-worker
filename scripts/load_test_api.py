from typing import List
import requests
import fire
import asyncio
import json
from random import randint, choices
import time
from time import sleep

# most common conversation topics
_topics = [
    "business",
    "work",
    "ice breaker",
    "travel",
    "politic",
    "food",
    "cooking",
    # less common / scientific
    "artificial intelligence",
    "robotics",
    "mathematics",
    "physics",
    "chemistry",
    "biology",
]


async def _load_test_api(
    api_key: str,
    is_prod: bool = False,
    max_requests: int = 10,
    seconds_between_requests: int = 5,
):
    """
    :param api_key:
    :param is_prod: If True, use production API.
    :param max_requests:
    :param seconds_between_requests:
    """
    url = f"https://{'' if is_prod else 'd'}api.langa.me/v1/conversation/starter"
    headers = {
        "Content-Type": "application/json",
        "X-Api-Key": api_key,
    }
    print("starting load test with settings:")
    # print api key with 3 chars then stars
    print(f"\tapi_key: {api_key[:3]}" + ("*" * (len(api_key) - 3)))
    print(f"\turl: {url}")
    print(f"\tmax_requests: {max_requests}")
    print(f"\tseconds_between_requests: {seconds_between_requests}")

    responses_per_code = {}
    average_response_time = 0

    for e in range(max_requests):
        data = {
            # random list of 2 topics
            "topics": choices(_topics, k=2),
            "limit": randint(1, 3),
            # 10% chance of being True
            "translated": bool(randint(0, 10) > 8),
        }
        print(f"requesting with data: {data}")
        # count time elapsed for request
        start = time.time()
        response = requests.post(
            url,
            headers=headers,
            data=json.dumps(data),
        )
        end = time.time()
        total = end - start
        average_response_time += total
        print(f"request took {total} seconds")
        responses_per_code[response.status_code] = (
            responses_per_code.get(response.status_code, 0) + 1
        )
        response_data = response.json()
        print(f"{e + 1}/{max_requests}: {response_data}")
        sleep(seconds_between_requests)
    print("finished load test")
    average_response_time /= max_requests
    print(f"responses per code: {responses_per_code}")
    print(f"average response time: {average_response_time}")


async def load_test_api(
    api_keys_file: str = ".keys",
    is_prod: bool = False,
    max_requests: int = 10,
    seconds_between_requests: int = 5,
):
    """
    :param api_keys_file:
    :param is_prod: If True, use production API.
    :param max_requests:
    :param seconds_between_requests:
    """
    assert isinstance(api_keys_file, str), "api_keys_file must be a string"
    with open(api_keys_file, "r") as f:
        api_keys = f.read().splitlines()

        print(f"found {len(api_keys)} API keys in {api_keys_file}")

        # for each api key, run _load_test_api in parallel

        await asyncio.gather(
            *[
                _load_test_api(api_key, is_prod, max_requests, seconds_between_requests)
                for api_key in api_keys
            ]
        )


if __name__ == "__main__":
    fire.Fire(load_test_api)
