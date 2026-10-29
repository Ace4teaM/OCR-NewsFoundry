/**
 * Fonction utile pour poster des données et recevoir une réponse JSON
 */
export async function postApi(url, post, domain = process.env.NEXT_PUBLIC_API_URL) {
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

    if (!response.ok)
    {
        const errorData = await response.json().catch(() => null);

        throw new Error(
            errorData?.message ?? `Erreur HTTP ${response.status}`
        );
    }

    return response.json()
}

/**
 * Fonction utile pour obtenir des données dans une réponse JSON
 */
export async function fetchApi(url, domain = process.env.NEXT_PUBLIC_API_URL) {
    const response = await fetch(`${domain}/${url}`, 
        {
            method: "GET",
            headers: {
                "Content-Type" : "application/json"
            },
            credentials: "include"
        }
    );

    if (!response.ok)
    {
        const errorData = await response.json().catch(() => null);

        throw new Error(
            errorData?.message ?? `Erreur HTTP ${response.status}`
        );
    }

    return response.json()
}
