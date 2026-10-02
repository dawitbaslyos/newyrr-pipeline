import os
from image_runner import ImageGenerator

# Maintain backwards compatibility for existing imports
FluxRunPodClient = ImageGenerator

if __name__ == "__main__":
    gen = FluxRunPodClient()
    test_out = os.path.join(os.path.dirname(__file__), "test_flux_sync.png")
    res = gen.generate_image("A futuristic teal sports car, 9:16 vertical", test_out)
    print("Generation completed:", res)
