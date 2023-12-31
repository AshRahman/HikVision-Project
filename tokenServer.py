from flask import (
    Flask,
    request,
    send_from_directory,
    jsonify,
    render_template,
    Response,
)
import time
import json
import requests
import base64

app = Flask(__name__)

# Variable to store the received JSON data
received_data = None
personCode = None
personId = None
personName = None
picUrl = None
b64pic = None
person_data = {"data": {"personName": None, "personId":None}}
door_data=None
pID= ""

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
        door_data= data["params"]["events"][0]["srcName"]
        print("Personcode is:"+personCode)
        print("PersonID is:"+person_data["data"]["personId"])
        print("Door is: "+door_data)
        
         # -------------------------------------------------------------
         ## Below code call the API to find the person information by PersonID
        url = "https://127.0.0.1/artemis/api/resource/v1/person/personCode/personInfo"
        payload = json.dumps({f"personCode": personCode})
        headers = {
            "x-ca-key": "22802759",
            "x-ca-signature": "UPM5yn29vrMcWTZwTgkw0NhHfG3bnmppWAsjA6yxaAM=",
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
        # print("Person ID:", person_id)
        # print(type(person_id))
        # print("Person Code:", person_code)
        # print("Person Name:", person_name)
        # print("Pic URI:", pic_uri)
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
            "x-ca-key": "22802759",
            "x-ca-signature": "q8sPwci5RnOYhmkRcpVqgje4aDmfayZUBGZj/LWtsPI=",
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
    return render_template("index.html")


@app.route("/gate_2", methods=["GET"])
def gate2():
    return render_template("gate2.html")



def generate():
    global b64pic
    global pID
    print("personID"+pID)
    while True:
        # Send the received_data as an SSE event
        if person_data["data"]["personId"] != '-1':
            json_data = json.dumps(person_data)
            yield f"data: {json_data}\n\n"
            print(json_data)
            person_data["data"]["personName"] = "next"
            person_data["data"]["personId"] = " "
            time.sleep(1)
            
        else:
             person_data["data"]["personName"] = "Stranger"
             person_data["data"]["personId"] = ""
             json_data = json.dumps(person_data)
             print(json_data)
             yield f"data: {json_data}\n\n"
             person_data["data"]["personName"] = "next"
             person_data["data"]["personId"] = " "
             time.sleep(1)
             
             
        
        
        # yield f"output.jpg"
          # Add a delay to avoid overloading the server


def generate_empty():
    while True:
        person_data["data"]["personName"] = "next"
        person_data["data"]["personId"] = " "
        json_data = json.dumps(person_data)
        print(json_data)
        yield f"data: {json_data}\n\n"
        time.sleep(1)
        
        
@app.route("/get_data", methods=["GET"])
def get_data():
    #global door_data
    if door_data == "Door 01":
        return Response(
            generate(),
            content_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
            },
        )
    else:
        return Response(
            generate_empty(),
            content_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
            },
        )

       
@app.route("/get_data2", methods=["GET"])
def get_data2():
    #global door_data
    if door_data == "Door 2":
        return Response(
            generate(),
            content_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
            },
        )
    else:
        return Response(
            generate_empty(),
            content_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
            },
        )



if __name__ == "__main__":
    # Change host and port as needed
    app.run(host="192.168.200.56", port=8089)
    




