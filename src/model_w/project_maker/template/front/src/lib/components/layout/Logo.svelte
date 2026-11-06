<script lang="ts">
    /**
     * Logo of the site, inlined so that it can follow the text color
     * (`currentColor`) and doesn't cost a request. Replace the SVG with the
     * actual logo.
     */
</script>

<svg class="logo" viewBox="0 0 48 48" aria-hidden="true" focusable="false">
    <rect x="1" y="1" width="46" height="46" rx="12" fill="currentColor" />
    <polyline
        points="10,14 17,34 24,20 31,34 38,14"
        fill="none"
        stroke="var(--logo-background, #fff)"
        stroke-width="4.5"
        stroke-linecap="round"
        stroke-linejoin="round"
    />
</svg>

<style lang="scss">
    .logo {
        display: block;
        width: 100%;
        height: 100%;
    }
</style>
