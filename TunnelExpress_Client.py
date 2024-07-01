import time
import requests
import base64
import socketio

sio = socketio.Client()
server_url = "https://tunnelexpress-backend.onrender.com"
# server_url = "http://localhost:3010"


def forward_request(data):
    url = f"http://localhost:{data['port']}{data['path']}"
    headers = data["headers"]
    body = base64.b64decode(data["body"]) if data["body"] else None
    try:
        response = requests.request(
            method=data["method"],
            url=url,
            headers=headers,
            params=data["query"],
            data=body,
        )
        response_data = {
            "status": response.status_code,
            "headers": dict(response.headers),
            "body": base64.b64encode(response.content).decode("utf-8"),
        }

        # Check and remove 'Content-Encoding' and 'Content-Length' headers if present
        forward_headers = response_data["headers"]
        if "Content-Encoding" in forward_headers:
            del forward_headers["Content-Encoding"]
        if "Content-Length" in forward_headers:
            del forward_headers["Content-Length"]

        final_response = {
            "status": response_data["status"],
            "headers": forward_headers,
            "body": response_data["body"],
            "requestId": data["requestId"],
        }
        return final_response
    except requests.RequestException as e:
        print(e)
        return {
            "status": 500,
            "headers": {},
            "body": str(e),
            "requestId": data["requestId"],
        }


@sio.event
def connect():
    print("connected to main server")


@sio.event
def disconnect():
    print("disconnected from main server")


@sio.event
def port_register_ack(data):
    if data["ack"]:
        for i in data["ports"]:
            print(f"{i} --> {server_url}/tunnel/{data['api_key']}_{i}")
    else:
        print("something went wrong")
        time.sleep(5)
        exit()


@sio.event
def request(data):
    response = forward_request(data)
    sio.emit("response", response)


def remove_duplicates(arr):
    return list(dict.fromkeys(arr))


def make_POST_request_to_main_server(url, data):
    response = requests.post(url=server_url + url, json=data)
    if response.status_code == 200:
        return response
    else:
        print("Invalid...")
        time.sleep(5)
        exit()


def main():
    try:
        api_key = input("enter client api key : ")
        response = make_POST_request_to_main_server("/verifyApi", {"api_key": api_key})
        data = response.json()
        print(f"client details\n{data['email']}\n{data['name']}")
        ports = input("Enter ports separated by spaces: ")
        string_list = ports.split()
        ports = [int(num) for num in string_list]
        ports = remove_duplicates(ports)
        print("ports you want to expose : ", ports)
        if len(ports) == 0:
            exit()
        sio.connect(server_url)
        sio.emit("register_ports", {"api_key": api_key, "ports": ports})
        sio.wait()
    except:
        print("somthing went wrong")
        time.sleep(5)
        exit()


main()
