# -*- coding: utf-8 -*-

from heapq import heappush, heappop


def hsortStream(stream, maxHeapSize, key=None):
    """
        stream: a generator or iterable
        maxHeapSize: int, maximum size of heap
        key: a key function, as in `list.sort` method, or `sorted` function
    """
    hp = []
    if key:
        for index, item in enumerate(stream):
            if len(hp) >= maxHeapSize:
                yield heappop(hp)[-1]
            heappush(hp, (
                key(item),
                index,
                item,
            ))
        while hp:
            yield heappop(hp)[-1]
    else:
        for item in stream:
            if len(hp) >= maxHeapSize:
                yield heappop(hp)
            heappush(hp, item)
        while hp:
            yield heappop(hp)




def stdinIntegerStream():
    while True:
        line = raw_input(' Input item: ')
        if not line:
            break
        yield int(line)


def main():
    stream = stdinIntegerStream()
    for line in hsortStream(stream, 3):
        print('------ Placed item: %s'%line)

if __name__=='__main__':
    main()


