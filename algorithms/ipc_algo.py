"""algorithms/ipc_algo.py - Pure Inter-Process Communication mechanisms (no GUI).

Three classic IPC primitives implemented as plain Python objects so they stay
unit-testable and free of any Tkinter dependency:

  * SharedMemory - a fixed-size buffer that several "processes" share. Whatever
    one writer stores, every reader sees, because they share one address space.
  * MessageQueue - asynchronous FIFO message passing. Producers send(), the
    queue holds messages, consumers receive() them in order.
  * Pipe         - a unidirectional stream. Bytes/chars flow in one end and out
    the other; reading *consumes* the data (stream, not random access).

Keeping the logic here lets apps/ipc.py be a thin GUI over these classes.
"""


class SharedMemory:
    """A fixed-size shared buffer (a list of slots).

    Models a region of memory mapped into several processes. Because every
    process indexes the *same* underlying list, a value written by one is
    immediately visible to all others - that is the whole point of shared
    memory: communication through a common address space, no copying.
    """

    def __init__(self, size=8):
        """Create ``size`` empty slots (each initialised to None)."""
        if size <= 0:
            raise ValueError("Shared memory size must be a positive integer.")
        self.size = size
        self._slots = [None] * size

    def write(self, index, value):
        """Store ``value`` in slot ``index`` (the 'writer process')."""
        self._check(index)
        self._slots[index] = value

    def read(self, index):
        """Return the value in slot ``index`` (the 'reader process')."""
        self._check(index)
        return self._slots[index]

    def dump(self):
        """Return a copy of all slots (snapshot for display/inspection)."""
        return list(self._slots)

    def _check(self, index):
        """Validate that ``index`` is a legal slot number."""
        if not isinstance(index, int) or not (0 <= index < self.size):
            raise IndexError(
                f"Slot {index} out of range 0..{self.size - 1}.")


class MessageQueue:
    """FIFO message passing between processes.

    Producers append messages with send(); consumers pull the oldest message
    with receive(). Messages are copied by value into the queue, so unlike
    shared memory the parties never touch the same object - they only exchange
    discrete messages. An optional ``capacity`` bounds the queue.
    """

    def __init__(self, capacity=None):
        """Create an empty queue. ``capacity`` None means unbounded."""
        if capacity is not None and capacity <= 0:
            raise ValueError("Capacity must be a positive integer or None.")
        self.capacity = capacity
        self._queue = []

    def send(self, msg):
        """Append ``msg`` to the back of the queue (producer)."""
        if self.capacity is not None and len(self._queue) >= self.capacity:
            raise OverflowError("Message queue is full.")
        self._queue.append(msg)

    def receive(self):
        """Pop and return the oldest message, or None if the queue is empty."""
        if not self._queue:
            return None
        return self._queue.pop(0)

    def peek(self):
        """Return a copy of the current queue contents without consuming."""
        return list(self._queue)

    def is_empty(self):
        """Return True when no messages are waiting."""
        return not self._queue


class Pipe:
    """A unidirectional character/byte stream.

    Data written with write() is appended to an internal buffer; read()
    consumes items from the *front*, so once read they are gone. This models
    the stream semantics of an OS pipe: bytes flow one direction and are
    delivered in order, exactly once.
    """

    def __init__(self):
        """Create an empty pipe buffer."""
        self._buffer = []

    def write(self, data):
        """Append the characters of ``data`` to the pipe (writer end)."""
        self._buffer.extend(str(data))

    def read(self, n=None):
        """Consume and return ``n`` items from the front as a string.

        With ``n`` None (the default) the whole buffer is drained. Reading
        removes the data, demonstrating that a pipe is consumed on read.
        """
        if n is None or n >= len(self._buffer):
            data = self._buffer
            self._buffer = []
        else:
            if n < 0:
                raise ValueError("Cannot read a negative number of items.")
            data = self._buffer[:n]
            self._buffer = self._buffer[n:]
        return "".join(data)

    def available(self):
        """Return the number of items still waiting in the pipe."""
        return len(self._buffer)
