# Model Download Instructions

## Crime Detection Model

The crime detection model is based on a fine-tuned ResNet50 architecture trained on a custom dataset of crime scenes and normal activities. Due to the large file size, the model is not included in this repository.

### Download Link

You can download the pre-trained crime detection model from the following link:

[Download Crime Detection Model](https://drive.google.com/file/d/1XYZ123_placeholder_link/view?usp=sharing)

### Installation

1. Download the model file (`crime_detection_model.h5`)
2. Place it in the `models/` directory of this project

## Weapon Detection Model

The weapon detection model is trained to identify common weapons like guns and knives in images and video frames.

### Download Link

You can download the pre-trained weapon detection model from the following link:

[Download Weapon Detection Model](https://drive.google.com/file/d/1ABC456_placeholder_link/view?usp=sharing)

### Installation

1. Download the model file (`weapon_detection_model.h5`)
2. Place it in the `models/` directory of this project

## Alternative: Using Your Own Models

If you want to use your own trained models, you can place them in the `models/` directory with the following names:

- `crime_detection_model.h5` - For crime detection
- `weapon_detection_model.h5` - For weapon detection

Alternatively, you can specify custom paths in the `.env` file:

```
CRIME_MODEL_PATH=path/to/your/crime/model.h5
WEAPON_MODEL_PATH=path/to/your/weapon/model.h5
```

## Note on Development Mode

If you run the application without the model files, it will operate in development mode with simulated detections. This is useful for testing the UI and workflow without the actual AI models.
