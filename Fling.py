# test_multiprocessing.py
import multiprocessing
import time

def process_one():
    print("Process One started")
    time.sleep(5)
    print("Process One finished")

def process_two():
    print("Process Two started")
    time.sleep(5)
    print("Process Two finished")

if __name__ == "__main__":
    multiprocessing.set_start_method('spawn')  # Ensure proper start method on all platforms
    p1 = multiprocessing.Process(target=process_one)
    p2 = multiprocessing.Process(target=process_two)

    p1.start()
    p2.start()

    p1.join()
    p2.join()

    print("Both processes finished.")
