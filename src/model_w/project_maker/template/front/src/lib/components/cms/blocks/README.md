# All blocks for the CMS site

Add all blocks here with the same name (case-sensitve) as Wagtail's block.type. This way, it's easier to track which front component belongs to which back model. Furthermore, it makes it easier to do automatic import of blocks, should you wish to do so.

## Example

Given the following `DemoBlock` type which uses a DemoBlock model.

```python
    demo_blocks = wagtail_fields.StreamField(
        [
            (
                "DemoBlock",
                DemoBlock(),
            ),
        ],
    )
```

A front component called `DemoBlock` should be created in [$lib/components/cms/blocks/](./).
