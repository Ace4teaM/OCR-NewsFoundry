"use client";

import { createContext, useContext, useState, useEffect } from "react";
import { fetchApi } from "@/utils/http";
import { useRouter } from "next/navigation";

const PageContext = createContext(null);

/**
 * Fournit les états partagés propres à la page.
 * @param {{ children: import("react").ReactNode }} props
 */
export function PageProvider({ searchParams, children }) {
  const [ selectedItem, setSelectedItem ] = useState(null)

  const router = useRouter();
  
    const chatId = searchParams?.chat_id;

    // si le paramètre chat_id est présent, on charge le chat correspondant
    useEffect(() => {
        if (!chatId) {
            setSelectedItem(null);
            return;
        }

        /**
         * Charge le chat depuis l'API.
         */
        async function fetchChat() {
            try {
                const result = await fetchApi(`chats/${chatId}`);
                
                const { id, title, created_at } = result.data;

                setSelectedItem({ id, title, created_at });
            } catch (error) {
            }
        }

        fetchChat();
    }, [chatId]);

    // si la sélection change on définit le paramètre chat_id dans l'URL (sans rechargement)
    useEffect(() => {
        if (!selectedItem) {
            return;
        }

        const params = new URLSearchParams(searchParams);
        params.set("chat_id", selectedItem?.id);

        router.replace(`/?${params.toString()}`, { scroll: false });

    }, [selectedItem]);

    return (
        <PageContext.Provider
            value={{ selectedItem, setSelectedItem }}
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