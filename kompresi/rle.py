import os

def rle_compress(filepath, outdir):
    with open(filepath, 'rb') as f:
        data = f.read()
    compressed = bytearray()
    i = 0
    while i < len(data):
        count = 1
        while i + 1 < len(data) and data[i] == data[i+1] and count < 255:
            count += 1
            i += 1
        compressed.append(count)
        compressed.append(data[i])
        i += 1
    outname = os.path.basename(filepath) + '.rle'
    outpath = os.path.join(outdir, outname)
    with open(outpath, 'wb') as f:
        f.write(compressed)
    return outpath 