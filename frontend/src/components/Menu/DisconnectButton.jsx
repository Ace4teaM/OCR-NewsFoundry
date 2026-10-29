"use client";

import { Logout } from "@/components/Icons";
import styles from "./Menu.module.css";

export default function DisconnectButton({data}) {
    
  // paramètres
  const { 
    isLogged = false, 
    loginAction = () => console.log("Connexion"),
    logoutAction = () => console.log("Déconnexion")
  } = data;

  return (
    <button onClick={(e)=>isLogged ? logoutAction() : loginAction()}><Logout /> {isLogged ? "Se déconnecter" : "Se connecter"}</button>
  );
}