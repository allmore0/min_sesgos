import random
import string
import json

class MultiSubstitutionCipher:
    def __init__(self, key_seed=42):
        """
        Initializes the cipher with a seed to generate consistent substitution tables.
        In a real scenario, the keys would be stored securely.
        """
        self.key_seed = key_seed
        self.num_layers = 3 # Number of substitution layers
        self.maps = self._generate_maps()

    def _generate_maps(self):
        """Generates multiple random substitution maps."""
        random.seed(self.key_seed)
        chars = string.printable
        maps = []
        for _ in range(self.num_layers):
            shuffled = list(chars)
            random.shuffle(shuffled)
            enc_map = {c: s for c, s in zip(chars, shuffled)}
            dec_map = {s: c for c, s in zip(chars, shuffled)}
            maps.append((enc_map, dec_map))
        return maps

    def encrypt(self, text):
        """Applies multiple layers of substitution."""
        if not isinstance(text, str):
            text = json.dumps(text) # Convert dict/list to string if needed
        
        current_text = text
        for enc_map, _ in self.maps:
            new_text = []
            for char in current_text:
                new_text.append(enc_map.get(char, char))
            current_text = "".join(new_text)
        return current_text

    def decrypt(self, text):
        """Reverses the multiple layers of substitution."""
        current_text = text
        for _, dec_map in reversed(self.maps):
            new_text = []
            for char in current_text:
                new_text.append(dec_map.get(char, char))
            current_text = "".join(new_text)
        return current_text

# Example usage
# cipher = MultiSubstitutionCipher()
# encrypted = cipher.encrypt("Hello World")
# decrypted = cipher.decrypt(encrypted)
