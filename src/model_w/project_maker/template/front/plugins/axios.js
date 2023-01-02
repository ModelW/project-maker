/**
 * Configure CSRF tokens to be automatically taken in account
 */
export default function ({ $axios }) {
    $axios.onRequest((config) => {
        Object.assign(config, {
            xsrfCookieName: "csrftoken",
            xsrfHeaderName: "X-CSRFToken",
            progress: false,
        });
    });
}
