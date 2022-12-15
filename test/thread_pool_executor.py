import concurrent.futures
import urllib.request

URLS = ['https://www.baidu.com/',
        'https://www.youku.com/',
       ]

# Retrieve a single page and report the URL and contents
def load_url(url, timeout):
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=timeout) as conn:
        return conn.read()

# We can use a with statement to ensure threads are cleaned up promptly
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    # Start the load operations and mark each future with its URL
    future_to_url = {executor.submit(load_url, url, 60): url for url in URLS}
    r = concurrent.futures.wait(future_to_url)
    print(r)
    for res in r.done:
      print(len(res.result()))
    # for future in concurrent.futures.as_completed(future_to_url):
    #     url = future_to_url[future]
    #     try:
    #         data = future.result()
    #     except Exception as exc:
    #         print('%r generated an exception: %s' % (url, exc))
    #     else:
    #         print('%r page is %d bytes' % (url, len(data)))