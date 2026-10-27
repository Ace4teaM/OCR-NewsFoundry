'use client'

import { useState, useMemo } from 'react'
import { parseErrorMessage, parseAPIError } from "@/utils/error";
 
export default function Delete(url, handleAPIError = parseAPIError) {
    const [data, setData] = useState({})
    const [isLoading, setLoading] = useState(false)
    const [error, setError] = useState(false)

    const hasData = useMemo(
        () => (isLoading == false && error == false && data && Object.keys(data).length > 0)
    ,[isLoading, error, data])

    async function send() {
        try {
            const response = await fetch(`${url}`, 
                {
                    method: "DELETE",
                    credentials: "include"
                }
            );

            // La réponse attendue est de type JSON
            const respData = await response.json().catch(() => null);
            if (!respData)
            {
                throw new Error( "La réponse attendu par le serveur est invalide, veuillez reéssayer." );
            }

            // La requête a échouée ?
            if (!response.ok)
            {
                throw new Error( handleAPIError(respData) ?? `Erreur HTTP ${response.status}`);
            }
            
            setData(respData)
        } catch (err) {
            const msg = parseErrorMessage(err)
            setError(true)
            setData(msg)
        } finally {
            setLoading(false)
        }
    }

    const ready_to_delete = ()=>{
        return Boolean(url)
    }

    const retry = ()=>{
        if (ready_to_delete()) {
            setLoading(true)
            setError(false)
            send()
        }
    }

    return { data, isLoading, error, hasData, retry }
}
