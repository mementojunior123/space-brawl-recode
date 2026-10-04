"""Module that contains multiple lerp related utility functions."""
from typing import Callable, TypeAlias, Literal, Any, TypeVar
EasingFunc : TypeAlias = Callable[[float], float]
def compatibilty_lerp(a, b, t : float) -> Any:
    try: return a + (b-a) * t 
    except: pass
        
    try : return a.lerp(b, t) 
    except: pass
        
    try: size_a, size_b = len(a), len(b)
    except: raise ValueError("Compatibilty checks failed")
    else: 
        if size_a != size_b: raise ValueError("Size mismatch")
        
    try: return [a[i] + (b[i] - a[i]) * t for i in range(size_a)] #type: ignore
    except: pass
        
    raise ValueError(f"Compatibilty checks failed ({a} does not match {b})")

T = TypeVar("T", bound=Any)
def lerp(a : T, b : T, t : float) -> T:
    return a + (b-a) * t
    
def flip(t : float) -> float:
    return 1 - t

def quad_ease_out(t : float) -> float:
    return 1 - (1 - t) * (1 - t)

def quad_ease_in(t : float) -> float:
    return t * t

def cubic_ease_in(t : float) -> float:
    return t * t * t

def cubic_ease_out(t : float) -> float:
    return flip(cubic_ease_in(flip(t)))

def smoothstep(t : float) -> float:
    return lerp(quad_ease_in(t), quad_ease_out(t), t)

def linear(t : float) -> float:
    return t

def mirror(t : float) -> float:
    if t < 0.5: return t * 2
    else: return flip(t) * 2

EasingStylesStr : TypeAlias = Literal['flip', 'quad_ease_out', 'quad_ease_in', 'cubic_ease_in', 'cubic_ease_out', 
                                      'smoothstep', 'linear', 'mirror']
EasingStylesList : list[EasingStylesStr] = ['flip', 'quad_ease_out', 'quad_ease_in', 'cubic_ease_in', 'cubic_ease_out', 
                                      'smoothstep', 'linear', 'mirror']
easing_style_dict : dict[EasingStylesStr, EasingFunc] = {
    'flip' : flip,
    'quad_ease_out' : quad_ease_out,
    'quad_ease_in' : quad_ease_in,
    'cubic_ease_in' : cubic_ease_in,
    'cubic_ease_out' : cubic_ease_out,
    'smoothstep' : smoothstep,
    'linear' : linear,
    'mirror' : mirror,
}
def get_easing_from_str(val : str) -> EasingFunc|None:
    if val not in easing_style_dict:
        return None
    return easing_style_dict[val]