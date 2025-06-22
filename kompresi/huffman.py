import os
import heapq
from collections import defaultdict

class Node:
    def __init__(self, freq, byte, left=None, right=None):
        self.freq = freq
        self.byte = byte
        self.left = left
        self.right = right
    def __lt__(self, other):
        return self.freq < other.freq

def build_tree(freqs):
    heap = [Node(freq, byte) for byte, freq in freqs.items()]
    heapq.heapify(heap)
    while len(heap) > 1:
        n1 = heapq.heappop(heap)
        n2 = heapq.heappop(heap)
        merged = Node(n1.freq + n2.freq, None, n1, n2)
        heapq.heappush(heap, merged)
    return heap[0] if heap else None

def build_codes(node, prefix='', codebook=None):
    if codebook is None:
        codebook = {}
    if node:
        if node.byte is not None:
            codebook[node.byte] = prefix
        build_codes(node.left, prefix + '0', codebook)
        build_codes(node.right, prefix + '1', codebook)
    return codebook

def huffman_compress(filepath, outdir):
    with open(filepath, 'rb') as f:
        data = f.read()
    freqs = defaultdict(int)
    for b in data:
        freqs[b] += 1
    tree = build_tree(freqs)
    codebook = build_codes(tree)
    encoded = ''.join(codebook[b] for b in data)
    # Pad encoded to byte
    pad_len = (8 - len(encoded) % 8) % 8
    encoded += '0' * pad_len
    barray = bytearray()
    for i in range(0, len(encoded), 8):
        barray.append(int(encoded[i:i+8], 2))
    outname = os.path.basename(filepath) + '.huff'
    outpath = os.path.join(outdir, outname)
    with open(outpath, 'wb') as f:
        f.write(bytes([pad_len]))
        f.write(barray)
    return outpath 