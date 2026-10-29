
import { parseResponseAPI, Result } from "@/utils/result";

/**
 * Fonction utile pour poster des données et recevoir une réponse JSON
 */
export async function postApi(url, post, domain = process.env.NEXT_PUBLIC_API_URL, handleResponse = parseResponseAPI) {
    const response = await fetch(`${domain}/${url}`, 
        {
            method: "POST",
            headers: {
                "Content-Type" : "application/json"
            },
            body: JSON.stringify(post),
            credentials: "include"
        }
    );

    const result = await handleResponse(response)

    return result
}

/**
 * Fonction utile pour obtenir des données dans une réponse JSON
 */
export async function fetchApi(url, domain = process.env.NEXT_PUBLIC_API_URL, handleResponse = parseResponseAPI) {
    const response = await fetch(`${domain}/${url}`, 
        {
            method: "GET",
            headers: {
                "Content-Type" : "application/json"
            },
            credentials: "include"
        }
    );

    const result = await handleResponse(response)

    return result
}
