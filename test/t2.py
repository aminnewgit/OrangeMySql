import concurrent.futures
import time
import urllib.request

kid_list = [
  ['jack', 2],
  ['tom',1],
]


def sleep(name, sleep_time):
    time.sleep(sleep_time)
    return name, sleep_time

# We can use a with statement to ensure threads are cleaned up promptly
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    # Start the load operations and mark each future with its URL
    future_list = [executor.submit(sleep, kid[0], kid[1]) for kid in kid_list]

    for future in concurrent.futures.as_completed(future_list):
        try:
            data = future.result()
        except Exception as exc:
            print(f"exception {exc}")
        else:
            print(f"{data[0]} sleep {data[1]}")