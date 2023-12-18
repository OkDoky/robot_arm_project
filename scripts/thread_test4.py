from threading import Thread, Event
import time

def simple_loop(num, event):
    while not event.is_set():
        print("simple loop is running")
        time.sleep(0.5)
    print("simple loop is done")

a = 0
simple_event = Event()
simple_thread = Thread(target=simple_loop, args=(a, simple_event,))
# simple_thread.daemon = True
simple_thread.start()
s1 = time.time()
while (time.time()-s1) < 1:
    print("main loop is running")
    time.sleep(0.3)
print("main loop is done")
time.sleep(1)
simple_event.set()