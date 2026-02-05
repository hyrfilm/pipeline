# p >> i >> p >> e >> l >> i >> n >> e
emulating elixir's pipeline operator in python

this project is dedicated to my wonderful whiskey mentor 💕 tomie 💕

- `Pipe`: single value in, single value out
- `PipeStream`: stream processing with optional fan-out via `spread(...)`

## Examples

### 1) Basic `Pipe`

```python
from pipe import Pipe

result = (
    Pipe("hello")
    >> str.upper
    >> (lambda s: s[::-1])
)()

print(result)  # OLLEH
```

### 2) `Pipe` reusable with different input

```python
from pipe import Pipe

p = Pipe() >> str.strip >> str.upper

print(p("  hi  "))
print(p(" world "))
```

### 3) `PipeStream` with fan-out (`spread`)

```python
from pipe import PipeStream, spread

def words(text):
    return text.split()

stream = (
    PipeStream("hello world")
    >> spread(words)
    >> str.upper
)

print(list(stream()))  # ['HELLO', 'WORLD']
```

### 4) Filtering with `keep`

```python
from pipe import PipeStream, keep

stream = PipeStream(range(10)) >> keep(lambda n: n % 2 == 0)

print(list(stream()))  # [0, 2, 4, 6, 8]
```

### 5) Side effects with `tap`

```python
from pipe import PipeStream, tap

stream = PipeStream([1, 2, 3]) >> tap(print) >> (lambda n: n * 10)

print(list(stream()))
```

### 6) Lift a `Pipe` into `PipeStream`

```python
from pipe import Pipe, PipeStream

base = Pipe() >> str.upper >> (lambda s: s[::-1])
stream = PipeStream.from_pipe(base, ["cat", "dog"])

print(list(stream))  # ['TAC', 'GOD']
```
