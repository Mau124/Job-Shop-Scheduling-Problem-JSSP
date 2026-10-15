# A* complete execution trace example

We now run the two-job example with `"h2"`.

Let `S0`, `S1`, and so on denote states by their insertion-counter values.

Whenever a queue order is shown below, it is the **logical removal order**, not necessarily the underlying heap list's physical arrangement.

### Initial state: `S0`

```python
indexes = [0, 0]
time = [0, 0]
job_time = [0, 0]
schedule = [[], []]
```

Heuristic calculation:

```text
makespan = 0

Job 0 optimistic finish = 0 + 3 + 2 = 5
Job 1 optimistic finish = 0 + 2 + 4 = 6
job_bound = 6

machine_bound = [
    0 + 3 + 4,  # Machine 0
    0 + 2 + 2,  # Machine 1
] = [7, 4]

bound = max(0, 6, 7) = 7
h = 7 - 0 = 7
f = 0 + 7 = 7
```

### Pop `S0`: create `S1` and `S2`

**Choose job 0.**

```python
machine = 0
start = max(0, 0) = 0
end = 0 + 3 = 3
```

Create `S1`:

```python
indexes = [1, 0]
time = [3, 0]
job_time = [3, 0]
schedule = [[(0, 0, 3)], []]
```

Its job bound is still `6`, and its machine-bound vector is `[7, 4]`.

```text
g = 3
bound = 7
h = 4
f = 7
```

**Choose job 1 from the original `S0`.**

```python
machine = 1
start = max(0, 0) = 0
end = 0 + 2 = 2
```

Create `S2`:

```python
indexes = [0, 1]
time = [0, 2]
job_time = [0, 2]
schedule = [[], [(1, 0, 2)]]
```

Its priority is also `7`.

Queue order:

```text
S1(f=7), S2(f=7)
```

`S1` comes first because it was inserted first.

### Pop `S1`: create `S3` and `S4`

From `S1`, choosing job 0 again schedules its second operation:

```text
Machine 1
start = max(0, 3) = 3
end = 3 + 2 = 5
```

This creates `S3`, where job 0 is completely scheduled and job 1 has not started.

Its machine bounds are `[7, 7]`, so its priority remains `7`.

Alternatively, choosing job 1 places its first operation on machine 1:

```text
start = max(0, 0) = 0
end = 2
```

This creates `S4`:

```python
indexes = [1, 1]
time = [3, 2]
job_time = [3, 2]
```

Notice that this operation starts at time `0`, even though job 0's operation had already been placed through time `3`.

Queue order:

```text
S2(f=7), S3(f=7), S4(f=7)
```

### Pop `S2`: skip one duplicate and create `S5`

Choosing job 0 produces:

```python
indexes = [1, 1]
time = [3, 2]
job_time = [3, 2]
```

That is exactly the key for `S4`.

The solver skips it, even though `S4` has not yet been expanded.

Choosing job 1 again places its second operation on machine 0:

```text
start = max(0, 2) = 2
end = 2 + 4 = 6
```

This creates `S5`.

Machine 0 now has tail `6` and still needs job 0's three-unit operation:

```text
machine_bound[0] = 6 + 3 = 9
```

Thus `S5` has:

```text
g = 6
h = 3
f = 9
```

Queue order:

```text
S3(f=7), S4(f=7), S5(f=9)
```

### Pop `S3`: skip finished job 0 and create `S6`

Job 0 is finished, so it is skipped.

Job 1's first operation needs machine 1, whose tail is already `5`:

```text
start = max(5, 0) = 5
end = 5 + 2 = 7
```

This creates `S6`.

Job 1 still needs four units on machine 0:

```text
job 1 optimistic finish = 7 + 4 = 11
```

So:

```text
g = 7
h = 4
f = 11
```

**This illustrates the append-only restriction.** Machine 1 had an earlier idle interval from `0` to `3`, but this branch cannot insert job 1 there after its tail has reached `5`.

Queue order:

