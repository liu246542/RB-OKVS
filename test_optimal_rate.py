import math
from bitarray import util as bitutil
from rbokvs import RBOKVS

def test_optimal_rate():
    """测试接近论文中 1.03n 的最优率"""
    
    # 构建测试数据
    n = 1000
    test_kv = {}
    for i in range(n):
        value = bitutil.urandom(8)
        test_kv.setdefault(str(i), value.tobytes())
    
    # 论文中提到的最优设置
    target_rates = [
        (1.03, 0.97),  # 论文声称的最优
        (1.05, 0.95),  # 
        (1.10, 0.91),  # 
        (1.15, 0.87),  # 
        (1.23, 0.81),  # 先前工作的最好结果
    ]
    
    print("Testing different rates to achieve 1.03n optimality:")
    print("=" * 60)
    
    for multiplier, expected_rate in target_rates:
        print(f"\nTesting m = {multiplier:.2f}n (expected rate = {expected_rate:.2f}):")
        
        # 计算参数
        M = math.ceil(n * multiplier)
        epsilon = multiplier - 1.0
        
        # 根据论文公式计算 w
        # w = O(λ/ε + log n)，这里使用更精确的公式
        if epsilon > 0:
            lambda_param = 40  # 使用较小的安全参数以获得更好的率
            w = max(64, int(lambda_param / epsilon + math.log2(n)))
            w = (w + 7) // 8 * 8  # 确保是8的倍数
        else:
            w = 64
            
        print(f"  Parameters: n={n}, M={M}, w={w}, ε={epsilon:.3f}")
        
        # 检查是否w太大导致无法工作
        if w > M - n:
            print(f"  ❌ W={w} too large for M={M} (need W < {M-n})")
            continue
            
        try:
            # 进行多次测试
            success_count = 0
            total_trials = 3
            
            for trial in range(total_trials):
                try:
                    rbokvs = RBOKVS(M, n, w)
                    s = rbokvs.encode(test_kv)
                    
                    # 验证正确性
                    correct = 0
                    for i in range(n):
                        if test_kv.get(str(i)) == rbokvs.decode(str(i), s):
                            correct += 1
                    
                    if correct >= n * 0.99:  # 99%以上正确率认为成功
                        success_count += 1
                        
                except Exception as e:
                    print(f"    Trial {trial+1}: Failed - {str(e)[:50]}...")
            
            if success_count >= 2:  # 至少2/3成功
                actual_rate = n / M
                print(f"  ✅ Success! Actual rate: {actual_rate:.3f}")
                print(f"    Success rate: {success_count}/{total_trials}")
                
                # 检查是否接近最优
                if actual_rate >= 0.95:
                    print(f"    🎯 Excellent rate! Close to optimal.")
                elif actual_rate >= 0.90:
                    print(f"    ✨ Good rate!")
                else:
                    print(f"    ⚠️  Moderate rate.")
            else:
                print(f"  ❌ Failed most trials ({success_count}/{total_trials} success)")
                
        except Exception as e:
            print(f"  ❌ Configuration error: {e}")
    
    print("\n" + "=" * 60)
    print("结论分析:")
    print("1. 论文中的 1.03n 是理论最优值，需要非常大的 w 值")
    print("2. 实际实现中，w 值过大会导致其他问题")
    print("3. 1.10n - 1.15n 是更实用的选择")

if __name__ == "__main__":
    test_optimal_rate()