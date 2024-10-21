import json
import base64
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

with open("/openai/api_key.json") as f:
    config = json.load(f)

api_key = config["key"]


# Function to encode image to base64
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


# Path to your image
image_path = "src/agent_testbed/connection_puzzle_image.png"

# Encode the image
base64_image = encode_image(image_path)

# Initialize the ChatOpenAI model
model = ChatOpenAI(
    model="gpt-4o",
    api_key=api_key,
    model_kwargs={"response_format": {"type": "json_object"}},
)

# Create a message with text and image
message = HumanMessage(
    content=[
        {"type": "text", "text": "extract words from the image and return as a json list"},
        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}},
    ]
)

# Get the response from the model
response = model.invoke([message])

# Print the response
print(response.content)

mr_format = json.loads(response.content)

print(mr_format)
