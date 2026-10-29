"use client"

import { useAppContext } from "@/contexts/AppContext";
import { usePageContext } from "./page-context.jsx";

import {useState, useEffect} from "react";
import {useFetch} from "@/hooks/Http";
import styles from "./page.module.css";
import Chat from "@/components/Chat/Chat";

export default function Component() {
  const { selectedItem } = usePageContext();
  const { setError } = useAppContext();

  const [ items, setItems ] = useState([])

  const [ fetchUrl, setFetchUrl ] = useState(null)
  const fetch = useFetch(fetchUrl)

  useEffect(() => {
    if (selectedItem) {
      setFetchUrl(`/chats/${selectedItem.id}`)
    }
  }, [selectedItem])

  useEffect(()=>{
    if(fetch.hasError == true)
    {
      setError(fetch.result.message);
    }
  }, [fetch.hasError])

  useEffect(()=>{
    if(fetch.hasSuccess == true)
    {
      const chatMessages = JSON.parse(fetch?.result?.data?.messages);

      setError(null);
      setItems(chatMessages);
    }
  }, [fetch.hasSuccess])

  return (
    <Chat 
        data={{
            items
        }}
    />
  );
}
