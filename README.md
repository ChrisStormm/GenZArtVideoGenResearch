# GenZArt Video Generation Research

A collection of standalone scripts for testing different video generation models using images and prompts.

## Project Structure

```
GenZArtVideoGenResearch/
├── inputs/              # Input images 
├── outputs/             # Generated videos
├── scripts/             # Standalone scripts for different models
├── requirements.txt     # Project dependencies
└── README.md            # Project documentation
```

### Installation

1. Clone this repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

Input image urls:

-https://i.imgur.com/mbvOZ38.jpeg (Studying Ghibli style)
-https://i.imgur.com/a4wxAeV.jpeg (cats on table)


Trigger kling api command:
python3 scripts/closed_source/piapi_kling.py --image_url "https://i.imgur.com/mbvOZ38.jpeg" --prompt "A focused man is studying and listening to music." --model 1.0 --mode std --duration 5
