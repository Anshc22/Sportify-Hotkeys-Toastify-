
from PIL import Image, ImageDraw

def create_icon():
    # Create images of different sizes for the ICO file
    sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    images = []
    
    for size in sizes:
        # Create a new image with transparent background
        img = Image.new('RGBA', size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Calculate circle dimensions
        padding = size[0] // 8
        circle_size = (padding, padding, size[0] - padding, size[1] - padding)
        
        # Draw a filled circle with Spotify green color
        draw.ellipse(circle_size, fill='#1DB954')
        
        images.append(img)
    
    # Save as ICO file with multiple sizes
    images[0].save('icon.ico', format='ICO', sizes=[(x, x) for x, _ in sizes])
    print("Icon file created successfully!")

if __name__ == "__main__":
    create_icon()