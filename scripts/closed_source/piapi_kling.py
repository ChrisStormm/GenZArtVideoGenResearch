#!/usr/bin/env python
"""
Script to generate videos from images using PiAPI Kling API
"""

import argparse
import os
import time
import requests
import json
import base64
from PIL import Image
import io
import datetime
import uuid
import dotenv

# Load environment variables from .env file
dotenv.load_dotenv()

def parse_args():
    parser = argparse.ArgumentParser(description="Generate video from image using PiAPI Kling API")
    parser.add_argument("--image", type=str, help="Path to local image file")
    parser.add_argument("--image_url", type=str, help="URL to an image (alternative to --image)")
    parser.add_argument("--prompt", type=str, required=True, help="Text prompt to guide the video generation")
    parser.add_argument("--output_dir", type=str, default="outputs", help="Directory to save the output video")
    parser.add_argument("--api_key", type=str, help="PiAPI API key (or set PIAPI_KEY env var)")
    parser.add_argument("--model", type=str, choices=["1.0", "1.5", "1.6", "2.0", "2.1"], default="2.0", 
                        help="Kling model version (1.0, 1.5, 1.6, or 2.0)")
    parser.add_argument("--mode", type=str, choices=["std", "pro"], default="std",
                        help="Generation mode: std or pro")
    parser.add_argument("--duration", type=int, choices=[5, 10], default=5,
                        help="Video duration in seconds (5 or 10)")
    parser.add_argument("--negative_prompt", type=str, default="", 
                        help="Negative prompt to guide the video generation")
    parser.add_argument("--aspect_ratio", type=str, choices=["16:9", "9:16", "1:1"], default="16:9",
                        help="Aspect ratio of the generated video")
    
    args = parser.parse_args()
    
    # Validate that either image or image_url is provided
    if not args.image and not args.image_url:
        parser.error("Either --image or --image_url must be provided")
    if args.image and args.image_url:
        parser.error("Please provide either --image or --image_url, not both")
        
    return args

def upload_image(image_path):
    """
    Upload image to an image hosting service and return the URL.
    Note: This is a placeholder. In a real implementation, you would:
    1. Use a service like ImgBB, Imgur, Cloudinary, etc.
    2. Or use PiAPI's own file upload API if available
    """
    print("WARNING: Direct image upload not implemented.")
    print("Please host your image online and use --image_url instead.")
    raise NotImplementedError("Image upload not implemented. Use --image_url instead.")

