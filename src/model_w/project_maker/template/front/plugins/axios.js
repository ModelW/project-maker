/**
 * Configure CSRF tokens to be automatically sent on each request
 */

export default function ({ $axios, redirect, $config: { API_URL } }) {
    $axios.onRequest((config) => {
        Object.assign(config, {
            xsrfCookieName: "csrftoken",
            xsrfHeaderName: "X-CSRFToken",
            progress: false,
        });
    });

    $axios.onError((error) => {
        const code = parseInt(error.response && error.response.status);
        if (code === 400) {
            redirect("/400");
        }
    });
}
