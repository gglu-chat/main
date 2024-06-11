import time
import math

class RateLimiter:
    def __init__(self, records=None, threshold=35, hashes=None):
        self.records = records if records is not None else {}
        self.threshold = threshold
        self.hashes = hashes if hashes is not None else {}

    def search(self, id):
        """Finding current score by `id`.
        
        :param id: target sid / hash
        """
        if id not in self.records:
            self.records[id] = {'time': time.time(), 'score': 0}
        return self.records[id]

    def frisk(self, id, deltaScore):
        """Adjusting the rate limiter via delta score.
           Mathematical model using exponential decay:
           new_score = old_score * exp(-decay_rate * time_diff) + deltaScore

        :param id: target sid / iphash
        :param deltaScore: adjusting the current score
        """
        decay_rate = 0.1  # Decay rate, you can adjust it according to your needs
        record = self.search(id)
        current_time = time.time()
        time_diff = current_time - record['time']

        # Apply exponential decay to the old score
        record['score'] = record['score'] * math.exp(-decay_rate * time_diff) + deltaScore

        # Update the record's time to the current time
        record['time'] = current_time

        # Check if the score exceeds the threshold
        if record['score'] >= self.threshold:
            return True
        return False

    def arrest(self, id, hash):
        """Blocking users from joining any room / sending messages.
        
        :param id: target sid / hash
        :param hash: target hash
        """
        record = self.search(id)
        record['arrested'] = True
        self.hashes[hash] = id

    def pardon(self, id):
        """Unblock users.
        
        :param id: target sid / hash
        """
        targetId = id
        if targetId in self.hashes:
            targetId = self.hashes[targetId]
        record = self.search(targetId)
        record['arrested'] = False

    def clear(self):
        """Clear all records."""
        
        self.records = {}
        self.hashes = {}
