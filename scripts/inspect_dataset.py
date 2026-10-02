from pathlib import Path
# It gives us a clean way to work with files and folders.
from PIL import Image
# Pillow allows Python to work with image files. We used that to find dimensions of the dataset image and to open the image.

# Path to our raw dataset
DATASET_PATH = Path("dataset/raw")
# This tells that where our datset is present currently, the path or we can say that the location of our dataset currently.

# Find all image files
image_files = sorted(
    [
        file
        for file in DATASET_PATH.iterdir()
        # What does "DATASET_PATH.iterdir()" do?"
        # Answer: Look inside dataset/raw and give me everything that's there.
        #         For example:
        #         1.jpg
        #         2.jpg
        #         3.jpg
        #         4.jpg
        #         notes.txt
        #         Python can iterate through these items.

        if file.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]
        # .suffix means gets the file extension like- jpg", ".jpeg", ".png", ".webp.
        # And this whole line means that add the file in the list if they have extension one of these.
    ],
    key=lambda file: int(file.stem)
)


print("=" * 50)
print("DATASET INSPECTION")
print("=" * 50)

print(f"Total images: {len(image_files)}")


# Count file extensions
extensions = {}

for file in image_files:
    extension = file.suffix.lower()
    extensions[extension] = extensions.get(extension, 0) + 1


print("\nFile types:")

for extension, count in extensions.items():
    print(f"{extension}: {count}")


# Inspect the first 10 images
print("\nFirst 20 images:")

for file in image_files[:20]:

    try:
        with Image.open(file) as image:
            width, height = image.size

        print(f"{file.name} → {width}x{height}")

    except Exception as error:
        print(f"{file.name} → ERROR: {error}")


print("\n" + "=" * 50)