import requests
print('# ###########################')


host= '127.0.0.1'
port = 5106
if True:
    d = {
        "request_type": "close_position",
        "symbol": "AAPL",
        "quantity": 10,
        "web_request_id": "test_request_001"
    }

    url = f"http://{host}:{port}/api/send-request"
    resp = requests.post(
        url
       ,
        json=d
    )

    print(f"url:{url}")
    print(f"Status:{resp.status_code}")
    print(f"rest:{resp}")
    print(f"Response:{resp.json()}")

    print('# ###########################')
    print('# ###########################')

if True:
    url = f"http://{host}:{port}/api/get-all-requests"

    resp = requests.get(url)

    print("Status:", resp.status_code)
    print("Body:", resp.json())


    print('# ###########################')
    print('# ###########################')



if True:

    url = f"http://{host}:{port}/api/health"
    print(f"Checking health at {url}")
    resp = requests.get(url)

    print("Status:", resp.status_code)
    print("Body:", resp.json())


    print('# ###########################')
    print('# ###########################')
