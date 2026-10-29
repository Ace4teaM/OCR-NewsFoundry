"use client"

import { useAppContext } from "@/contexts/AppContext";
import { usePageContext } from "./page-context.jsx";

import { useRouter } from "next/navigation";
import {useState, useEffect, useRef} from "react";
import {usePost} from "@/hooks/Http";
import styles from "./page.module.css";
import {Button} from "@/components/Buttons";
import {Navigation} from "@/components/Icons";


export default function Component() {
  const router = useRouter();

  const formRef = useRef(null);

  const { selectedItem, setSelectedItem, setItems, messages, setMessages } = usePageContext();
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
      setError(post.result.message);
    }
  }, [post.hasError])

  useEffect(()=>{
    if(post.hasSuccess == true)
    {
        if(!selectedItem)
        {
            // charge la nouvelle discussion
            const newItem = post.result?.data;
            setItems(prev => [...prev, newItem]);
            setSelectedItem(newItem);
        }
        else{
            // ajoute la réponse à la liste des messages existants
            
            const newMessages = [...messages];

            newMessages.push({
                date: new Date().toISOString(),
                message: post.result?.data?.response,
                type: "system"
            });

            setMessages(newMessages);
        }
         
        setPrompt("");
    }
  }, [post.hasSuccess])

    function handleKeyDown(event) {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            formRef.current?.requestSubmit();
        }
    }

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
            message: prompt,
            type: "user"
        });

        setMessages(newMessages);

        setPostRequest({
            url: `/chats/${selectedItem?.id}/messages`,
            data: { message: prompt }
        });
    }

  };

  return (
    <form ref={formRef} className={styles.footer} onSubmit={handleSubmit}>
        <textarea name="message" 
            value={prompt} 
            onChange={(e) => setPrompt(e.target.value)} 
            onKeyDown={handleKeyDown}
            placeholder="Tapez votre message ici..."></textarea>
        <Button type="submit" style="primary" disabled={!prompt} icon={Navigation}></Button>
    </form>
  );
}
