import requests
print('# ###########################')


host= '127.0.0.1'
port = 5102

def get_buy_order_request():
    """
    Enter the maximum price you are willing to pay. The order fills when the model ask falls to your price or better.

    Example: If you enter –3.50, the order fills when the model ask reaches –3.50 or lower.
    :return:
    """
    d = {
      "request_type": "BUY_ORDER",
      "base_strike": 6760,
      "user_price": 1,  # less then 1 will be filled out at market price
      "expiry": "20251219",
      "web_request_id": "saeed-1",
      "web_timestamp": "2025-12-11 16:44:18",
      "status": "WEB_SENT"
    }
    return d

def get_sell_order_request():
    d = {
        "order_set_id": "SET-20251217-134642-29",  # TODO u need to change it every time
        "user_price" : -30,
        "web_request_id": "100",
        "request_type": "CLOSE_ORDER_SET",
        "memo": "A request from Web to close order ",
        'status': 'PY_SENT'
    }
    return d


d = get_buy_order_request()
# d = get_sell_order_request()

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



if False:

    url = f"http://{host}:{port}/api/health"
    print(f"Checking health at {url}")
    resp = requests.get(url)

    print("Status:", resp.status_code)
    print("Body:", resp.json())


    print('# ###########################')
    print('# ###########################')
