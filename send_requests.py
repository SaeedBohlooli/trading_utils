import requests
print('# ###########################')


host= '127.0.0.1'
port = 5102
if True:
    d = {
        "request_type": "buy_order",
        "base_strike": "6850",
        "expiry": 20251211,
        "bid_price" :-10,
        "web_request_id": "test_request_003",
        "memo": "Test buy order from send_requests.py",
        'status': 'PY_SENT'
    }

    # d = {
    #     "order_set_id": "SET-20251210-140109--206",  # TODO u need to change it every time
    #     "base_strike": 6850,
    #     "expiry": 20251211,
    #     "bid_price" : -21.50,
    #     "web_request_id": "100",
    #     "request_type": "close_order",
    #     "memo": "A request from Web to close order ",
    # 'status': 'PY_SENT'
    # }

    # d = {
    #     "request_type": "close_position",
    #     "symbol": "AAPL",
    #     "quantity": 10,
    #     "web_request_id": "test_request_001"
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
