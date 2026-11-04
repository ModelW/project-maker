# All blocks for the CMS site

Add all blocks here with the same name (case-sensitive) as Wagtail's `block.type`. That's all
there is to do: the block registry (`getBlockComponents()` in `$lib/utils/cms.ts`) finds the
components by their file name, and the `StreamField` component renders them.

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

A front component called `DemoBlock.svelte` should be created in
[$lib/components/cms/blocks/](./). It receives the value of the block as `cmsData`:

```svelte
<script lang="ts">
    let { cmsData }: { cmsData: any } = $props();
</script>
```

And the page renders the StreamField with:

```svelte
<StreamField blocks={cmsData.demo_blocks} />
```

Blocks nested in a block (a `StreamBlock` or a `ListBlock` of blocks) are rendered the same way,
with another `<StreamField>` inside the block's component.
