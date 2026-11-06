<script lang="ts">
    /**
     * Footer of the site: each group of the footer menu is a column, titled
     * by its label, with its links below. Footers only go one level deep.
     */
    import { useMenu } from "$lib/navigation/context";
    import { isMenuGroup } from "$lib/navigation/menus";

    const menu = useMenu("footer");
    const uid = $props.id();
</script>

<footer class="footer" data-testid="site footer">
    <nav class="container columns" aria-label="Footer">
        {#each menu.items as item, i (i)}
            <div class="column">
                {#if isMenuGroup(item)}
                    <h2 class="title" id="{uid}-{i}">{item.label}</h2>
                    <ul aria-labelledby="{uid}-{i}">
                        {#each item.children as child, j (j)}
                            {#if !isMenuGroup(child)}
                                <li><a href={child.href}>{child.label}</a></li>
                            {/if}
                        {/each}
                    </ul>
                {:else}
                    <a class="title" href={item.href}>{item.label}</a>
                {/if}
            </div>
        {/each}
    </nav>
</footer>

<style lang="scss">
    @use "$lib/styles/abstracts/mixins" as mixins;

    .footer {
        padding-block: 3rem;
        background: rgb(0 0 0 / 4%);
    }

    .columns {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(12rem, 1fr));
        gap: 2rem;
    }

    .title {
        margin: 0;
        font-size: 1rem;
        font-family: var(--font-heading);
        font-weight: 700;
        color: inherit;
        text-decoration: none;
    }

    ul {
        @include mixins.reset-list;

        margin-top: 0.75rem;
        display: grid;
        gap: 0.5rem;
    }

    a {
        color: inherit;
    }
</style>
