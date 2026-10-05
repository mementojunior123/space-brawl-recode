from typing import Callable, Generator, Any

class SentinelClass:
    ...

_MISSING : SentinelClass = SentinelClass()

type CoroutineFunction[T1, T2] = Callable[..., Generator[T2, T1|SentinelClass, T2]]



class CoroutineScript[T1, T2]:
    def __init__(self, coroutine : CoroutineFunction|None = None):
        self.initialized : bool = False
        self.is_over : bool = False
        self.coro_func : CoroutineFunction[T1, T2] = coroutine or self.corou
        self.coroutine : Generator[T2, T1|SentinelClass, T2]
        self.coro_attributes : list[str] = []
    
    def initialize(self, *args, **kwargs):
        self.coroutine = self.coro_func(*args, **kwargs)
        next(self.coroutine)
        self.initialized = True

    def process_frame(self, values : T1|SentinelClass = _MISSING) -> T2|None:
        if self.is_over : return None
        if not self.initialized: self.initialize()
        try:
            return self.coroutine.send(values)
        except StopIteration as e:
            self.is_over = True
            return e.value
    
    @staticmethod
    def corou(*args, **kwargs) -> Generator[T2, T1|SentinelClass, T2]:
        raise NotImplementedError
