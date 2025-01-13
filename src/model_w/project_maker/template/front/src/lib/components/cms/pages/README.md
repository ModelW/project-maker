# All blocks for the CMS site

Add all blocks here with the same name (case-sensitve) as Wagtail's block.type. This way, it's easier to track which front component belongs to which back model. Furthermore, it makes it easier to do automatic import of blocks, should you wish to do so.

## Example

Given the following `DemoPage`.

```python
    class DemoPage(utils.ApiPage):
        ...
```

A front component called `DemoPage` should be created in [$lib/components/cms/pages/](./).
