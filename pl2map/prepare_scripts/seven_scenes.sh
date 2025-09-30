#!/bin/bash

if [ ! -d "train_test_datasets" ]; then
  mkdir train_test_datasets
fi

if [ ! -d "train_test_datasets/gt_3Dmodels" ]; then
  mkdir train_test_datasets/gt_3Dmodels
fi

if [ ! -d "train_test_datasets/imgs_datasets" ]; then
  mkdir train_test_datasets/imgs_datasets
fi

TARGET_FOLDER="train_test_datasets/gt_3Dmodels"
OUTPUT_FILE="7scenes.zip"
FILE_ID="1X8_tV0Y4b_W-vPgeXKoqtFaDCQ5_csL3"

# Download the file from Google Drive using gdown and save it in the target folder
gdown --id $FILE_ID -O $TARGET_FOLDER/$OUTPUT_FILE

# Unzip the downloaded file in the target folder
unzip $TARGET_FOLDER/$OUTPUT_FILE -d $TARGET_FOLDER

# Remove the zip file after extraction
rm $TARGET_FOLDER/$OUTPUT_FILE

echo "Download, extraction, and cleanup completed in $TARGET_FOLDER."


cd train_test_datasets/imgs_datasets
mkdir 7scenes
cd 7scenes

# List of datasets
datasets=("chess" "fire" "heads" "office" "pumpkin" "redkitchen" "stairs")

# Loop through each dataset
for ds in "${datasets[@]}"; do
    # Check if the dataset directory exists
    if [ ! -d "$ds" ]; then
        echo "=== Downloading 7scenes Data: $ds ==============================="
        
        # Download the dataset zip file
        wget "http://download.microsoft.com/download/2/8/5/28564B23-0828-408F-8631-23B1EFF1DAC8/$ds.zip"
        
        # Unzip the dataset
        unzip "$ds.zip"
        
        # Remove the zip file
        rm "$ds.zip"

        # Loop through the dataset folder and unzip any additional zip files
        for file in "$ds"/*.zip; do
            if [ -f "$file" ]; then
                echo "Unpacking $file"
                unzip "$file" -d "$ds"
                rm "$file"
            fi
        done
    else
        echo "Found data of scene $ds already. Assuming its complete and skipping download."
    fi
done
