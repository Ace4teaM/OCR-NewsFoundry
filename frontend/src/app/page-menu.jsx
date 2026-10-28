"use client"

import { useAppContext } from "@/contexts/AppContext";
import { usePageContext } from "./page-context.jsx";

import {useState, useEffect} from "react";
import {useFetch} from "@/hooks/Http";
import styles from "./page.module.css";
import Menu from "@/components/Menu/Menu";


export default function Component() {
  const { selectedItem, setSelectedItem } = usePageContext();
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
    if (!fetchUrl) {
      setFetchUrl("/chats")
    }
  }, [fetchUrl])

  useEffect(()=>{
    if(fetch.hasError == true)
    {
      setError(fetch.result.message);
    }
  }, [fetch.hasError])

  useEffect(()=>{
    if(fetch.hasSuccess == true)
    {
      setError(null);
      setItems(fetch?.result?.data);
    }
  }, [fetch.hasSuccess])

  return (
    <Menu 
        data={{
            items
        }}
        setSelectedItem={setSelectedItem}
        selectedItem={selectedItem}
    />
  );
}
