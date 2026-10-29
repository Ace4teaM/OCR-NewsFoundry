"use client"

import styles from "./page.module.css";

import { useAppContext } from "@/contexts/AppContext";

import {Button} from "@/components/Buttons";
import {LogoLarge} from "@/components/Icons";
import {usePost} from "@/hooks/Http";
import { useRouter } from "next/navigation";
import { useId, useState, useEffect } from "react";

export default function Page() {
  const router = useRouter();

  const { setError, setUser } = useAppContext();

  const password_id = useId();
  const email_id = useId();

  const [ data, setData ] = useState(null)
  const login = usePost(`/login`, data)

  useEffect(()=>{
    if(login.hasError == true)
    {
      console.info("hasError")
      setError(login.result.message);
    }
  }, [login.hasError])

  useEffect(()=>{
    if(login.hasSuccess == true)
    {
      console.info("hasSuccess")
      setUser(login.result.data);
      router.push("/");
    }
  }, [login.hasSuccess])

  const handleSubmit = (e) => {
    e.preventDefault(); // Empêche la soumission du formulaire
    
    const formData = new FormData(e.target)
    const data = Object.fromEntries(formData.entries())

    setData(data);
  };

  return (
    <div className={styles.page}>
      <main className={styles.main}>
        <div className={styles.box}>
            <LogoLarge className={styles.icon}/>
            <p>Connectez-vous pour accéder à votre assistant d'actualités IA</p>
            <form onSubmit={(e)=>handleSubmit(e)}>
                <label htmlFor={email_id}>Adresse email</label>
                <input id={email_id} type="mail" name="email" placeholder="votre.email@exemple.com" />
                <label htmlFor={password_id}>Mot de passe</label>
                <input id={password_id} name="password" type="password"></input>
                <Button type="submit" style="secondary">Se connecter</Button>
            </form>
        </div>
      </main>
    </div>
  );
}
