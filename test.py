import math
from bitarray import util as bitutil
from rbokvs import RBOKVS

# 构建随机 key-value 型数据，其中 value 为 bytes 类型
test_kv = {}

for i in range(1000):
    value = bitutil.urandom(8)
    test_kv.setdefault(str(i), value.tobytes())
# -------------------------------------------------

# 设定 RB-OKVS 参数，计算最终的编码结果 s
M = math.ceil(len(test_kv) * 1.1)
w = 384
rbokvs = RBOKVS(M, len(test_kv), w)
s = rbokvs.encode(test_kv)
# ------------------------------------

# 测试，给定 key，输出对应的 value
for i in range(1000):
    print(test_kv.get(str(i)) == rbokvs.decode(str(i), s))
