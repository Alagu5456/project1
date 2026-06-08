import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout
from tensorflow.keras.models import Model
from tensorflow.keras.optimizers import Adam
import os

def build_model(num_classes):
    # Use MobileNetV2 for transfer learning (efficient and accurate for this task)
    base_model = MobileNetV2(weights='imagenet', include_top=False, input_shape=(224, 224, 3))
    
    # Freeze base model layers
    base_model.trainable = False
    
    # Add custom head
    x = base_model.output
    x = GlobalAveragePooling2D()(x)
    x = Dense(128, activation='relu')(x)
    x = Dropout(0.5)(x)
    predictions = Dense(num_classes, activation='softmax')(x)
    
    model = Model(inputs=base_model.input, outputs=predictions)
    return model

def train_model(data_dir='dataset', epochs=10, batch_size=32):
    # Data Augmentation
    train_datagen = ImageDataGenerator(
        rescale=1./255,
        rotation_range=20,
        width_shift_range=0.2,
        height_shift_range=0.2,
        shear_range=0.2,
        zoom_range=0.2,
        horizontal_flip=True,
        validation_split=0.2
    )
    
    train_generator = train_datagen.flow_from_directory(
        data_dir,
        target_size=(224, 224),
        batch_size=batch_size,
        class_mode='categorical',
        subset='training'
    )
    
    validation_generator = train_datagen.flow_from_directory(
        data_dir,
        target_size=(224, 224),
        batch_size=batch_size,
        class_mode='categorical',
        subset='validation'
    )
    
    num_classes = len(train_generator.class_indices)
    print(f"Classes found: {train_generator.class_indices}")
    
    model = build_model(num_classes)
    
    model.compile(optimizer=Adam(learning_rate=0.0001),
                  loss='categorical_crossentropy',
                  metrics=['accuracy'])
    
    model.fit(
        train_generator,
        steps_per_epoch=train_generator.samples // batch_size,
        validation_data=validation_generator,
        validation_steps=validation_generator.samples // batch_size,
        epochs=epochs
    )
    
    # Save the model
    model.save('condition_detection_model.h5')
    print("Model saved as condition_detection_model.h5")
    
    # Save class indices
    import pickle
    with open('condition_class_indices.pkl', 'wb') as f:
        pickle.dump(train_generator.class_indices, f)

if __name__ == "__main__":
    # Create dummy dataset folder structure if it doesn't exist (for demonstration)
    if not os.path.exists('dataset'):
        os.makedirs('dataset/New', exist_ok=True)
        os.makedirs('dataset/Good', exist_ok=True)
        os.makedirs('dataset/Fair', exist_ok=True)
        os.makedirs('dataset/Poor', exist_ok=True)
        print("Created dataset folder structure. Please add images to dataset/New, dataset/Good, etc. before training.")
    else:
        try:
            train_model()
        except Exception as e:
            print(f"Training failed (likely no images): {e}")
