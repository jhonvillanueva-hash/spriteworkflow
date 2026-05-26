from spriteworkflow.extractor import extract_frames

frames = extract_frames("assets/samurai_attack.mp4")

print(f"Frames extracted: {len(frames)}")

for frame in frames[:5]:
    print(frame)