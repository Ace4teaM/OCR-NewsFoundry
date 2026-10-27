
/**
 * Représente un objet de résultat utilisée par les mééthodes et requêtes de l'application
 * @param success {bool} - Indique si le traitement est un succès
 * @param data - Les données du résultat
 * @param error - Le message d'erreur si le traitement a échoué
 */
export class Result {
  constructor(success, data = null, error = null) {
    this.success = success;
    this.data = data;
    this.error = error;
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
    if (!response.ok && respData.detail)
    {
        return new Result(false, respData, respData.detail);
    }

    // La requête a réussie ?
    if (respData?.success == true)
    {
        return new Result(true, respData);
    }

    // La requête a réussie ?
    if (respData?.success == false)
    {
        return new Result(false, respData, respData?.message ?? "Erreur inconnue");
    }

    throw new Error("Réponse inattendue du serveur");
}
