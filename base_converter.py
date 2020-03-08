class BaseConverter:

    base = "BZfnrp0mTsvWNzC31hXLDwj9VQbPFtGxJ7HY62kq4MgKcRly5d8S"

    def int_to_string(self, integer):
        if integer < 0:
            raise ValueError("negative numbers are not going to work!")
        if integer < len(self.base):
            return self.base[integer]
        result = []
        quotient = integer
        while quotient:
            quotient, remainder = divmod(quotient, len(self.base))
            result.append(self.base[remainder])
        return ''.join(reversed(result))

    def string_to_int(self, string):
        result = 0
        for i, v in enumerate(reversed(string)):
            try:
                digit = self.base.index(v)
            except ValueError:
                return 0
            result += digit * (len(self.base) ** i)
        return result

BaseConverter().string_to_int("ass")