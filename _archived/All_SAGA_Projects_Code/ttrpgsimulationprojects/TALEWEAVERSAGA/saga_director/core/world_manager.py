import random
import hashlib

class WorldManager:
    def __init__(self, world_seed: int):
        self.world_seed = world_seed

    def get_seed(self, *args):
        """Generates a deterministic seed from a list of arguments and the world master seed."""
        seed_str = f"{self.world_seed}_" + "_".join(map(str, args))
        # Use first 8 chars of hex md5 as an integer
        return int(hashlib.md5(seed_str.encode()).hexdigest()[:8], 16)

    def get_rng(self, *args):
        """Returns a seeded Random instance for deterministic generation."""
        return random.Random(self.get_seed(*args))
