import os
import numpy as np
import tensorflow as tf
from tensorflow.keras.applications import ResNet50
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D
from tensorflow.keras.models import Model
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.preprocessing.image import ImageDataGenerator
import argparse
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('logs', 'training.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def parse_arguments():
    parser = argparse.ArgumentParser(description='Train ResNet model for crime detection')
    parser.add_argument('--data-dir', help='Path to training data directory', required=True)
    parser.add_argument('--output-model', help='Path to save trained model', 
                        default=os.path.join('models', 'crime_detection_model.h5'))
    parser.add_argument('--epochs', help='Number of training epochs', type=int, default=20)
    parser.add_argument('--batch-size', help='Batch size for training', type=int, default=32)
    parser.add_argument('--learning-rate', help='Learning rate', type=float, default=0.0001)
    parser.add_argument('--img-size', help='Image size (width, height)', type=int, default=224)
    parser.add_argument('--validation-split', help='Validation split ratio', type=float, default=0.2)
    return parser.parse_args()

def build_model(num_classes, img_size=224, learning_rate=0.0001):
    # Load ResNet50 with pre-trained weights
    base_model = ResNet50(weights='imagenet', include_top=False, input_shape=(img_size, img_size, 3))
    
    # Add custom layers
    x = base_model.output
    x = GlobalAveragePooling2D()(x)
    x = Dense(1024, activation='relu')(x)
    predictions = Dense(num_classes, activation='softmax')(x)
    
    # Create model
    model = Model(inputs=base_model.input, outputs=predictions)
    
    # Freeze base model layers
    for layer in base_model.layers:
        layer.trainable = False
    
    # Compile model
    model.compile(
        optimizer=Adam(learning_rate=learning_rate),
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )
    
    return model

def train_model(data_dir, output_model_path, epochs=20, batch_size=32, learning_rate=0.0001, 
                img_size=224, validation_split=0.2):
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_model_path), exist_ok=True)
    
    # Data generators
    train_datagen = ImageDataGenerator(
        rescale=1./255,
        rotation_range=20,
        width_shift_range=0.2,
        height_shift_range=0.2,
        shear_range=0.2,
        zoom_range=0.2,
        horizontal_flip=True,
        fill_mode='nearest',
        validation_split=validation_split
    )
    
    # Training generator
    train_generator = train_datagen.flow_from_directory(
        data_dir,
        target_size=(img_size, img_size),
        batch_size=batch_size,
        class_mode='categorical',
        subset='training'
    )
    
    # Validation generator
    validation_generator = train_datagen.flow_from_directory(
        data_dir,
        target_size=(img_size, img_size),
        batch_size=batch_size,
        class_mode='categorical',
        subset='validation'
    )
    
    # Get class names and count
    class_names = list(train_generator.class_indices.keys())
    num_classes = len(class_names)
    
    logger.info(f"Found {num_classes} classes: {class_names}")
    logger.info(f"Training on {train_generator.samples} samples")
    logger.info(f"Validating on {validation_generator.samples} samples")
    
    # Build model
    model = build_model(num_classes, img_size, learning_rate)
    
    # Train model
    history = model.fit(
        train_generator,
        steps_per_epoch=train_generator.samples // batch_size,
        epochs=epochs,
        validation_data=validation_generator,
        validation_steps=validation_generator.samples // batch_size
    )
    
    # Save model
    model.save(output_model_path)
    logger.info(f"Model saved to {output_model_path}")
    
    # Save class names
    class_names_path = os.path.join(os.path.dirname(output_model_path), 'class_names.txt')
    with open(class_names_path, 'w') as f:
        for class_name in class_names:
            f.write(f"{class_name}\n")
    logger.info(f"Class names saved to {class_names_path}")
    
    # Fine-tune model (unfreeze some layers)
    logger.info("Fine-tuning model...")
    for layer in model.layers[-20:]:  # Unfreeze last 20 layers
        layer.trainable = True
    
    # Recompile model with lower learning rate
    model.compile(
        optimizer=Adam(learning_rate=learning_rate/10),
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )
    
    # Continue training
    history = model.fit(
        train_generator,
        steps_per_epoch=train_generator.samples // batch_size,
        epochs=epochs // 2,  # Fewer epochs for fine-tuning
        validation_data=validation_generator,
        validation_steps=validation_generator.samples // batch_size
    )
    
    # Save fine-tuned model
    fine_tuned_path = os.path.join(os.path.dirname(output_model_path), 'crime_detection_model_fine_tuned.h5')
    model.save(fine_tuned_path)
    logger.info(f"Fine-tuned model saved to {fine_tuned_path}")
    
    return model, history

def main():
    args = parse_arguments()
    
    # Train model
    model, history = train_model(
        args.data_dir,
        args.output_model,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        img_size=args.img_size,
        validation_split=args.validation_split
    )
    
    logger.info("Training completed successfully")

if __name__ == "__main__":
    main()