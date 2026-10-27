/**
 * Retourne le message correspondant à l'exception
 * @param err - Exception ou message
 */
export function parseErrorMessage(err) {  
    if (typeof(err) === "string") {
        return err
    } else if (err instanceof Error) {
        return err.message
    } else {
        return String(err)
    }
}

/**
 * Retourne le message correspondant à l'erreur API
 * @param data - Données de la réponse API
 */
export function parseAPIError(data){
    return data?.error ?? String(data)
}