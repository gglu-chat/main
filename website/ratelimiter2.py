import time
import math

class RateLimiter2:
    def __init__(self, records=None, threshold=1500, hashes=None, penalty=0,
                 chars_per_line=35, max_char_per_ms=0.0025):
        self.records = records if records is not None else {}
        self.threshold = threshold
        self.hashes = hashes if hashes is not None else {}
        self.penalty = penalty
        self.chars_per_line = chars_per_line
        self.max_char_per_ms = max_char_per_ms

    def lineCount(self, msg):
        """计算消息的行数

        :param s: 指定的消息
        """
        strays = 0
        ans = 1
        for i in range(len(msg)):
            if msg[i] == '\n':
                strays = 0
                ans += 1
            elif msg[i] == '>' and (i == 0 or msg[i-1] == '\n'):
                while i < len(s) and msg[i] == '>':
                    ans += 2
                    i += 1
                strays = 0
                i -= 1
            else:
                strays += 1
            if strays == self.chars_per_line + 1:
                strays = 1
                ans += 1
        return ans

    def search(self, id):
        """以id寻找当前惩罚积分
        
        :param id: 指定的 sid / hash
        """
        if id not in self.records:
            self.records[id] = {'time': time.time() * 1000 - 10000, 'score': 0}
        return self.records[id]

    def frisk(self, id, msg):
        """通过用户所发消息，计算deltaScore以调整频率限制器

        :param id: 指定的 sid / iphash
        :param msg: 用户所发消息
        """
        half_life = 40
        decay_rate = math.log(2) / (half_life * 1000)
        record = self.search(id)
        if 'arrested' in record and record['arrested']:
            return True
        else:
            t = time.time() * 1000
            len_message = len(msg)
            line_count = self.lineCount(msg)
            deltatime = t - record['time']
            delta_score = min(750, (
                5 * min(max((len_message + 10) - deltatime * self.max_char_per_ms, 0.0), 120.0) + 
                1 * self.chars_per_line * line_count + 
                0.2 * len_message + 
                10 * max((6 - deltatime * 0.001), 0.0) * (6 - deltatime * 0.001)
            ))
            
            self.penalty = self.penalty * math.exp(-decay_rate * deltatime) + delta_score
            record['time'] = t
            record['score'] = self.penalty
            if record['score'] > self.threshold:
                if deltatime >= 120:
                    record['score'] = self.threshold - 300
                    record['time'] = time.time() * 1000
                    return False
                return True
        return False


    def arrest(self, id, hash):
        """封禁用户，不让其 加入房间/发送消息
        
        :param id: 指定的 sid / hash
        :param hash: 指定的 hash
        """
        record = self.search(id)
        record['arrested'] = True
        self.hashes[hash] = id

    def pardon(self, id):
        """解封用户
        
        :param id: 指定的 sid / hash
        """
        targetId = id
        if targetId in self.hashes:
            targetId = self.hashes[targetId]
        record = self.search(targetId)
        record['arrested'] = False

    def clear(self):
        """清除所有记录"""
        self.records = {}
        self.hashes = {}
