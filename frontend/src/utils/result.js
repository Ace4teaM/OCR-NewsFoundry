/**
 * Représente un objet de résultat utilisée par les mééthodes et requêtes de l'application
 * @param success {bool} - Indique si le traitement est un succès
 * @param data - Les données du résultat
 * @param message - Le message du résultat
 */
export class Result {
  constructor(success, data = null, message = null) {
    this.success = success;
    this.data = data;
    this.message = message;
  }

  isSuccess() {
    return this.success;
  }
}

/**
 * Transforme la réponse d'une requête API en un objet Result
 * @param response - Réponse de la requête HTTP
 * @returns {Result} - Objet Result représentant le succès ou l'échec de la requête
 */
export async function parseResponseAPI(response){

    // La réponse attendue est de type JSON
    const respData = await response.json().catch(() => null);
    if (!respData)
    {
        return new Result(false, null, "La réponse attendu par le serveur est invalide, veuillez reéssayer." );
    }

    // La requête a échouée ?
    if (!response.ok)
    {
        return new Result(false, response, respData?.detail);
    }

    // La demande a réussie ?
    if (respData?.success == true)
    {
        return new Result(true, respData?.data, respData?.message);
    }

    // La demande a échouée ?
    if (respData?.success == false)
    {
        return new Result(false, respData?.data, respData?.message ?? "Erreur inconnue");
    }

    console.error("Réponse inattendue du serveur", response, respData);
    throw new Error("Réponse inattendue du serveur");
}

/**
 * Transforme la réponse d'une requête API en un objet Result
 * @param response - Réponse de la requête HTTP
 * @param onMessage - Fonction de rappel pour traiter les messages intermédiaires du flux
 * @returns {Result} - Objet Result représentant le succès ou l'échec de la requête
 */
export async function parseStreamResponseAPI(response, onMessage) {

    // La requête a échoué ?
    if (!response.ok) {
        const respData = await response.json().catch(() => null);
        const result = new Result(false, response, respData?.detail );
        onMessage(result);
        return result;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    let buffer = "";
    let result = null;

    while (true) {

        const { done, value } = await reader.read();

        buffer += decoder.decode(value || new Uint8Array(), {
            stream: !done
        });

        const lines = buffer.split("\n");
        buffer = lines.pop();
        
        for (const line of lines) {

            if (!line.trim()) continue;

            result = JSON.parse(line);
            onMessage(result);
        }

        if (done) break;
    }

    if (buffer.trim()) {
        result = JSON.parse(buffer);
        onMessage(result);
    }

    return result;
}