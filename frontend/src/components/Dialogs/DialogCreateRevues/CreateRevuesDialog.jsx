"use client"

import { memo, useState, useEffect } from "react";
import { useAppContext } from "@/contexts/AppContext";

import styles from "./CreateRevuesDialog.module.css";

import { Button } from "@/components/Buttons";
import { usePost } from "@/hooks/Http";

const CreateRevuesDialog = ({
    chat_id,
    setDialogResult,
    ...props
}) => {

    const { setError } = useAppContext();

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
            setDialogResult(true);
        }
    }, [post.hasSuccess])

    const handleSubmit = (e) => {
        e.preventDefault();

        const formData = new FormData(e.target.form);

        const formDataObject = Object.fromEntries(
            formData.entries()
        );

        setPostRequest({
            url: `/chats/${chat_id}/revues`,
            data: formDataObject
        });
    };


    return (
        <div className={styles.content}>

            <div className={styles.header}>
                <div className={styles.title}>
                    Générer une revue de presse
                </div>

                <p>Donner un titre à votre revue de presse</p>
            </div>

            <form className={styles.form}>

                <label htmlFor="theme">
                    Thème de la revue de presse
                </label>

                <input
                    required
                    type="text"
                    name="theme"
                    id="theme"
                />

                <div className={styles.footer}>
                    <Button
                        style="secondary"
                        onClick={(e) => handleSubmit(e)}
                        disabled={post.isLoading}
                    >
                        Générer
                    </Button>
                </div>

            </form>

        </div>
    );
};


export default memo(CreateRevuesDialog);