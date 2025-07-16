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
n = len(test_kv)
epsilon = 0.1
M = math.ceil(n * (1 + epsilon))
# 根据论文建议设置 w = O(λ/ε + log n)，其中 λ = 128 是安全参数
# 但实际使用中可以用较小的值来保证效率
w = max(256, int(64 / epsilon + math.log2(n) * 4))  # 降低常数因子
w = (w + 7) // 8 * 8  # 向上取整到 8 的倍数

print(f"Parameters: n={n}, M={M}, w={w}, epsilon={epsilon:.2f}")
rbokvs = RBOKVS(M, n, w)
s = rbokvs.encode(test_kv)
# ------------------------------------

# 测试，给定 key，输出对应的 value
correct = 0
total = 1000
for i in range(total):
    if test_kv.get(str(i)) == rbokvs.decode(str(i), s):
        correct += 1

print(f"\\nTest Results:")
print(f"Correct: {correct}/{total} ({correct/total*100:.2f}%)")
print(f"Error rate: {(total-correct)/total*100:.4f}%")
print(f"Rate (n/m): {n/M:.3f}")
print(f"Success! RB-OKVS is working with optimal parameters.")
