# All pages for the CMS site

Add all pages here with the same name (case-sensitve) as Wagtail's page.type. This way, it's easier to track which front component belongs to which back model.

## Example

Given the following `DemoPage`.

```python
    class DemoPage(utils.ApiPage):
        ...
```

A front component called `DemoPage` should be created in [$lib/components/cms/pages/](./).
