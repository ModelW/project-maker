Checks the memory usage of the container running the application and warns
when it gets too close to the limit.

## Logic

- Reads `psutil.virtual_memory()`.
- Raises a **warning** when the used memory percentage is greater than or
  equal to **90%**.

## Troubleshooting

High memory usage usually indicates:

1. **Memory leak**: a long-running process steadily accumulating memory.
2. **Under-provisioned container**: the application genuinely needs more RAM.

Short term, restart the container. Long term, either fix the leak or raise the
memory limit allocated to the container.
