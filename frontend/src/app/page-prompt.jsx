"use client"

import { useAppContext } from "@/contexts/AppContext";
import { usePageContext } from "./page-context.jsx";

import { useRouter } from "next/navigation";
import {useState, useEffect} from "react";
import {usePost} from "@/hooks/Http";
import styles from "./page.module.css";
import {Button} from "@/components/Buttons";
import {Navigation} from "@/components/Icons";


export default function Component() {
  const router = useRouter();

  const { selectedItem, messages, setMessages } = usePageContext();
  const { setError } = useAppContext();

  const [ prompt, setPrompt ] = useState("")

    const [postRequest, setPostRequest] = useState({
        url: null,
        data: null,
    });

    const post = usePost(postRequest.url, postRequest.data);

  useEffect(()=>{
    if(post.hasError == true)
    {
        console.log("error", post.result.message)
      setError(post.result.message);
    }
  }, [post.hasError])

  useEffect(()=>{
    if(post.hasSuccess == true)
    {
        if(!selectedItem)
        {
            const params = new URLSearchParams({
                chat_id: post.result?.data?.id
            });

            // charge la nouvelle discussion
            router.push(`/?${params.toString()}`);
        }
        else{
            // actualise la liste des messages après l'envoi réussi
            router.refresh();
            setPrompt("");
        }
    }
  }, [post.hasSuccess])

  const handleSubmit = (e) => {
    e.preventDefault(); // Empêche la soumission du formulaire
    
    // création d'une nouvelle discussion ?
    if(!selectedItem)
    {
        setPostRequest({
            url: `/chats`,
            data: { title: "Nouvelle discussion", message: prompt }
        });
    }
    else
    {
        // place le message dans la pile en attendant le retour du serveur...

        const newMessages = [...messages];

        newMessages.push({
            date: new Date().toISOString(),
            message: prompt
        });

        setMessages(newMessages);

        setPostRequest({
            url: `/chats/${selectedItem?.id}/messages`,
            data: { message: prompt }
        });
    }

  };

  return (
    <form className={styles.footer} onSubmit={handleSubmit}>
        <textarea name="message" value={prompt} onChange={(e) => setPrompt(e.target.value)} placeholder="Tapez votre message ici..."></textarea>
        <Button type="submit" style="primary" disabled={!prompt} icon={Navigation}></Button>
    </form>
  );
}
