"use client";

import { createContext, useContext, useState, useEffect, useRef } from "react";
import { useSearchParams } from "next/navigation";
import { fetchApi, postApi } from "@/utils/http";
import { useRouter } from "next/navigation";
import { useAppContext } from "@/contexts/AppContext";
import { CreateRevuesDialog } from "@/components/Dialogs";

const PageContext = createContext(null);

/**
 * Fournit les états partagés propres à la page.
 * @param {{ children: import("react").ReactNode }} props
 */
export function PageProvider({ children }) {
  const searchParams = useSearchParams();
  const [ selectedItem, setSelectedItem ] = useState(null)
  const [ items, setItems ] = useState([])
  const [ messages, setMessages ] = useState([])
  const [ revues, setRevues ] = useState([])
  const [ contentView, setContentView ] = useState("chat")
  const { setError, setUser, user } = useAppContext();

  const { openDialog } = useAppContext();
  const router = useRouter();
  
    const chatId = Number(searchParams.get("chat_id"));

    const refreshRevue = () => {
        async function fetchRevues() {
            try {
                const result = await fetchApi(`/revues`);

                if(result.success == false)
                    throw new Error(result.message);

                setSelectedItem(null);
                setRevues(result.data);
                setContentView("revues");
            } catch (error) {
                setError(error.message);
            }
        }

        fetchRevues();
    };

    const createRevue = () => {
        openDialog(
            // dialog
            CreateRevuesDialog, 
            // dialog props
            {chat_id: chatId}, 
            // success
            () => refreshRevue())
    };

    const refreshChats = (chatId) => {
        async function fetchChats() {
            try {
                const result = await fetchApi(`/chats`);

                if(result.success == false)
                    throw new Error(result.message);

                setItems(result.data);
                setSelectedItem(result.data.find(item => item.id === chatId));
                setContentView("chat");
            } catch (error) {
                setError(error.message);
            }
        }

        fetchChats();
    };

    const createChat = async () => {
        try {
            const result = await postApi(`/chats`, {title: "Nouvelle discussion"});

            if(result.success == false)
                throw new Error(result.message);

            refreshChats(result.data.id);
        } catch (error) {
            setError(error.message);
        }
    };

    const login = () => {
        router.replace("/login", { scroll: false });
    };

    const logout = async () => {
        try {
            const result = await postApi(`/logout`);

            if(result.success == false)
                throw new Error(result.message);

            setUser(null);

            window.location.reload();
        } catch (error) {
            setError(error.message);
        }
    };

    // liste les chats de l'utilisateur authentifié
    useEffect(() => {

        // l'utilisateur doit etre loggé
        if (!user){
            return;
        }

        /**
         * Charge le chat depuis l'API.
         */
        async function fetchChats() {
            try {
                const result = await fetchApi(`/chats`);

                if(result.success == false)
                    throw new Error(result.message);

                setItems(result.data);
            } catch (error) {
                setError(error.message);
            }
        }

        fetchChats();
    }, [user]);

    // charge les revues
    useEffect(() => {
        // l'utilisateur doit etre loggé
        if (!user){
            setRevues([]);
            return;
        }

        async function fetchRevues() {
            try {
                const result = await fetchApi(`/revues`);

                if(result.success == false)
                    throw new Error(result.message);

                setRevues(result.data);
            } catch (error) {
                setError(error.message);
            }
        }

        fetchRevues();
    }, [user]);

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

    // si la sélection change 
    // on définit le paramètre chat_id dans l'URL (sans rechargement) 
    // on charge les messages du chat correspondant
    useEffect(() => {
        const params = new URLSearchParams(searchParams);

        if (!selectedItem) {
            params.delete("chat_id");
            router.replace(`/?${params.toString()}`, { scroll: false });
            setMessages([]);
            setRevues([]);
            return;
        }

        params.set("chat_id", selectedItem?.id);

        router.replace(`/?${params.toString()}`, { scroll: false });

        /**
         * Charge le chat depuis l'API.
         */
        async function fetchChat() {
            try {
                const result = await fetchApi(`/chats/${selectedItem.id}`);
                
                if(result.success == false)
                    throw new Error(result.message);

                setMessages(JSON.parse(result.data.messages));
                setContentView("chat");
            } catch (error) {
                setError(error.message);
            }
        }

        fetchChat();
    }, [selectedItem]);

    return (
        <PageContext.Provider
            value={{ selectedItem, setSelectedItem, items, setItems, messages, setMessages, revues, setRevues, contentView, setContentView, logoutAction: logout, loginAction: login, createRevue, refreshRevue, createChat, refreshChats }}
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