import requests
print('# ###########################')


host= '127.0.0.1'
port = 5102
if True:
    # d = {
    #     "request_type": "buy_order",
    #     "base_strike": "6870",
    #     "expiry": 2025112,
    #     "bid_price" :-8,
    #     "web_request_id": "test_request_003",
    #     "memo": "Test buy order from send_requests.py",
    #     'status': 'PY_SENT'
    # }

    d = {
      "request_type": "BUY_ORDER",
      "base_strike": 6900,
      "user_price": -.95,
      "expiry": "20251212",
      "web_request_id": "saeed-1",
      "web_timestamp": "2025-12-11 16:44:18",
      "status": "WEB_SENT"
    }
    # d = {
    #     "order_set_id": "SET-20251211-105818--113",  # TODO u need to change it every time
    #     "base_strike": 6850,
    #     "expiry": 20251211,
    #     "user_price" : -21.50,
    #     "web_request_id": "100",
    #     "request_type": "CLOSE_ORDER_SET",
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
