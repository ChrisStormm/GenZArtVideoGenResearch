#!/usr/bin/env python
"""
Script to generate videos from images using MiniMax Hailuo API
"""

import requests
import json
import base64
import argparse
import os
import datetime
import dotenv
import uuid
import re
import time

# Load environment variables from .env file
dotenv.load_dotenv()

def parse_args():
    parser = argparse.ArgumentParser(description="Generate video from image using MiniMax Hailuo API")
    parser.add_argument("--image", type=str, required=True, help="Path to input image")
    parser.add_argument("--prompt", type=str, required=True, help="Text prompt to guide the video generation")
    parser.add_argument("--output", type=str, help="Path to save the output video (optional, default: auto-generated)")
    parser.add_argument("--api_key", type=str, help="MiniMax API key (or set MINIMAX_API_KEY env var)")
    parser.add_argument("--model", type=str, default="I2V-01-Director", help="MiniMax model name")
    parser.add_argument("--poll_interval", type=int, default=10, help="Polling interval in seconds (default: 10)")
    return parser.parse_args()

def generate_unique_filename(prompt, model, ext=".mp4"):
    """Generate a unique filename based on timestamp, prompt and model"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    # Create a short hash of the prompt
    prompt_hash = str(uuid.uuid5(uuid.NAMESPACE_DNS, prompt))[:8]
    # Sanitize prompt for filename (take first 20 chars and replace problematic chars)
    safe_prompt = re.sub(r'[^a-zA-Z0-9]', '_', prompt[:20]).lower()
    # Sanitize model name for directory
    safe_model = re.sub(r'[^a-zA-Z0-9\-]', '_', model).lower()
    
    return f"minimax_{timestamp}_{safe_prompt}_{prompt_hash}_{safe_model}{ext}"

def format_time_elapsed(seconds):
    """Format seconds into a human-readable time string"""
    if seconds < 60:
        return f"{seconds:.2f} seconds"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.2f} minutes ({seconds:.2f} seconds)"
    else:
        hours = seconds / 3600
        minutes = (seconds % 3600) / 60
        return f"{hours:.2f} hours ({minutes:.2f} minutes)"

def query_video_generation(api_key, task_id):
    """Query the status of a video generation task"""
    url = f"https://api.minimaxi.chat/v1/query/video_generation?task_id={task_id}"
    headers = {
        'Authorization': f'Bearer {api_key}'
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Error querying task status: {response.status_code}")
        print(f"Response: {response.text}")
        return None, "Error"
    
    response_data = response.json()
    status = response_data.get('status', '')
    
    if status == 'Success':
        file_id = response_data.get('file_id', '')
        return file_id, "Success"
    else:
        return None, status

def fetch_video_result(api_key, file_id, output_path):
    """Fetch the generated video using the file_id"""
    print("Retrieving video download URL...")
    url = f"https://api.minimaxi.chat/v1/files/retrieve?file_id={file_id}"
    headers = {
        'Authorization': f'Bearer {api_key}'
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Error retrieving file: {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    response_data = response.json()
    download_url = response_data.get('file', {}).get('download_url', '')
    
    if not download_url:
        print("Error: No download URL found in response")
        print(f"Response: {json.dumps(response_data, indent=2)}")
        return False
    
    print(f"Video download URL: {download_url}")
    print("Downloading video...")
    
    download_start = time.time()
    video_response = requests.get(download_url)
    if video_response.status_code != 200:
        print(f"Error downloading video: {video_response.status_code}")
        return False
    
    with open(output_path, 'wb') as f:
        f.write(video_response.content)
    
    download_duration = time.time() - download_start
    print(f"Video downloaded in {format_time_elapsed(download_duration)}")
    return True

def main():
    args = parse_args()
    
    # Start timing
    start_time = time.time()
    
    # Get API key from arguments or environment
    api_key = args.api_key or os.environ.get("MINIMAX_API_KEY")
    if not api_key:
        print("Error: MiniMax API key not provided. Use --api_key or set MINIMAX_API_KEY environment variable.")
        return
    
    # Validate image path
    if not os.path.isfile(args.image):
        print(f"Error: Input image '{args.image}' does not exist")
        return

    # Encode the image
    print(f"Encoding image: {args.image}")
    encoding_start = time.time()
    with open(args.image, "rb") as image_file:
        data = base64.b64encode(image_file.read()).decode('utf-8')
    print(f"Image encoded in {time.time() - encoding_start:.2f} seconds")
    
    # Determine output path
    if args.output:
        # Use specified output path
        output_path = args.output
        # Make sure the directory exists
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    else:
        # Generate unique filename in a model-specific subfolder
        safe_model = re.sub(r'[^a-zA-Z0-9\-]', '_', args.model).lower()
        output_dir = os.path.join("outputs", "minMax", safe_model)
        os.makedirs(output_dir, exist_ok=True)
        
        filename = generate_unique_filename(args.prompt, args.model)
        output_path = os.path.join(output_dir, filename)
    
    # Print configuration
    print(f"Configuration:")
    print(f"Image: {args.image}")
    print(f"Prompt: {args.prompt}")
    print(f"Model: {args.model}")
    print(f"Output will be saved to: {output_path}")
    print(f"Poll interval: {args.poll_interval} seconds")
    
    # Prepare API request
    url = "https://api.minimaxi.chat/v1/video_generation"
    
    payload = json.dumps({
        "model": args.model,
        "prompt": args.prompt,
        "first_frame_image": f"data:image/jpeg;base64,{data}"
    })
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    # Submit the video generation task
    print(f"Submitting video generation task to MiniMax API...")
    api_request_start = time.time()
    response = requests.post(url, headers=headers, data=payload)
    api_request_duration = time.time() - api_request_start
    
    if response.status_code != 200:
        print(f"Error: API request failed with status code {response.status_code}")
        print(f"Response: {response.text}")
        return
    
    print(f"API request completed in {api_request_duration:.2f} seconds")
    
    try:
        response_data = response.json()
    except json.JSONDecodeError:
        print(f"Error: Failed to parse API response as JSON")
        print(f"Response: {response.text}")
        return
    
    # Get task ID for tracking
    task_id = response_data.get('task_id')
    if not task_id:
        print("Error: No task_id in API response")
        print(f"Response: {json.dumps(response_data, indent=2)}")
        return
    
    print(f"Video generation task submitted successfully. Task ID: {task_id}")
    
    # Poll for task completion
    generation_start = time.time()
    poll_count = 0
    
    while True:
        poll_count += 1
        print(f"Polling for task status... (Attempt #{poll_count})")
        
        file_id, status = query_video_generation(api_key, task_id)
        
        elapsed = time.time() - generation_start
        print(f"Status: {status} - Time elapsed: {format_time_elapsed(elapsed)}")
        
        if status == "Success" and file_id:
            generation_duration = time.time() - generation_start
            print(f"Video generation completed in {format_time_elapsed(generation_duration)}!")
            
            # Fetch and save the video
            if fetch_video_result(api_key, file_id, output_path):
                total_duration = time.time() - start_time
                print(f"Video saved to {output_path}")
                print(f"Total process completed in {format_time_elapsed(total_duration)}")
                print(f"Video generation statistics:")
                print(f"  - API request time: {api_request_duration:.2f} seconds")
                print(f"  - Generation time: {generation_duration:.2f} seconds")
                print(f"  - Polling attempts: {poll_count}")
                print(f"  - Average time per poll: {generation_duration/poll_count:.2f} seconds")
            break
        elif status in ["Fail", "Error", "Unknown"]:
            generation_duration = time.time() - generation_start
            print(f"Generation failed after {format_time_elapsed(generation_duration)}")
            print(f"Total time elapsed: {format_time_elapsed(time.time() - start_time)}")
            return
        else:
            # Status is one of: "Preparing", "Queueing", "Processing"
            time.sleep(args.poll_interval)

if __name__ == "__main__":
    main()
