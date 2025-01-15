from tkinter import Image
import torch
import pickle
import cv2
import numpy as np
import mediapipe as mp
from typing import Optional, List, Tuple
from sklearn.preprocessing import LabelEncoder
from torch import nn
import torch.nn.functional as F

import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="google.protobuf.symbol_database")

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=1, min_detection_confidence=0.5)


class ResidualBlock(nn.Module):
    def __init__(self, in_features, out_features):
        super(ResidualBlock, self).__init__()

        self.fc1 = nn.Linear(in_features, out_features)
        self.fc2 = nn.Linear(out_features, out_features)

        self.skip_connection = nn.Linear(in_features, out_features) if in_features != out_features else None

    def forward(self, x):
        residual = x

        out = F.relu(self.fc1(x))
        out = self.fc2(out)

        if self.skip_connection is not None:
            residual = self.skip_connection(x)

        out += residual
        out = F.relu(out)
        return out


class ResidualNetwork(nn.Module):
    def __init__(self, input_size, hidden_layer_sizes, output_size):
        super(ResidualNetwork, self).__init__()

        self.fc_in = nn.Linear(input_size, hidden_layer_sizes[0])

        self.residual_blocks = nn.ModuleList()
        for i in range(len(hidden_layer_sizes) - 1):
            self.residual_blocks.append(ResidualBlock(hidden_layer_sizes[i], hidden_layer_sizes[i + 1]))

        self.fc_out = nn.Linear(hidden_layer_sizes[-1], output_size)

    def forward(self, x):
        x = F.relu(self.fc_in(x))

        for block in self.residual_blocks:
            x = block(x)

        x = self.fc_out(x)
        return x


def normalize_landmarks(landmarks: List[List[int]]) -> List[Tuple[float, float]]:
    """Normalize hand landmarks to make coordinates relative to the minimum x and y values."""
    x_coords = [lm[0] for lm in landmarks]
    y_coords = [lm[1] for lm in landmarks]

    min_x = np.min(x_coords)
    min_y = np.min(y_coords)

    normalized_landmarks = [(int(x - min_x), int(y - min_y)) for x, y in landmarks]
    return normalized_landmarks


def extract_and_normalize_landmarks(image: np.ndarray) -> Optional[Tuple[List[Tuple[float, float]], np.ndarray]]:
    """Extract and normalize hand landmarks from an image using MediaPipe Hands."""
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    result = hands.process(image_rgb)

    if result.multi_hand_landmarks:
        hand_landmarks = result.multi_hand_landmarks[0]
        landmarks: list[list[int]] = []
        for landmark in hand_landmarks.landmark:
            landmarks.append(
                [int(landmark.x * 360), int(landmark.y * 240)]
            )
        normalized_landmarks = normalize_landmarks(landmarks)
        for hand_landmarks in result.multi_hand_landmarks:
            mp.solutions.drawing_utils.draw_landmarks(image, hand_landmarks, mp.solutions.hands.HAND_CONNECTIONS)
        return normalized_landmarks, image
    return None, image


def process_image_for_model(image: np.ndarray) -> Optional[Tuple[np.ndarray, np.ndarray]]:
    """Resize the image, extract landmarks, and prepare data for the model."""
    image_resized = cv2.resize(image, (360, 240))
    landmarks, image = extract_and_normalize_landmarks(image_resized)

    if landmarks:
        flattened_landmarks = np.array([coord for lm in landmarks for coord in lm])
        return flattened_landmarks, image
    return None, image

def classify_pillow_image(pil_image: Image, model: ResidualNetwork , label_encoder : LabelEncoder) -> Optional[str]:
    """
    Classify a Pillow image using the ResidualNetwork model.

    Args:
        pil_image (Image.Image): The input Pillow image.
        model (ResidualNetwork): The trained PyTorch model for classification.

    Returns:
        Optional[int]: The predicted class label if landmarks are detected, otherwise None.
    """
    # Convert Pillow image to a NumPy array and then to OpenCV format
    image_np = np.array(pil_image)
    if len(image_np.shape) == 2:  # Handle grayscale images
        image_np = cv2.cvtColor(image_np, cv2.COLOR_GRAY2BGR)
    elif image_np.shape[2] == 4:  # Handle images with alpha channel
        image_np = cv2.cvtColor(image_np, cv2.COLOR_RGBA2BGR)

    # Process the image for the model
    processed_data = process_image_for_model(image_np)
    if processed_data is None:
        return None

    flattened_landmarks, _ = processed_data

    # Prepare the input tensor
    input_tensor = torch.tensor(flattened_landmarks, dtype=torch.float32).unsqueeze(0)

    # Perform classification
    model.eval()
    with torch.no_grad():
        output = model(input_tensor)
        predicted_label = torch.argmax(output, dim=1).item()
        
        class_name = label_encoder.inverse_transform([predicted_label])[0]

    return class_name
    

if __name__ == '__main__':
    model = ResidualNetwork(input_size=42, hidden_layer_sizes=(64, 128, 256), output_size=10)
    model.load_state_dict(torch.load('Models/hand_sign_resnet_model.pth', weights_only=True))

    with open('Label_Encoder/label_encoder.pkl', 'rb') as file:
        label_encoder = pickle.load(file)

