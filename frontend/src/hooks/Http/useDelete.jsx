'use client'

import { useState, useMemo } from 'react'
import { parseResponseAPI, Result } from "@/utils/result";

 
export default function Delete(url, domain = process.env.NEXT_PUBLIC_API_URL, handleResponse = parseResponseAPI) {
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

    async function send() {
        try {
            const response = await fetch(`${domain}${url}`, 
                {
                    method: "DELETE",
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

    const ready_to_delete = ()=>{
        return Boolean(url)
    }

    const retry = ()=>{
        if (ready_to_delete()) {
            setLoading(true)
            setResult(null)
            send()
        }
    }

    return { data: result?.data, isLoading, error: result?.error, hasData, hasError, hasSuccess, result, retry }
}
