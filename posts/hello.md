[category]: <> (General)
[date]: <> (2026/06/16)
[title]: <> (Hello from elrakabawi.sol)

This is the first pass of a deliberately small blog.

The whole site is generated from Markdown into plain HTML, which keeps the writing workflow simple and the output easy to host anywhere. For a normal browser URL, the canonical address is `elrakabawi.sol.site`. In Brave and other SNS-aware surfaces, the same site can resolve from `elrakabawi.sol`.

Here's the shape of the publishing loop:

```python
def publish():
    return "write -> build -> upload"
```
