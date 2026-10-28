'use client'

import { useState, useEffect, useMemo } from 'react'
import { parseResponseAPI, Result } from "@/utils/result";
 

export default function useFetch(url, domain = process.env.NEXT_PUBLIC_API_URL, handleResponse = parseResponseAPI) {
    const [result, setResult] = useState(null)
    const [isLoading, setLoading] = useState(false)

    const hasData = useMemo(
        () => (isLoading == false && result?.data)
    ,[isLoading, result])

    const hasError = useMemo(
        () => (isLoading == false && result?.success == false)
    ,[isLoading, result])

    const hasSuccess = useMemo(
        () => (isLoading == false && result?.success == true)
    ,[isLoading, result])

    async function fetchData() {
        try {
            const response = await fetch(`${domain}${url}`, 
                {
                    method: "GET",
                    credentials: "include"
                }
            );
            
            setResult(await handleResponse(response))
        } catch (err) {
            setResult(new Result(false, null, err?.message))
        } finally {
            setLoading(false)
        }
    }
    
    const ready_to_fetch = ()=>{
        return Boolean(url)
    }

    const retry = ()=>{
        if (ready_to_fetch()) {
            setLoading(true)
            setResult(null)
            fetchData()
        }
    }

    useEffect(() => {
        if (ready_to_fetch()) {
            setLoading(true)
            setResult(null)
            fetchData()
        }
    }, [url])

    return { data: result?.data, isLoading, error: result?.message, hasData, hasError, hasSuccess, retry, result }
}
