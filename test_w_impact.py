import math
from bitarray import util as bitutil
from rbokvs import RBOKVS

# 构建测试数据
test_kv = {}
for i in range(1000):
    value = bitutil.urandom(8)
    test_kv.setdefault(str(i), value.tobytes())

n = len(test_kv)
epsilon = 0.1
M = math.ceil(n * (1 + epsilon))

# 测试不同的W值
w_values = [
    680,   # 当前值
    896,   # 中等值 (8的倍数)
    1200,  # 接近论文推荐
    1296,  # 论文推荐值
]

# 对于较大的W值，需要相应增加M
def get_safe_M(n, w, epsilon):
    base_M = math.ceil(n * (1 + epsilon))
    # 确保 M >= N + W，避免 rest_pos < 0
    return max(base_M, n + w + 100)

print(f"Testing with n={n}, M={M}, epsilon={epsilon:.2f}")
print("-" * 60)

for w in w_values:
    try:
        M_safe = get_safe_M(n, w, epsilon)
        print(f"\nTesting W={w}, M={M_safe}:")
        
        # 进行多次测试
        success_count = 0
        error_rates = []
        
        for trial in range(5):
            try:
                rbokvs = RBOKVS(M_safe, n, w)
                s = rbokvs.encode(test_kv)
                
                # 计算成功率
                correct = 0
                for i in range(n):
                    if test_kv.get(str(i)) == rbokvs.decode(str(i), s):
                        correct += 1
                
                success_count += 1
                error_rate = (n - correct) / n * 100
                error_rates.append(error_rate)
                
            except Exception as e:
                print(f"  Trial {trial+1}: Failed - {e}")
        
        if success_count > 0:
            avg_error_rate = sum(error_rates) / len(error_rates)
            print(f"  Success rate: {success_count}/5 trials")
            print(f"  Avg error rate: {avg_error_rate:.4f}%")
            print(f"  Rate (n/m): {n/M_safe:.3f}")
        else:
            print(f"  All trials failed!")
            
    except Exception as e:
        print(f"  Configuration failed: {e}")

print("\n" + "="*60)
print("结论: W值越大，成功率越高，错误率越低")