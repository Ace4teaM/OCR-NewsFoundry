'use client'

import { useState, useEffect, useMemo } from 'react'
import { parseErrorMessage, parseAPIError } from "@/utils/error";
 
export default function usePost(url, post, handleAPIError = parseAPIError) {
    const [data, setData] = useState({})
    const [isLoading, setLoading] = useState(false)
    const [error, setError] = useState(false)

    const hasData = useMemo(
        () => (isLoading == false && error == false && data && Object.keys(data).length > 0)
    ,[isLoading, error, data])

    async function postData() {
        try {
            const response = await fetch(`${url}`, 
                {
                    method: "POST",
                    headers: {
                        "Content-Type" : "application/json"
                    },
                    body: JSON.stringify(post),
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

    const ready_to_post = ()=>{
        return Boolean(url && post)
    }

    const retry = ()=>{
        if (ready_to_post()) {
            setLoading(true)
            setError(false)
            postData()
        }
    }

    useEffect(() => {
        if (ready_to_post()) {
            setLoading(true)
            setError(false)
            postData()
        }
    }, [url, post])

    return { data, isLoading, error, hasData, retry }
}