```text
S4(f=7), S5(f=9), S6(f=11)
```

### Pop `S4`: create `S7` and `S8`

Recall:

```python
indexes = [1, 1]
time = [3, 2]
job_time = [3, 2]
```

Choosing job 0 places its machine-1 operation at:

```text
start = max(2, 3) = 3
end = 5
```

This creates `S7`:

```text
g = 5
job_bound = 6
machine_bound = [7, 5]
h = 2
f = 7
```

Choosing job 1 instead places its machine-0 operation at:

```text
start = max(3, 2) = 3
end = 7
```

This creates `S8`:

```python
indexes = [1, 2]
time = [7, 2]
job_time = [3, 7]
```

Its calculation is:

```text
g = 7
job_bound = 7
machine_bound = [7, 4]
bound = 7
h = 0
f = 7
```

**`S8` is not complete, despite `h == 0`.**

Job 0 still has an operation left, but that operation can fit before time `7`. No additional makespan is necessary.

Queue order:

```text
S7(f=7), S8(f=7), S5(f=9), S6(f=11)
```

### Pop `S7`: create complete state `S9`

Job 0 is finished.

Job 1's final operation is placed on machine 0:

```text
start = max(3, 2) = 3
end = 3 + 4 = 7
```

Create `S9`:

```python
indexes = [2, 2]
time = [7, 5]
job_time = [5, 7]
```

All work is scheduled, so:

```text
g = 7
h = 0
f = 7
```

But the solver does not stop on generation.

Queue order:

```text
S8(f=7), S9(f=7), S5(f=9), S6(f=11)
```

### Pop `S8`: skip a duplicate goal

Job 0's remaining operation runs on machine 1:

```text
start = max(2, 3) = 3
end = 5
```

The resulting state matches `S9`, so it is skipped.

Job 1 is already finished.

Queue order:

```text
S9(f=7), S5(f=9), S6(f=11)
```

### Pop `S9`: save and return

Now:

```python
sum(indexes) == 2 + 2 == 4
```

The solver saves:

```python
self.min_time = 7

self.schedule_response = [
    [
        (0, 0, 3),
        (1, 3, 7),
    ],
    [
        (1, 0, 2),
        (0, 3, 5),
    ],
]
```

In plain language:

| Machine | Schedule |
|---|---|
| Machine 0 | Job 0 from `0–3`, then job 1 from `3–7`. |
| Machine 1 | Job 1 from `0–2`, idle from `2–3`, then job 0 from `3–5`. |

The final makespan is:

```python
max(7, 5) == 7
```

### Complete state ledger

| State | `indexes` | `time` | `job_time` | `g` | `h` | `f` |
|---|---|---|---|---:|---:|---:|
| S0 | `[0, 0]` | `[0, 0]` | `[0, 0]` | 0 | 7 | 7 |
| S1 | `[1, 0]` | `[3, 0]` | `[3, 0]` | 3 | 4 | 7 |
| S2 | `[0, 1]` | `[0, 2]` | `[0, 2]` | 2 | 5 | 7 |
| S3 | `[2, 0]` | `[3, 5]` | `[5, 0]` | 5 | 2 | 7 |
| S4 | `[1, 1]` | `[3, 2]` | `[3, 2]` | 3 | 4 | 7 |
| S5 | `[0, 2]` | `[6, 2]` | `[0, 6]` | 6 | 3 | 9 |
| S6 | `[2, 1]` | `[3, 7]` | `[5, 7]` | 7 | 4 | 11 |
| S7 | `[2, 1]` | `[3, 5]` | `[5, 2]` | 5 | 2 | 7 |
| S8 | `[1, 2]` | `[7, 2]` | `[3, 7]` | 7 | 0 | 7 |
| S9 | `[2, 2]` | `[7, 5]` | `[5, 7]` | 7 | 0 | 7 |

`S5` and `S6` remain unexpanded when the solver returns. Their `f` values are bounds, not necessarily the makespans their eventual completions would achieve.
