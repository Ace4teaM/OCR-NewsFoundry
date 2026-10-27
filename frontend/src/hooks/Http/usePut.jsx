'use client'

import { useState, useEffect, useMemo } from 'react'
import { parseResponseAPI, Result } from "@/utils/result";
 
export default function Put(url, put, domain = process.env.NEXT_PUBLIC_API_URL, handleResponse = parseResponseAPI) {
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

    async function putData() {
        try {
            const response = await fetch(`${domain}${url}`, 
                {
                    method: "PUT",
                    headers: {
                        "Content-Type" : "application/json"
                    },
                    body: JSON.stringify(put),
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

    const ready_to_put = ()=>{
        return Boolean(url && put)
    }

    const retry = ()=>{
        if (ready_to_put()) {
            setLoading(true)
            setResult(null)
            putData()
        }
    }

    useEffect(() => {
        if (ready_to_put()) {
            setLoading(true)
            setResult(null)
            putData()
        }
    }, [url, put])

    return { data: result?.data, isLoading, error: result?.error, hasData, hasError, hasSuccess, retry, result }
}
