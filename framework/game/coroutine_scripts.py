from typing import Callable, Generator, Any

CoroutineFunction = Callable[..., Generator]

class CoroutineScript:
    def __init__(self, coroutine : CoroutineFunction|None = None):
        self.initialized : bool = False
        self.is_over : bool = False
        self.coro_func : CoroutineFunction = coroutine or self.corou
        self.coroutine : Generator
        self.coro_attributes : list[str] = []
    
    def initialize(self, *args, **kwargs):
        self.coroutine = self.coro_func(*args, **kwargs)
        next(self.coroutine)
        self.initialized = True

    def process_frame(self, values = None):
        if self.is_over : return
        if not self.initialized: self.initialize()
        try:
            return self.coroutine.send(values)
        except StopIteration as e:
            self.is_over = True
            return e.value
    
    @staticmethod
    def corou(*args, **kwargs) -> Generator[Any, Any, Any]:
        raise NotImplementedError
