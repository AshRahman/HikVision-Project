from flask import Flask, render_template, jsonify,request
from flask_socketio import SocketIO, emit
import time
import json
import requests
import base64

app = Flask(__name__)
socketio = SocketIO(app, async_mode='eventlet')

# Variable to store the received JSON data
received_data = None
personCode = None
personId = None
personName = None
picUrl = None
b64pic = None
person_data = {"data": {"personName": None, "personId": None}}
door_data = None
pID = ""

@app.route("/event", methods=["POST"])
def handle_event():
    global received_data
    global door_data
    try:
        data = request.get_json()
        # received_data = data
        # Here you can process the received event data
        print("Received event:", data)
        personCode = data["params"]["events"][0]["data"][
            "personCode"
        ]  # Person Code required for the PersonInfo API
        person_data["data"]["personId"] = data["params"]["events"][0]["data"][
            "personId"
        ]
        door_data = data["params"]["events"][0]["srcName"]
        print("Personcode is:" + personCode)
        print("PersonID is:" + person_data["data"]["personId"])
        print("Door is: " + door_data)

        # ... (rest of your code for handling the event)
    # -------------------------------------------------------------
         ## Below code call the API to find the person information by PersonID
        url = "https://127.0.0.1/artemis/api/resource/v1/person/personCode/personInfo"
        payload = json.dumps({f"personCode": personCode})
        headers = {
            "x-ca-key": "20437019",
            "x-ca-signature": "+TA2G9MOazY2FbjTQat9LHsDl3Ma9BUV6Q/Gl+RGknc=",
            "x-ca-signature-headers": "x-ca-key",
            "Content-Type": "application/json",
        }
        response = requests.request(
            "POST", url, headers=headers, data=payload, verify=False
        )
        received_data = response.text
        print("Received Data:"+received_data)
        data_final = json.loads(received_data)
        person_id = data_final["data"]["personId"]
        person_code = data_final["data"]["personCode"]
        person_name = data_final["data"]["personName"]
        pic_uri = data_final["data"]["personPhoto"]["picUri"]
        # Print the extracted values
        print("Person ID:", person_id)
        print(type(person_id))
        print("Person Code:", person_code)
        print("Person Name:", person_name)
        print("Pic URI:", pic_uri)
        # ------------------------------------------------
        ## Picture Fetch API
        pic_url = "https://127.0.0.1/artemis/api/resource/v1/person/picture_data"
        pic_payload = json.dumps(
            {
                "personId": person_id,
                "picUri": pic_uri,
            }
        )
        pic_headers = {
            "x-ca-key": "20437019",
            "x-ca-signature": "LOSeJnym1JQ4F8SiaOne/EzExD/FpCL/7O1p7ClsjU0=",
            "x-ca-signature-headers": "x-ca-key",
            "Content-Type": "application/json",
        }
        pic_response = requests.request(
            "POST", pic_url, headers=pic_headers, data=pic_payload, verify=False
        )
        print(response.text)
        print(type(pic_response))
        b64pic = pic_response.text  # .split("data:image/jpeg;base64,", 1)[1]
        # ----------------------------------------------------------
        # ---------------------------------------------------------
        # Extract the Base64-encoded image data from the string
        data_idx = pic_response.text.find(",") + 1
        image_data = pic_response.text[data_idx:]
        # Decode the Base64 string to binary data
        binary_data = base64.b64decode(image_data)
        # Save the binary data as a JPEG image
        with open(f"static/images/{person_name}.jpg", "wb") as f:
            f.write(binary_data)
        print(f"Image saved as '{person_name}.jpg'")
        
        person_data["data"]["personName"] = person_name
        person_data["data"]["personId"] = person_id
        print(person_data["data"]["personName"])
        print(type(person_data))
            # ---------------------------------------------------------------
        
        return jsonify({"message": "Event received successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/", methods=["GET"])
def index():
    return render_template("socket.html")

@app.route("/gate_2", methods=["GET"])
def gate2():
    return render_template("gate2.html")

@socketio.on('connect')
def handle_connect():
    global door_data
    if door_data == "Door 01":
        emit('initial_data', json.dumps(person_data), namespace='/get_data')
    else:
        emit('initial_data_empty', json.dumps(person_data), namespace='/get_data')
@socketio.on('update_data', namespace='/get_data')
def update_data():
    while True:
        global door_data
        if door_data == "Door 01":
            if person_data["data"]["personId"] != '-1':
                emit('update_data', json.dumps(person_data))
                person_data["data"]["personName"] = "next"
                person_data["data"]["personId"] = " "
                time.sleep(1)
            else:
                person_data["data"]["personName"] = "Stranger"
                person_data["data"]["personId"] = ""
                emit('update_data', json.dumps(person_data))
                person_data["data"]["personName"] = "next"
                person_data["data"]["personId"] = " "
                time.sleep(1)
        else:
            emit('update_data_empty', json.dumps(person_data))
            time.sleep(1)

if __name__ == "__main__":
    socketio.start_background_task(target=update_data)
    socketio.run(app, host="192.168.249.254", port=8089)
