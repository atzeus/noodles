from noodles import (schedule, run_parallel, gather)
import time
import numpy as np


@schedule
def delay(dt):
    time.sleep(dt)
    return dt


def measure(f, *args):
    start = time.time()
    ret = f(*args)
    end = time.time()
    return (ret, (end - start))


def constant_time(dt, n, n_threads=4):
    wf = schedule(sum)(
            gather(*(delay(dt) for i in range(n))))

    return measure(run_parallel, wf, n_threads)


#print("dt", "N", "tot", "elapsed", "err")
#for n in [2**k for k in range(3, 14)]:
#    data = np.array([constant_time(1/n, n, 4) for i in range(10)])
#    mean = data.mean(axis=0)
#    std = data.std(axis=0)
#    print("{0:8} {1:8} {2:8} {3:8} {4:8}".format(
#        1/n, n, mean[0], mean[1], std[1]))

print("\n\n")
for n in [2**k for k in range(5, 14)]:
    data = np.array([constant_time(1/n, 1000, 4) for i in range(10)])
    mean = data.mean(axis=0)
    std = data.std(axis=0)
    print("{0:8} {1:8} {2:8} {3:8} {4:8}".format(
        1/n, n, mean[0], mean[1], std[1]))
