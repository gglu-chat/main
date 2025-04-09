"""此频率限制其已弃用，使用ratelimiter2"""
import time
import math

class RateLimiter:
    def __init__(self, records={}, threshold=35, hashes:dict={}):
        self.records = records
        self.threshold = threshold
        self.hashes = hashes

    def search(self, id):
        """Finding current score by `id`.
        
        :param id: target sid / hash
        """
        try:
            record = self.records[id]
        except:
            self.records[id] = {'time': time.time(), 'score': 0}
            record = self.records[id]
        return record

    def frisk(self, id, deltaScore):
        """Adjusting the ratelimiter via deltascore.
           mathematical models: 
        `y=p\left(\\frac{\ln\left(x+1\right)}{0.3\min\left(s,50\right)+0.06}\right)+0.5p+1`

        :param id: target sid / iphash
        :param deltaScore: adjusting the current score
        """
        record = self.search(id)
        try:
            if record['arrested']:
                return True
        except:
            p = record['score']
            dltime = time.time() - record['time']
            record['score'] = (math.log(deltaScore + 1) / (0.3 * min(dltime, 50) + 0.06)) * p + 0.5 * p + 1
            if record['score'] >= self.threshold:
                if dltime >= 120:
                    record['score'] = self.threshold
                    record['time'] = time.time()
                    return False
                return True
        record['time'] = time.time()
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
        try:
            type(self.hashes[targetId])
        except:
            targetId = self.hashes[targetId]
        record = self.search(targetId)
        record['arrested'] = False

    def clear(self):
        """Clear all records."""
        self.records = {}
        self.hashes = {}
