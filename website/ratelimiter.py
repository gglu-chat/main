import time
import math

class RateLimiter:
    def __init__(self, records={}, 
                halflife=30000, threshold=25, hashes:dict={}):
        self.records = records
        self.halflife = halflife
        self.threshold = threshold
        self.hashes = hashes

    def search(self, id_):
        try:
            record = self.records[id_]
        except:
            self.records[id_] = {'time': time.time(), 'score': 0}
            record = self.records[id_]
        return record

    def frisk(self, id_, deltaScore):
        record = self.search(id_)
        try:
            if record['arrested']:
                return True
        except:
            p = record['score']
            dltime = time.time() - record['time']
            record['score'] = (math.log(deltaScore) / (0.3 * min(dltime, 50) + 0.06)) * p + 0.5 * p + 1
            print(p)
            print(dltime)
            print(math.log(deltaScore))
            print(0.3 * min(dltime, 50) + 0.06)
            print(record['score'])
            if record['score'] >= self.threshold:
                if dltime >= 120:
                    record['score'] = 25
                    record['time'] = time.time()
                    return False
                return True
        record['time'] = time.time()
        return False

    def arrest(self, id_, hash):
        record = self.search(id_)
        record['arrested'] = True
        self.hashes[hash] = id_

    def pardon(self, id_):
        targetId = id_
        try:
            type(self.hashes[targetId])
        except:
            targetId = self.hashes[targetId]
        record = self.search(targetId)
        record['arrested'] = False

    def clear(self):
        self.records = {}
        self.hashes = {}
