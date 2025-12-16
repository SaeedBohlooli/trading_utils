import requests
print('# ###########################')


host= '127.0.0.1'
port = 5102
if True:


    d = {
      "request_type": "BUY_ORDER",
      "base_strike": 6810,
      "user_price": 1,
      "expiry": "20251217",
      "web_request_id": "saeed-1",
      "web_timestamp": "2025-12-11 16:44:18",
      "status": "WEB_SENT"
    }
    # d = {
    #     "order_set_id": "SET-20251216-154252-85",  # TODO u need to change it every time
    #     "base_strike": 6810,
    #     "expiry": 20251216,
    #     "user_price" : -20,
    #     "web_request_id": "100",
    #     "request_type": "CLOSE_ORDER_SET",
    #     "memo": "A request from Web to close order ",
    #     'status': 'PY_SENT'
    # }



    url = f"http://{host}:{port}/api/send-request"
    resp = requests.post(
        url, json=d
    )
    print(d)
    print(f"url:{url}")
    print(f"Status:{resp.status_code}")
    print(f"rest:{resp}")
    print(f"Response:{resp.json()}")

    print('# ###########################')
    print('# ###########################')

if False:
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
