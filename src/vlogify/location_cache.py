class LocationCache:

    def __init__(self):
        self.cache = {}

    def key(self, lat, lon):
        # rounding prevents tiny floating point differences
        return (round(lat, 4), round(lon, 4))

    def get(self, lat, lon):
        return self.cache.get(self.key(lat, lon))

    def set(self, lat, lon, location):
        self.cache[self.key(lat, lon)] = location