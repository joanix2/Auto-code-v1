#!/usr/bin/env python3
"""
Simple script to generate placeholder PWA icons.
Creates basic colored icons for the web app manifest.
"""

try:
    from PIL import Image, ImageDraw, ImageFont
    import os

    def create_icon(size, filename, bg_color="#667eea", text_color="white"):
        """Create a simple icon with gradient background"""
        # Create image with gradient-like background
        img = Image.new('RGB', (size, size), bg_color)
        draw = ImageDraw.Draw(img)
        
        # Add a simple design - circle in the center
        margin = size // 4
        draw.ellipse([margin, margin, size-margin, size-margin], 
                     fill="#764ba2", outline=text_color, width=size//20)
        
        # Add text
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size//4)
        except:
            font = ImageFont.load_default()
        
        text = "AC"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        position = ((size - text_width) // 2, (size - text_height) // 2 - size//20)
        
        draw.text(position, text, fill=text_color, font=font)
        
        # Save
        img.save(filename, 'PNG')
        print(f"Created {filename}")

    # Create icons directory
    icon_dir = "frontend/public"
    os.makedirs(icon_dir, exist_ok=True)

    # Generate icons
    create_icon(192, os.path.join(icon_dir, "icon-192.png"))
    create_icon(512, os.path.join(icon_dir, "icon-512.png"))
    create_icon(180, os.path.join(icon_dir, "apple-touch-icon.png"))
    create_icon(32, os.path.join(icon_dir, "favicon-32x32.png"))
    create_icon(16, os.path.join(icon_dir, "favicon-16x16.png"))

    print("\n✅ All icons generated successfully!")
    print("Icons created in frontend/public/")

except ImportError:
    print("⚠️  PIL/Pillow not installed. Skipping icon generation.")
    print("Icons can be added manually to frontend/public/")
    print("\nTo generate icons, install Pillow:")
    print("  pip install Pillow")
    print("\nOr create icons manually using any image editor.")
