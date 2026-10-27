'use client'

import { useState, useEffect, useMemo } from 'react'
import { parseErrorMessage, parseAPIError } from "@/utils/error";
 
export default function Put(url, put, handleAPIError = parseAPIError) {
    const [data, setData] = useState({})
    const [isLoading, setLoading] = useState(false)
    const [error, setError] = useState(false)

    const hasData = useMemo(
        () => (isLoading == false && error == false && data && Object.keys(data).length > 0)
    ,[isLoading, error, data])

    async function putData() {
        try {
            const response = await fetch(`${url}`, 
                {
                    method: "PUT",
                    headers: {
                        "Content-Type" : "application/json"
                    },
                    body: JSON.stringify(put),
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

    const ready_to_put = ()=>{
        return Boolean(url && put)
    }

    const retry = ()=>{
        if (ready_to_put()) {
            setLoading(true)
            setError(false)
            putData()
        }
    }

    useEffect(() => {
        if (ready_to_put()) {
            setLoading(true)
            setError(false)
            putData()
        }
    }, [url, put])

    return { data, isLoading, error, hasData, retry }
}
