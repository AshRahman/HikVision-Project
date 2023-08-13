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
person_data = {"data": {"personName": None, "personPhoto": {"picUri": None}}}


@app.route("/event", methods=["POST"])
def handle_event():
    global received_data
    try:
        data = request.get_json()
        # received_data = data
        # Here you can process the received event data
        print("Received event:", data)
        personCode = data["params"]["events"][0]["data"][
            "personCode"
        ]  # Person Code required for the PersonInfo API
        print("Personcode is:"+personCode)
        
         # -------------------------------------------------------------
         ## Below code call the API to find the person information by PersonID
        url = "https://127.0.0.1/artemis/api/resource/v1/person/personCode/personInfo"
        payload = json.dumps({f"personCode": personCode})
        headers = {
            "x-ca-key": "20942152",
            "x-ca-signature": "fBb++H9TnmkutgMtnQgNyNGR4q5RxVSbCb7lwW6Zzlg=",
            "x-ca-signature-headers": "x-ca-key",
            "Content-Type": "application/json",
        }
        response = requests.request(
            "POST", url, headers=headers, data=payload, verify=False
        )
        received_data = response.text
        print("Recieved Data:"+received_data)
        data_final = json.loads(received_data)
        person_id = data_final["data"]["personId"]
        person_code = data_final["data"]["personCode"]
        person_name = data_final["data"]["personName"]
        pic_uri = data_final["data"]["personPhoto"]["picUri"]
        # Print the extracted values
        print("Person ID:", person_id)
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
            "x-ca-key": "20942152",
            "x-ca-signature": "9AIUX/5aX4eqW3bpE++N2fvKW3t8Cvk8gEP5YcBxoek=",
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
        person_data["data"]["personPhoto"]["picUri"] = b64pic
        print(person_data["data"]["personName"])
        print(type(person_data))
            # ---------------------------------------------------------------
        
        return jsonify({"message": "Event received successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/images/<filename>")
def serve_image(filename):
    return send_from_directory(
        os.path.join(app.root_path, "static", "images"), filename
    )


def generate():
    global b64pic
    while True:
        # Send the received_data as an SSE event
        if person_data['data']['personName']:
            temp=person_data['data']['personName']
            yield f"data: {person_data['data']['personName']}\n\n"
        else:
             person_data["data"]["personName"] = "Stranger"
             yield f"data: {person_data['data']['personName']}\n\n"
        # yield f"output.jpg"
        time.sleep(2)  # Add a delay to avoid overloading the server


# def send_name():
#     global b64pic
#     while True:
#         # Send the received_data as an SSE event
#         yield f"{person_data['data']}\n"
#         # yield f"output.jpg"
#         time.sleep(2)  # Add a delay to avoid overloading the server


@app.route("/get_data", methods=["GET"])
def get_data():
    return Response(
        generate(),
        content_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
        },
    )


if __name__ == "__main__":
    # Change host and port as needed
    app.run(host="192.168.200.19", port=8089)
