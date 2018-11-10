import os
import threading
import time


def interruptible_sleep(event, delay, interval=0.1):
    if delay <= interval:
        time.sleep(delay)
    else:
        start = time.time()
        while not event.is_set():
            time.sleep(min(interval, delay - (time.time() - start)))
            if time.time() - start >= delay:
                break


class LED(object):
    LEDS_PATH = '/sys/class/leds'

    def __init__(self, name):
        self._orig_trigger = None
        self._pattern_stack = []
        self.name = name

        if self.name is None:
            self.triggers = ['none']
            self._trigger = 'none'
        else:
            with open(self._f('trigger'), 'r') as fp:
                self.triggers = list(fp.read().split(' '))
                for idx, tname in enumerate(self.triggers):
                    if tname.startswith('['):
                        tname = tname[1:-1]
                        self._trigger = tname
                        self.triggers[idx] = tname

    def _f(self, fname):
        return os.path.join(self.LEDS_PATH, self.name, fname)

    @property
    def trigger(self):
        return self._trigger

    @trigger.setter
    def trigger(self, value):
        if self.name is None:
            return

        with open(self._f('trigger'), 'w') as fp:
            fp.write(value)
            self._trigger = value

    @property
    def max_brightness(self):
        if self.name is None:
            return 1

        with open(self._f('max_brightness'), 'r') as fp:
            return int(fp.read().strip())

    @property
    def brightness(self):
        if self.name is None:
            return 0

        with open(self._f('brightness'), 'r') as fp:
            return int(fp.read().strip())

    @brightness.setter
    def brightness(self, value):
        if self.name is None:
            return

        with open(self._f('brightness'), 'w') as fp:
            fp.write(str(value))

    def __enter__(self):
        self._orig_trigger = self.trigger
        self.trigger = 'none'
        self.off()
        return self

    def __exit__(self, type_, value, traceback):
        self.trigger = self._orig_trigger
        self._orig_trigger = None

    def on(self, brightness=None):
        self.brightness = int((brightness or 1.0) * self.max_brightness)

    def off(self):
        self.brightness = 0


class Pattern(threading.Thread):
    def __init__(self, led):
        self.led = led
        self.run_event = threading.Event()
        self.run_event.set()
        self.stop_event = threading.Event()
        super().__init__()

    def run(self):
        raise NotImplementedError()

    def suspend(self):
        self.run_event.clear()

    def unsuspend(self):
        self.run_event.set()

    def stop(self):
        if not self.run_event.is_set():
            self.run_event.set()
        self.stop_event.set()
        self.join()
        self.stop_event.clear()

    def __enter__(self):
        if self.led._pattern_stack:
            self.led._pattern_stack[-1].suspend()
        self.led._pattern_stack.append(self)
        self.start()
        return self

    def __exit__(self, type_, value, traceback):
        self.stop()
        self.led._pattern_stack.pop()
        if self.led._pattern_stack:
            self.led._pattern_stack[-1].unsuspend()


class Blink(Pattern):
    def __init__(self, led, on_time, off_time=None, brightness=None):
        self.on_time = on_time
        self.off_time = off_time or on_time
        self.brightness = brightness
        super().__init__(led)

    def run(self):
        while not self.stop_event.is_set():
            self.run_event.wait()
            self.led.on(self.brightness)
            interruptible_sleep(self.stop_event, self.on_time)
            self.led.off()
            interruptible_sleep(self.stop_event, self.off_time)


class ExtBlink(Pattern):
    def __init__(self, led, on_time, off_time=None, on_count=None, cycle_time=None, brightness=None):
        self.on_time = on_time
        self.off_time = off_time or on_time
        self.on_count = on_count or 1
        self.cycle_time = cycle_time or (self.on_time + self.off_time)
        self.brightness = brightness
        super().__init__(led)

    def run(self):
        while not self.stop_event.is_set():
            self.run_event.wait()
            start = time.time()
            for _ in range(self.on_count):
                self.led.on(self.brightness)
                interruptible_sleep(self.stop_event, self.on_time)
                self.led.off()
                interruptible_sleep(self.stop_event, self.off_time)
            delay = self.cycle_time - (time.time() - start)
            if delay > 0:
                interruptible_sleep(self.stop_event, delay)


if __name__ == '__main__':
    with LED('input3::capslock') as led:
        with Blink(led, 1):
            time.sleep(5)
            with ExtBlink(led, 0.1, on_count=3, cycle_time=1):
                time.sleep(5)
            time.sleep(3)
