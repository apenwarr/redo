import time
t2 = int(time.time()) + 1.0
while 1:
    t = time.time()
    if t >= t2: break
    time.sleep(t2 - t + 0.01)
