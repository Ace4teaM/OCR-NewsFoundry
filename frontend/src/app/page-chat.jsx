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
      console.log("selectedItem", selectedItem)
    }
  }, [selectedItem])

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
      const messages = JSON.parse(fetch?.result?.data?.messages);
      // construit une suite de messages individuels à partir des données récupérées
      let chatMessages = []
      for (const msg of messages) {
        if(msg.message)
          chatMessages.push({
            date: msg.date,
            message: msg.message
          });
        if(msg.response)
          chatMessages.push({
            date: msg.date,
            response: msg.response
          });
      }

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
