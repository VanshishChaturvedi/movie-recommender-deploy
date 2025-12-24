import pickle
import numpy as np

print("Loading similarity matrix...")
similarity = pickle.load(open('similarity.pkl', 'rb'))

print(f"Original shape: {similarity.shape}")
print(f"Original dtype: {similarity.dtype}")
print(f"Original size (MB): {similarity.nbytes / 1024 / 1024:.2f}")

# Convert to float16
similarity_small = similarity.astype(np.float16)

print(f"New dtype: {similarity_small.dtype}")
print(f"New size (MB): {similarity_small.nbytes / 1024 / 1024:.2f}")

print("Saving optimized similarity matrix...")
pickle.dump(similarity_small, open('similarity.pkl', 'wb'))
print("Done!")
