'use client'

import { useState, useEffect, useMemo } from 'react'
import { parseResponseAPI, Result } from "@/utils/result";
 
export default function usePost(url, post, domain = process.env.NEXT_PUBLIC_API_URL, handleResponse = parseResponseAPI) {
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

    async function postData() {
        try {
            const response = await fetch(`${domain}${url}`, 
                {
                    method: "POST",
                    headers: {
                        "Content-Type" : "application/json"
                    },
                    body: JSON.stringify(post),
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

    const ready_to_post = ()=>{
        return Boolean(url && post)
    }

    const retry = ()=>{
        if (ready_to_post()) {
            setLoading(true)
            setResult(null)
            postData()
        }
    }

    useEffect(() => {
        if (ready_to_post()) {
            setLoading(true)
            setResult(null)
            postData()
        }
    }, [url, post])

    return { data: result?.data, isLoading, error: result?.message, hasData, hasError, hasSuccess, result, retry }
}
