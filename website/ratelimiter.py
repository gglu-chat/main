import time

class RateLimiter:
    def __init__(self, records={}, 
                halflife=30000, threshold=25, hashes=[]):
        self.records = records
        self.halflife = halflife
        self.threshold = threshold
        self.hashes = hashes

    def search(self, id_):
        try:
            record = self.records[id_]
        except:
            self.records[id_] = {'time': int(round(time.time() * 1000)), 'score': 0}
            record = self.records[id_]
        return record

    def frisk(self, id_, deltaScore):
        record = self.search(id_)
        if record['arrested']:
            return True
        record['score'] *= pow(2, -(int(round(time.time() * 1000)) - record['time']) / self.halflife)
        record['score'] += deltaScore
        record['time'] = int(round(time.time() * 1000))
        if record['score'] >= self.threshold:
            return True
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
        self.hashes = []
