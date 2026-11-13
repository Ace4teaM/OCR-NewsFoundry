"use client"

import { useAppContext } from "@/contexts/AppContext";
import { usePageContext } from "./page-context.jsx";

import { useRouter } from "next/navigation";
import {useState, useEffect, useRef} from "react";
import {usePost} from "@/hooks/Http";
import styles from "./page.module.css";
import {Button} from "@/components/Buttons";
import {Navigation} from "@/components/Icons";
import { parseStreamResponseAPI } from "@/utils/result.js";


export default function Component() {
    const router = useRouter();

    const formRef = useRef(null);

    const { selectedItem, setSelectedItem, setItems, setRevues, setContentView, messages, setMessages } = usePageContext();
    const { setError,setNotification } = useAppContext();

    const [ prompt, setPrompt ] = useState("")

    const [postRequest, setPostRequest] = useState({
        url: null,
        data: null,
        handleResponse: undefined, // défaut
    });

    const post = usePost(postRequest.url, postRequest.data, undefined, postRequest.handleResponse);

    useEffect(()=>{
        if(post.hasError == true)
        {
            if(post.result?.data?.erreur)
            {
                // ajoute la réponse à la liste des messages existants
                if(selectedItem)
                {
                    const newMessage = {
                        date: new Date().toISOString(),
                        message: post.result?.data?.erreur,
                        type: "error"
                    };

                    setMessages(prev => [...prev.filter(item => item.type !== "loading"), newMessage]);
                }
                else
                    setError(post.result?.data?.erreur);
            }
            else
                setError(post.result.message);
        }
    }, [post.hasError])

    useEffect(()=>{
        if(post.hasSuccess == true)
        {
            const data = post.result?.data;

            // charge une nouvelle discussion
            if(!selectedItem && data?.chat)
            {
                const newChat = data?.chat;
                setItems(prev => [...prev, newChat]);
                setSelectedItem(newChat);
            }
            
            // charge une revue de presse
            if(data?.revue)
            {
                const newRevue = data?.revue;
                setRevues(prev => [...prev, newRevue]);
                setSelectedItem(null);
                setContentView("revues");
            }

            // ajoute la réponse à la discussion existantes
            if(selectedItem && data?.response)
            {       
                const newMessage = {
                    date: new Date().toISOString(),
                    message: post.result?.data?.response,
                    type: "assistant"
                };

                setMessages(prev => [...prev.filter(item => item.type !== "loading"), newMessage]);
            }
                
            setPrompt("");
        }
    }, [post.hasSuccess])

    // Traite les résultats intermédiaires du flux
    function onMessage(result) {
        if(result.success) {
            // si il s'agit d'une notification mais pas des données finales...
            if(result?.message && !result?.data)
            {
                if(selectedItem)
                {       
                    const newMessage = {
                        date: new Date().toISOString(),
                        message: result?.message,
                        type: "loading"
                    };

                    setMessages(prev => [...prev.filter(item => item.type !== "loading"), newMessage]);
                }
                else
                    setNotification(result?.message);
            }
        } else {
            console.error("onMessage Error:", result);
        }
    }

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
            url: `/prompt_stream`,
            data: { message: prompt },
            handleResponse: async (response) => {
                return await parseStreamResponseAPI(response, onMessage);
            }
        });
    }
    // discussion existante
    else
    {
        // place le message dans la pile en attendant la réponse du serveur...

        const newMessage = {
            date: new Date().toISOString(),
            message: prompt,
            type: "user"
        };

        setMessages(prev => [...prev, newMessage]);

        setPostRequest({
            url: `/chats/${selectedItem?.id}/messages_stream`,
            data: { message: prompt },
            handleResponse: async (response) => {
                return await parseStreamResponseAPI(response, onMessage);
            }
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
