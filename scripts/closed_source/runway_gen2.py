#!/usr/bin/env python
"""
Script to generate videos from images using RunwayML Gen-2 API
"""

import argparse
import os
import time
import requests
import json
import base64
from PIL import Image
import io

def parse_args():
    parser = argparse.ArgumentParser(description="Generate video from image using RunwayML Gen-2 API")
    parser.add_argument("--image", type=str, required=True, help="Path to input image")
    parser.add_argument("--prompt", type=str, required=True, help="Text prompt to guide the video generation")
    parser.add_argument("--output", type=str, required=True, help="Path to save the output video")
    parser.add_argument("--api_key", type=str, help="RunwayML API key (or set RUNWAY_API_KEY env var)")
    parser.add_argument("--num_frames", type=int, default=24, help="Number of frames to generate")
    parser.add_argument("--fps", type=int, default=8, help="Frames per second for the output video")
    return parser.parse_args()

def encode_image(image_path):
    """Encode image to base64 string"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def main():
    args = parse_args()
    
    # Check if input image exists
    if not os.path.isfile(args.image):
        print(f"Error: Input image '{args.image}' does not exist")
        return
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    
    # Get API key from arguments or environment
    api_key = args.api_key or os.environ.get("RUNWAY_API_KEY")
    if not api_key:
        print("Error: RunwayML API key not provided. Use --api_key or set RUNWAY_API_KEY environment variable.")
        return
    
    # Print configuration
    print(f"Input image: {args.image}")
    print(f"Prompt: {args.prompt}")
    print(f"Output video: {args.output}")
    
    # Encode the image
    print("Encoding input image...")
    base64_image = encode_image(args.image)
    
    # Prepare API request
    url = "https://api.runwayml.com/v1/inference/gen2"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "prompt": args.prompt,
        "image": base64_image,
        "mode": "image-to-video",
        "num_frames": args.num_frames,
        "fps": args.fps
    }
    
    # Call API
    print("Sending request to RunwayML Gen-2 API...")
    start_time = time.time()
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code != 200:
        print(f"Error: API request failed with status code {response.status_code}")
        print(f"Response: {response.text}")
        return
    
    # Process the response
    response_data = response.json()
    generation_time = time.time() - start_time
    print(f"Video generation completed in {generation_time:.2f} seconds")
    
    # Save the video
    if "video" in response_data:
        print(f"Saving video to {args.output}...")
        video_data = base64.b64decode(response_data["video"])
        with open(args.output, "wb") as f:
            f.write(video_data)
        print("Done!")
    else:
        print("Error: No video in API response")
        print(f"Response: {json.dumps(response_data, indent=2)}")

if __name__ == "__main__":
    main() 