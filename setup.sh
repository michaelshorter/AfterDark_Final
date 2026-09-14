#!/bin/bash
echo "Setting up AfterDark Jukebox..."

# System dependencies
sudo apt update
sudo apt install -y vlc python3-lgpio swig python3-full unclutter

# Create venv
python3 -m venv ~/jukebox-env --system-site-packages

# Install Python dependencies
source ~/jukebox-env/bin/activate
pip install -r requirements.txt

# Make launch script executable
chmod +x run_jukebox.sh

# Set up autostart
mkdir -p ~/.config/autostart
cat > ~/.config/autostart/jukebox.desktop << EOF
[Desktop Entry]
Type=Application
Name=AfterDark Jukebox
Exec=/home/jukebox/AfterDark2/run_jukebox.sh
EOF

# Generate idle images
echo "Generating screen images..."
python3 -c "
from PIL import Image, ImageDraw, ImageFont

# Insert token screen
img = Image.new('RGB', (1920, 1080), (0, 0, 0))
draw = ImageDraw.Draw(img)
font = ImageFont.load_default(size=80)
text = 'Please insert token'
bbox = draw.textbbox((0, 0), text, font=font)
w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
draw.text(((1920 - w) // 2, (1080 - h) // 2), text, fill=(255, 255, 255), font=font)
img.save('/media/jukebox/JUKEBOX/insert_token.png')
print('insert_token.png saved')

# Make your selection screen
img2 = Image.new('RGB', (1920, 1080), (0, 0, 0))
draw2 = ImageDraw.Draw(img2)
text2 = 'Please make your selection'
bbox2 = draw2.textbbox((0, 0), text2, font=font)
w2, h2 = bbox2[2] - bbox2[0], bbox2[3] - bbox2[1]
draw2.text(((1920 - w2) // 2, (1080 - h2) // 2), text2, fill=(255, 255, 255), font=font)
img2.save('/media/jukebox/JUKEBOX/make_selection.png')
print('make_selection.png saved')
"

echo ""
echo "Setup complete!"
echo "Add your .mp4 files to the JUKEBOX USB drive under /videos/"
echo "Then reboot and the jukebox will start automatically."