def generate_unique_filename(prompt, model, mode, ext=".mp4"):
    """Generate a unique filename based on timestamp, prompt and parameters"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    # Create a short hash of the prompt (first 8 chars)
    prompt_hash = str(uuid.uuid5(uuid.NAMESPACE_DNS, prompt))[:8]
    # Sanitize prompt for filename (take first 20 chars and replace problematic chars)
    safe_prompt = "".join(c if c.isalnum() else "_" for c in prompt[:20]).lower()
    return f"kling_{timestamp}_{safe_prompt}_{prompt_hash}_{model}_{mode}{ext}"

def main():
    args = parse_args()
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Generate a unique filename
    output_filename = generate_unique_filename(args.prompt, args.model, args.mode)
    output_path = os.path.join(args.output_dir, output_filename)
    
    # Get API key from arguments or environment
    api_key = args.api_key or os.environ.get("PIAPI_KEY")
    if not api_key:
        print("Error: PiAPI API key not provided. Use --api_key or set PIAPI_KEY environment variable.")
        return
    
    # Get image URL
    image_url = args.image_url
    if args.image:
        # Check if input image exists
        if not os.path.isfile(args.image):
            print(f"Error: Input image '{args.image}' does not exist")
            return
        
        # Here you would upload the image and get a URL
        # This would require implementing the upload_image function
        try:
            image_url = upload_image(args.image)
        except NotImplementedError:
            print("Please use --image_url with a URL to an already hosted image.")
            return
    
    # Print configuration
    print(f"Image URL: {image_url}")
    print(f"Prompt: {args.prompt}")
    print(f"Model version: {args.model}")
    print(f"Mode: {args.mode}")
    print(f"Duration: {args.duration} seconds")
    print(f"Aspect Ratio: {args.aspect_ratio}")
    print(f"Output video will be saved to: {output_path}")
    
    # Prepare API request
    url = "https://api.piapi.ai/api/v1/task"
    
    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json"
    }
    
    # Prepare payload according to PiAPI Kling API documentation
    payload = {
        "model": "kling",
        "task_type": "video_generation",
        "input": {
            "prompt": args.prompt,
            "negative_prompt": args.negative_prompt,
            "cfg_scale": 0.5,  # Recommended value from docs
            "duration": args.duration,
            "aspect_ratio": args.aspect_ratio,
            "mode": args.mode,
            "version": args.model,
            "image_url": image_url
        }
    }
    
    # Call API
    print(f"Sending request to PiAPI Kling API using model version {args.model}...")
    start_time = time.time()
    
    try:
        print(f"Sending request with payload:")
        print(json.dumps(payload, indent=2))
        
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code != 200:
            print(f"\n==== API REQUEST FAILED ====")
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
            try:
                error_json = response.json()
                print(f"Response JSON: {json.dumps(error_json, indent=2)}")
            except:
                print("Response is not valid JSON")
            return
        
        # Process the response
        response_data = response.json()
        
        if response_data.get("code") != 200:
            print(f"\n==== API RESPONSE ERROR ====")
            print(f"Error code: {response_data.get('code')}")
            print(f"Message: {response_data.get('message')}")
            print(f"Full response: {json.dumps(response_data, indent=2)}")
            return
            
        # Get task ID for tracking
        task_id = response_data.get("data", {}).get("task_id")
        if not task_id:
            print("Error: No task ID received in API response")
            print(f"Response: {json.dumps(response_data, indent=2)}")
            return
            
        print(f"Task submitted successfully. Task ID: {task_id}")
        
        # Poll for results
        status_url = f"https://api.piapi.ai/api/v1/task/{task_id}"
        while True:
            print("Waiting for generation to complete...")
            time.sleep(5)  # Check every 5 seconds
            
            status_response = requests.get(status_url, headers=headers)
            
            if status_response.status_code != 200:
                print(f"\n==== STATUS CHECK FAILED ====")
                print(f"Status code: {status_response.status_code}")
                print(f"Response: {status_response.text}")
                try:
                    error_json = status_response.json()
                    print(f"Response JSON: {json.dumps(error_json, indent=2)}")
                except:
                    print("Response is not valid JSON")
                continue
                
            status_data = status_response.json()
            
            if status_data.get("code") != 200:
                print(f"\n==== STATUS CHECK ERROR ====")
                print(f"Error code: {status_data.get('code')}")
                print(f"Message: {status_data.get('message')}")
                print(f"Full response: {json.dumps(status_data, indent=2)}")
                continue
                
            # Process the status response to check completion
            task_status = status_data.get("data", {}).get("status", "").lower()
            
            if task_status == "completed" or task_status == "Completed":
                print("Generation completed!")
                break
            elif task_status == "failed":
                print("\n==== TASK FAILED ====")
                
                # Extract error details
                error_obj = status_data.get("data", {}).get("error", {})
                error_message = error_obj.get("message", "No error message")
                error_code = error_obj.get("code", "No error code")
                error_raw = error_obj.get("raw_message", "No raw error message")
                error_detail = error_obj.get("detail", "No error details")
                
                print(f"Error code: {error_code}")
                print(f"Error message: {error_message}")
                print(f"Raw error: {error_raw}")
                print(f"Error details: {error_detail}")
                
                # Print any logs that might provide more context
                logs = status_data.get("data", {}).get("logs", [])
                if logs:
                    print("\nTask logs:")
                    for i, log in enumerate(logs):
                        print(f"  Log {i+1}: {json.dumps(log, indent=2)}")
                
                # Print the full response for debugging
                print("\nFull response data:")
                print(json.dumps(status_data.get("data", {}), indent=2))
                
                return
            else:
                # Extract progress if available
                progress = "unknown"
                for log in status_data.get("data", {}).get("logs", []):
                    if "progress" in log:
                        progress = log.get("progress", "unknown")
                print(f"Status: {task_status} - Progress: {progress}")
        
        # Get the final result
        final_response = requests.get(status_url, headers=headers)
        if final_response.status_code != 200:
            print(f"Error getting final result: {final_response.status_code}")
            print(f"Response: {final_response.text}")
            return
            
        final_data = final_response.json()
        
        # Extract video URL
        video_url = final_data.get("data", {}).get("output", {}).get("video_url")
        if not video_url:
            print("Error: No video URL in API response")
            print(f"Response: {json.dumps(final_data, indent=2)}")
            return
        
        generation_time = time.time() - start_time
        print(f"Video generation completed in {generation_time:.2f} seconds")
        
        # Download and save the video
        print(f"Downloading video from {video_url}...")
        video_response = requests.get(video_url)
        
        if video_response.status_code != 200:
            print(f"Error downloading video: {video_response.status_code}")
            return
            
        with open(output_path, "wb") as f:
            f.write(video_response.content)
        
        print(f"Video saved to {output_path}")
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main() 