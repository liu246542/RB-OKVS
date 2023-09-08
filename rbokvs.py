#!/usr/bin/python3

import math
import hashlib
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
    result = bytearray(b1)
    for i, b in enumerate(b2):
        result[i] ^= b
    return bytes(result)


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
        assert W % 8 == 0
        self.M = M
        self.N = N
        self.W = W

    def __hash1__(self, key):
        """
        hash a key to a specific position
        h_1(key) -> [0, M - W]
        """
        hash_range = self.M - self.W
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
            for j in range(start_list[i], start_list[i] + self.W):
                if sorted_coding[i][j] == 1:
                    piv[i] = j
                    for i_p in range(i + 1, self.N):
                        if start_list[i_p] <= piv[i]:
                            if sorted_coding[i_p][piv[i]] == 1:
                                sorted_coding[i_p] ^= sorted_coding[i]
                                b[i_p] = bxor(b[i_p], b[i])
                    break
            if piv[i] == 0:
                raise RuntimeError(f"Fail to initialize at {i}th row!")
        z = [0] * self.M
        for i in range(self.N - 1, -1, -1):
            z[piv[i]] = bxor(bip(sorted_coding[i], z), b[i])
        return z

    def decode(self, k, z):
        _, trans_conding = self.calcu_coding(k)
        return bip(trans_conding, z)
