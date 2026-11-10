export const API_URL = process.env.NEXT_PUBLIC_API_URL;

if (!API_URL) {
    console.error("NEXT_PUBLIC_API_URL n'est pas définie");
}
else {
    console.info("process.env OK");
}