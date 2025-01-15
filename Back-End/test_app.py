import pytest
from server_main import app, socketio, process_frame
from flask_socketio import SocketIOTestClient
from unittest.mock import MagicMock, patch
import base64
from PIL import Image
import io

# Fixtures for Flask and SocketIO test client
@pytest.fixture
def client():
    global app
    """Creează un client pentru testarea aplicației Flask."""
    test_client = app.test_client()
    return test_client

@pytest.fixture
def socket_client():
    global app 
    """Creează un client SocketIO pentru testare."""
    return SocketIOTestClient(app, socketio)

# Test for process_frame function
@patch('resNetPrediction.classify_pillow_image', return_value='All_Fingers_Up')
def test_process_frame_with_image(mock_classify, socket_client):
    """Test pentru procesarea imaginilor, folosind o imagine existentă."""
    socket_client.emit('cameracon')
    # Încarcă o imagine din fișier
    image_path = 'photo_2024-10-19_14-51-50_rotated_-1.jpg'
    img = Image.open(image_path)

    # Salvează imaginea într-un buffer pentru a o codifica în base64
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    encoded_image = base64.b64encode(buf.getvalue()).decode('utf-8')

    # Trimite cererea către `process_frame`
    data = {
        'data': f'data:image/png;base64,{encoded_image}'
    }

    socket_client.emit('frame', data)

    # Verifică răspunsul
    received = socket_client.get_received()
    assert len(received) == 2
    assert received[1]['name'] == 'response'
    assert received[1]['args'][0]['message'] == 'All_Fingers_Up'
    
    socket_client.emit('cameradisc')

# Test for handle_message function
@patch('qdrant.receive_answear', return_value='Thumbs Up')
def test_handle_message(mock_receive, socket_client):
    """Test pentru procesarea mesajelor."""
    socket_client.connect()
    
    data = {'message': 'What is used for the backend?'}

    socket_client.emit('message', data)
    
    received = socket_client.get_received()
    assert len(received) == 1
    assert received[0]['name'] == 'response'
    assert 'Flask' in received[0]['args'][0]['message']

# Test for the cameracon event, which sets the active socket
def test_cameracon(socket_client):
    """Test pentru evenimentul cameracon."""
    socket_client.connect()
    socket_client.emit('cameracon')

    received = socket_client.get_received()
    assert len(received) == 1
    assert 'You are now the active socket' in received[0]['args'][0]['message']
    
    socket_client.emit('cameradisc')

# Test for queue handling (when a new client connects while another is active)
def test_queue_handling(socket_client):
    """Test pentru gestionarea cozii când un alt client se conectează."""
    # First client connects
    socket_client.connect()
    socket_client.emit('cameracon')

    # Second client connects
    socket_client2 = SocketIOTestClient(app, socketio)
    socket_client2.connect()
    socket_client2.emit('cameracon')

    # Check that the second client is in queue
    received = socket_client2.get_received()
    assert len(received) == 1
    assert 'You are in the queue, waiting for your turn' in received[0]['args'][0]['message']
    
    socket_client.emit('cameradisc')
    socket_client2.emit('cameradisc')

@patch('resNetPrediction.classify_pillow_image', return_value='test_label')
def test_process_frame_no_image_data(mock_classify, socket_client):
    """Test for missing image data."""
    # First, simulate an active connection (to avoid "not the active socket" message)
    socket_client.emit('cameracon')  # Connect the socket to simulate active socket

    # Now simulate no image data (empty string or None)
    data = {
        'data': ''  # No image data
    }

    # Emit the frame event with no image data
    socket_client.emit('frame', data)

    # Check the response
    received = socket_client.get_received()
    assert len(received) == 2
    assert received[1]['name'] == 'response'
    assert 'Failed to process image' in received[1]['args'][0]['message']
    
    socket_client.emit('cameradisc')

@patch('resNetPrediction.classify_pillow_image', return_value='test_label')
def test_process_frame_invalid_image(mock_classify, socket_client):
    """Test for processing invalid images."""
    # First, simulate an active connection (this is necessary to avoid "not the active socket" message)
    socket_client.emit('cameracon')  # Connect the socket to simulate active socket

    # Now simulate invalid image data (either corrupted or empty base64)
    invalid_image_data = ''  # This is empty or invalid base64 image data

    data = {
        'data': f'data:image/png;base64,{invalid_image_data}'
    }

    # Emit the frame event with invalid image data
    socket_client.emit('frame', data)

    # Check the response
    received = socket_client.get_received()
    assert len(received) == 2
    assert received[1]['name'] == 'response'
    assert 'Failed to process image' in received[1]['args'][0]['message']
    
    socket_client.emit('cameradisc')
