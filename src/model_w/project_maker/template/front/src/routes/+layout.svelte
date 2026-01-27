<slot />

<footer>
    <hr />
    <a href="/">Home page</a>
    # :: IF api__testing
    <a href="/demo/">Demo page</a>
    # :: ENDIF
    <a href="/non-cms">Non-CMS</a>
</footer>

<style lang="scss">
    :global(h1) {
        color: red;
    }
</style>
