#!/usr/bin/python3

import hashlib
import math

from bitarray import bitarray
from bitarray import util as bitutil


def hash_to_fixsize(bytesize, content):
    # constrain the output's size (as =bytesize)
    if not isinstance(content, bytes):
        content = bytes(content, "utf-8")
    if bytesize > 64:
        for_count = math.ceil(bytesize / 64)
        result_list = []
        last_length = bytesize
        for i in range(for_count):
            if i == for_count - 1:
                result_list.append(hash_to_fixsize(last_length, content))
            else:
                result_list.append(hash_to_fixsize(64, content))
                last_length -= 64
        return b"".join(result_list)
    hash_obj = hashlib.blake2b(digest_size=bytesize)
    hash_obj.update(content)
    return hash_obj.digest()


def bxor(b1, b2):
    if b1 == 0:
        return b2
    assert len(b1) == len(b2)
    return bytes(x ^ y for x, y in zip(b1, b2))


def bip(b1, b2):
    # compute inner product
    assert isinstance(b1, bitarray)
    assert isinstance(b2, list)
    assert len(b1) == len(b2)
    result = 0
    for i, b in enumerate(b1):
        if b == 1 and b2[i] != 0:
            result = bxor(result, b2[i])
    return result


class RBOKVS(object):
    """docstring for OKVS
    :n: rows
    :m: columns
    :w: length of band
    The choice of parameters:
    m = (1 + epsilon)n
    w = O(lambda / epsilon + log n)
    For example:
    m = 2^10, epsilon = 0.1,
    ==> n = (1+0.1) * 2^10
    ==> w = (lambda + 19.830) / 0.2751
    """

    def __init__(self, M, N, W):
        assert W % 8 == 0, "W must be divisible by 8"
        assert M >= N, "M must be at least N"
        assert W > 0, "W must be positive"

        # Parameter validation based on paper requirements
        epsilon = (M - N) / N if N > 0 else 0
        if epsilon > 0:
            min_w = max(64, int(128 / epsilon + 10))  # λ/ε + log(n), with λ=128
            if W < min_w:
                print(f"Warning: W={W} may be too small. Recommended W >= {min_w}")

        self.M = M
        self.N = N
        self.W = W

    def __hash1__(self, key):
        """
        hash a key to a specific position
        h_1(key) -> [0, M - W]
        """
        hash_range = self.M - self.W + 1
        pos_bin = hash_to_fixsize(64, key)
        pos_convert = int.from_bytes(pos_bin, byteorder="big") % hash_range
        return pos_convert

    def __hash2__(self, key):
        hash_bytes = hash_to_fixsize(int(self.W / 8), key)
        band = bitarray()
        band.frombytes(hash_bytes)
        return band

    def calcu_coding(self, key):
        start_pos = self.__hash1__(key)
        band = self.__hash2__(key)
        rest_pos = self.M - self.W - start_pos

        # Handle edge cases where rest_pos might be negative
        if rest_pos < 0:
            rest_pos = 0

        result = bitutil.zeros(start_pos) + band + bitutil.zeros(rest_pos)
        return (start_pos, result)

    def encode(self, kv_store):
        """
        :kv_store: dict
        """
        assert len(kv_store) == self.N
        pos_dic = {}  # 记录每一个 key 映射的起始位置
        key_encode = {}  # 记录每一个 key 映射的向量
        for k in kv_store.keys():
            start_pos, trans_conding = self.calcu_coding(k)
            pos_dic.setdefault(k, start_pos)
            key_encode.setdefault(k, trans_conding)

        sorted_pos = dict(sorted(pos_dic.items(), key=lambda item: item[1]))
        start_list = [x for x in sorted_pos.values()]
        b = [kv_store.get(k) for k in sorted_pos.keys()]
        sorted_coding = [key_encode.get(k) for k in sorted_pos.keys()]

        piv = [0] * self.N
        for i in range(self.N):
            # Find leftmost 1 in current row (pivot)
            pivot_found = False
            for j in range(start_list[i], start_list[i] + self.W):
                if j < self.M and sorted_coding[i][j] == 1:
                    piv[i] = j
                    pivot_found = True

                    # Eliminate this column in subsequent rows
                    for i_p in range(i + 1, self.N):
                        # Check if row i_p's band overlaps with pivot column j
                        if (start_list[i_p] <= j < start_list[i_p] + self.W and
                            sorted_coding[i_p][j] == 1):
                            sorted_coding[i_p] ^= sorted_coding[i]
                            b[i_p] = bxor(b[i_p], b[i])
                    break

            if not pivot_found:
                # Matrix is not solvable, return random encoding as per paper
                from bitarray import util as bitutil
                random_z = []
                for _ in range(self.M):
                    random_bytes = bitutil.urandom(len(list(kv_store.values())[0]))
                    random_z.append(random_bytes.tobytes())
                return random_z
        # Back substitution
        z = [0] * self.M
        for i in range(self.N - 1, -1, -1):
            if piv[i] > 0:  # Valid pivot
                # Compute z[piv[i]] = b[i] XOR (inner product of row i with current z)
                inner_prod = bip(sorted_coding[i], z)
                z[piv[i]] = bxor(inner_prod, b[i])
        return z

    def decode(self, k, z):
        _, trans_conding = self.calcu_coding(k)
        return bip(trans_conding, z)
