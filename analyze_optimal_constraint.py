import math
from bitarray import util as bitutil
from rbokvs import RBOKVS

def analyze_theoretical_constraints():
    """分析理论最优值的约束条件"""
    
    n = 1000
    print("分析论文中 1.03n 最优率的理论约束:")
    print("=" * 50)
    
    # 不同的 epsilon 值
    epsilons = [0.03, 0.05, 0.10, 0.15, 0.20, 0.30]
    
    for epsilon in epsilons:
        M = math.ceil(n * (1 + epsilon))
        
        # 论文公式: w = O(λ/ε + log n)
        lambda_param = 40
        w_theoretical = int(lambda_param / epsilon + math.log2(n))
        w_practical = (w_theoretical + 7) // 8 * 8
        
        # 检查约束条件
        max_w_possible = M - n  # 最大可能的 w 值
        
        print(f"\nε = {epsilon:.3f} (rate = {n/M:.3f}):")
        print(f"  M = {M}, max possible W = {max_w_possible}")
        print(f"  Theoretical W = {w_theoretical}")
        print(f"  Practical W = {w_practical}")
        
        if w_practical <= max_w_possible:
            print(f"  ✅ 可行 (W <= {max_w_possible})")
            
            # 实际测试
            try:
                test_kv = {}
                for i in range(min(100, n)):  # 小规模测试
                    value = bitutil.urandom(8)
                    test_kv.setdefault(str(i), value.tobytes())
                
                rbokvs = RBOKVS(M, len(test_kv), w_practical)
                s = rbokvs.encode(test_kv)
                print(f"  ✅ 编码成功!")
                
            except Exception as e:
                print(f"  ❌ 编码失败: {str(e)[:30]}...")
        else:
            print(f"  ❌ 不可行 (W > {max_w_possible})")
            print(f"    需要 W 减少 {w_practical - max_w_possible}")
    
    print("\n" + "=" * 50)
    print("关键发现:")
    print("1. 论文的 1.03n 需要 ε=0.03，但对应的 W 值过大")
    print("2. 实际约束: W < M - N = ε·N")
    print("3. 理论需求: W = O(λ/ε + log N)")
    print("4. 当 ε 很小时，λ/ε 会变得很大，违反约束")
    
    # 找到平衡点
    print("\n寻找实际可行的最优点:")
    for epsilon in [0.10, 0.15, 0.20, 0.25, 0.30]:
        M = math.ceil(n * (1 + epsilon))
        max_w = M - n
        
        # 计算在约束下的最大安全参数
        max_lambda = (max_w - math.log2(n)) * epsilon
        
        print(f"ε = {epsilon:.2f}: rate = {n/M:.3f}, max λ = {max_lambda:.1f}")
        
        if max_lambda >= 40:  # 足够的安全参数
            print(f"  ✅ 推荐选择! (λ = {max_lambda:.1f} >= 40)")
        else:
            print(f"  ⚠️  安全参数较低 (λ = {max_lambda:.1f} < 40)")

if __name__ == "__main__":
    analyze_theoretical_constraints()