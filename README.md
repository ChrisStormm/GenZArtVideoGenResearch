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

Trigger hailuo api command:
python3 scripts/closed_source/minMax_hailuo.py --image inputs/cats_on_table.jpg --prompt "A humorous scene featuring two cats at a dining table. tl , a gray and white tabby cat appears, looking cheerful and convey a sense of mischief." --model I2V-01-Director