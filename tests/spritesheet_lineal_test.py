from spriteworkflow.spritesheet_lineal import create_spritesheet_lineal

spritesheet = create_spritesheet_lineal(frames_dir="temp/frames_6t249_qe", output_file="output/samurai2_spritesheet")

print("Spritesheet created successfully: output/samurai2_spritesheet.png")
print(spritesheet)