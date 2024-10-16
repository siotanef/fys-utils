# python cebraspe.py <file>.txt i1 i2 ...

import sys

def main():
    filename = sys.argv[1]
    indices = [int(i) for i in sys.argv[2:]]
    with open(filename) as handle:
        text = ' '.join(line.strip() for line in handle.readlines())
    
    candidates = [
        [cell.strip() for cell in line.strip().split(',')]
        for line in text.split('/')
    ]
    candidates = [
        [
            c[1],
            *[float(c[i]) for i in indices],
            round(sum([float(c[i]) for i in indices]), 2),
        ] for c in candidates
    ]

    candidates = sorted(candidates, key=lambda x: -x[-1])
    for i, c in enumerate(candidates, 1):
        print(i, *c)
    return 0


if __name__ == '__main__':
    sys.exit(main())