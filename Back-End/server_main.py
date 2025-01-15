from flask import Flask, request
from flask_socketio import SocketIO
import base64
import io
from PIL import Image
import torch
from resNetPrediction import ResidualNetwork,classify_pillow_image
import pickle
from qdrant import receive_answear
from threading import Lock
from queue import Queue

model = ResidualNetwork(input_size=42, hidden_layer_sizes=(64, 128, 256), output_size=10)
model.load_state_dict(torch.load('Models/hand_sign_resnet_model.pth', weights_only=True))

with open('Label_Encoder/label_encoder.pkl', 'rb') as file:
    label_encoder = pickle.load(file)


app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")

last_predicted = ''

@socketio.on('connect')
def on_connect():
    print("Client connected.")

@socketio.on('disconnect')
def on_disconnect():
    print("Client disconnected.")

socket_queue = Queue()
active_socket = None
active_socket_lock = Lock()

last_predicted = None

@socketio.on('cameracon')
def handle_connect():
    global active_socket

    socket_id = request.sid

    with active_socket_lock:
        if active_socket is None:
            active_socket = socket_id
            socketio.emit('response', {'message': 'You are now the active socket'}, room=socket_id)
        else:
            if socket_id not in list(socket_queue.queue):
                socket_queue.put(socket_id)
            socketio.emit('response', {'message': 'You are in the queue, waiting for your turn'}, room=socket_id)


@socketio.on('frame')
def handle_frame(data):
    global active_socket

    socket_id = request.sid

    try:
        with active_socket_lock:
            if active_socket == socket_id:
                process_frame(socket_id, data)
            else:
                socketio.emit('response', {'message': 'Please wait, you are not the active socket'}, room=socket_id)

    except Exception as e:
        print(f"Error: {e}")
        socketio.emit('response', {'message': f"Failed to process frame: {e}"}, room=socket_id)


@socketio.on('cameradisc')
def handle_disconnect():
    global active_socket

    socket_id = request.sid

    with active_socket_lock:
        if active_socket == socket_id:
            active_socket = None
            if not socket_queue.empty():
                next_socket = socket_queue.get()
                active_socket = next_socket
                socketio.emit('response', {'message': 'You are now the active socket'}, room=active_socket)


def process_frame(socket_id, data):
    try:
        global last_predicted

        image_data = data.get('data')

        if not image_data:
            raise ValueError("No image data received.")

        if image_data.startswith('data:image/png;base64,'):
            encoded = image_data.split('base64,', 1)[1]
        else:
            raise ValueError("Invalid image format, expected base64 PNG image.")

        decoded = base64.b64decode(encoded)

        image = Image.open(io.BytesIO(decoded))

        predicted_label = classify_pillow_image(image, model, label_encoder)

        if last_predicted != predicted_label:
            socketio.emit('response', {'message': f'{predicted_label}'}, room=socket_id)
            last_predicted = predicted_label
        else:
            socketio.emit('response', {'message': 'Already in list'}, room=socket_id)

    except Exception as e:
        print(f"Failed to process image: {e}")

        socketio.emit('response', {'message': f"Failed to process image: {e}"}, room=socket_id)
        
@socketio.on('message')
def handle_message(data):
    try:
        message = data.get('message')
    
        response = receive_answear(message)
        
        print(response) 
        socketio.emit('response' , {'message' : f"{response}"})
    except Exception as e:
        print(f"Failed to proces message : {e}")
        
        socketio.emit('response' , {'message' :f"Failed to receive a response: {e}" })

if __name__ == "__main__":
    socketio.run(app, host="127.0.0.1", port=5000)