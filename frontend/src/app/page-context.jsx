"use client";

import { createContext, useContext, useState, useEffect, useRef } from "react";
import { fetchApi } from "@/utils/http";
import { useRouter } from "next/navigation";
import { useAppContext } from "@/contexts/AppContext";

const PageContext = createContext(null);

/**
 * Fournit les états partagés propres à la page.
 * @param {{ children: import("react").ReactNode }} props
 */
export function PageProvider({ searchParams, children }) {
  const [ selectedItem, setSelectedItem ] = useState(null)
  const [ items, setItems ] = useState([])
  const [ messages, setMessages ] = useState([])
  const { setError } = useAppContext();

  const router = useRouter();
  
    const chatId = Number(searchParams?.chat_id);
    const hasRun = useRef(false);

    // si le paramètre chat_id est présent, on charge le chat correspondant
    useEffect(() => {

        // Code exécuté une seule fois
        if (hasRun.current) return;
        hasRun.current = true;


        /**
         * Charge le chat depuis l'API.
         */
        async function fetchChats() {
            try {
                const result = await fetchApi(`chats`);

                if(result.success == false)
                    throw new Error(result.message);

                setItems(result.data);
            } catch (error) {
                setError(error.message);
            }
        }

        fetchChats();
    }, []);

    // si le paramètre chat_id est présent, on sélectionne le chat correspondant
    useEffect(() => {
        
        if (!chatId) {
            return;
        }

        const found = items.find(item => item.id === chatId)

        if (!found) {
            return;
        }

        setSelectedItem(found);
    }, [chatId, items]);

    // si la sélection change on définit le paramètre chat_id dans l'URL (sans rechargement)
    useEffect(() => {
        if (!selectedItem) {
            setMessages([]);
            return;
        }

        const params = new URLSearchParams(searchParams);
        params.set("chat_id", selectedItem?.id);

        router.replace(`/?${params.toString()}`, { scroll: false });

        /**
         * Charge le chat depuis l'API.
         */
        async function fetchChat() {
            try {
                const result = await fetchApi(`chats/${selectedItem.id}`);
                
                if(result.success == false)
                    throw new Error(result.message);
                
                setMessages(JSON.parse(result.data.messages));
            } catch (error) {
                setError(error.message);
            }
        }

        fetchChat();
    }, [selectedItem]);

    return (
        <PageContext.Provider
            value={{ selectedItem, setSelectedItem, items, setItems, messages, setMessages }}
        >
            {children}
        </PageContext.Provider>
    );
}

/**
 * Accède aux états propres à la page.
 */
export function usePageContext() {
    const context = useContext(PageContext);

    if (context === null) {
        throw new Error("usePageContext doit être utilisé dans PageProvider");
    }

    return context;
}