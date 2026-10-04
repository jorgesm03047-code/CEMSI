from PIL import Image
import sys

def make_transparent(img_path, out_path):
    img = Image.open(img_path).convert("RGBA")
    data = img.getdata()
    newData = []
    for item in data:
        # If pixel is very close to white, make it transparent
        if item[0] > 240 and item[1] > 240 and item[2] > 240:
            newData.append((255, 255, 255, 0))
        else:
            newData.append(item)
    img.putdata(newData)
    img.save(out_path, "WEBP")

make_transparent(sys.argv[1], sys.argv[2])
